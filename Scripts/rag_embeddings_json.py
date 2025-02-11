import os
from dotenv import load_dotenv
from tkinter import filedialog, Tk
from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain_pinecone import PineconeVectorStore
from pinecone import Pinecone, ServerlessSpec
from langchain_openai import OpenAIEmbeddings
from langchain.schema import Document
from langchain_community.document_loaders import JSONLoader
from typing import List, Dict, Tuple, Callable
import time
import warnings
import urllib3
from pathlib import Path
import json

# Suppress warnings
warnings.filterwarnings('ignore', category=DeprecationWarning)
warnings.filterwarnings('ignore', category=urllib3.exceptions.NotOpenSSLWarning)
os.environ['TK_SILENCE_DEPRECATION'] = '1'

def get_folder_path():
    """Open a folder selection dialog and return the selected path."""
    root = Tk()
    root.withdraw()
    folder_path = filedialog.askdirectory(title="Select Folder Containing JSON Files")
    return folder_path

def ensure_index_exists(pc: Pinecone, index_name: str) -> bool:
    """Check if index exists, create it if it doesn't."""
    existing_indexes = [index_info["name"] for index_info in pc.list_indexes()]
    
    if index_name not in existing_indexes:
        print(f"Creating new index: {index_name}")
        pc.create_index(
            name=index_name,
            dimension=1536,
            metric="cosine",
            spec=ServerlessSpec(
                cloud="aws",
                region="us-east-1"
            )
        )
        return True
    
    print(f"Index {index_name} already exists, proceeding with upsert")
    return False

def clean_filename(filename: str) -> str:
    """Clean filename by removing domain and .com part."""
    parts = filename.split('_')
    if len(parts) > 1:
        return '_'.join(parts[1:])
    return filename

def extract_metadata(record: dict, metadata: dict) -> dict:
    """Extract and combine metadata from the JSON record."""
    # Base metadata from the record
    extracted = {
        'url': record.get('website_url', ''),
        'title': record.get('title', ''),
    }
    
    # Add SEO metadata if available
    if 'meta' in record and 'SEO' in record['meta']:
        seo = record['meta']['SEO']
        extracted.update({
            'description': seo.get('description', ''),
            'og_title': seo.get('og:title', ''),
            'og_description': seo.get('og:description', '')
        })
    
    # Combine with existing metadata
    return {**metadata, **extracted}

def format_content(record: dict) -> str:
    """Format the content from the JSON record."""
    content_parts = []
    
    # Add headings in a structured way
    if 'headings' in record:
        for level, heads in sorted(record['headings'].items()):
            for heading in heads:
                if heading:
                    content_parts.append(f"{level}: {heading}")
    
    # Add main content
    if 'content' in record:
        content_parts.append(record['content'])
    
    return '\n\n'.join(content_parts)

def process_file(file_path: str, text_splitter: RecursiveCharacterTextSplitter) -> List[Document]:
    """Process a single JSON file using JSONLoader."""
    try:
        # Create JSONLoader with custom jq-like schema and metadata function
        loader = JSONLoader(
            file_path=file_path,
            jq_schema='.',  # Load entire JSON object
            content_key=None,  # We'll format content in the metadata function
            metadata_func=extract_metadata
        )
        
        # Load the documents
        documents = loader.load()
        
        split_docs = []
        for doc in documents:
            # Format the content using our custom function
            formatted_content = format_content(json.loads(doc.page_content))
            
            # Split the formatted content
            splits = text_splitter.split_text(formatted_content)
            
            print(f"\n=== SPLIT OUTPUT ({len(splits)} chunks) ===")
            for i, split in enumerate(splits[:2]):  # Print first 2 chunks as example
                print(f"\nChunk {i+1}:\n{split[:200]}...\n{'-'*50}")
            
            # Create new documents with splits while preserving metadata
            for split in splits:
                split_docs.append(Document(
                    page_content=split.strip(),
                    metadata=doc.metadata
                ))
        
        return split_docs
    except Exception as e:
        print(f"Error processing {file_path}: {e}")
        raise

def batch_upsert(vectordb: PineconeVectorStore, documents: List[Document], filename: str, batch_size: int = 50):
    """Upsert documents in batches to handle rate limits."""
    total_docs = len(documents)
    clean_name = clean_filename(filename)
    
    for i in range(0, total_docs, batch_size):
        batch = documents[i:i + batch_size]
        print(f"Upserting batch {i//batch_size + 1}/{(total_docs + batch_size - 1)//batch_size} "
              f"({len(batch)} documents)")
        
        # Add source file to metadata
        for doc in batch:
            doc.metadata['source_file'] = clean_name
        
        vectordb.add_documents(documents=batch)
        time.sleep(2)  # Rate limit delay

def create_embeddings(json_folder: str, persist_directory: str) -> Tuple[int, List[Dict]]:
    """Process JSON files and create embeddings in Pinecone."""
    os.makedirs(persist_directory, exist_ok=True)
    load_dotenv()
    
    pc = Pinecone(api_key=os.getenv('PINECONE_API_KEY'))
    embeddings = OpenAIEmbeddings(model="text-embedding-ada-002", api_key=os.getenv('OPENAI_API_KEY'))
    
    text_splitter = RecursiveCharacterTextSplitter(
        chunk_size=1000,
        chunk_overlap=100,
        length_function=len,
        separators=[
            "\n\n",      # Paragraph breaks
            "\n",        # Line breaks
            ". ",        # Sentences
            "! ",        # Exclamations
            "? ",        # Questions
            ", ",        # Phrases
        ],
        keep_separator=True
    )

    processed_files = []
    total_chunks = 0

    # Setup Pinecone index
    index_name = "leapsjson"
    is_new_index = ensure_index_exists(pc, index_name)
    
    if is_new_index:
        print("Waiting for index to initialize...")
        time.sleep(20)

    index = pc.Index(index_name)
    vectordb = PineconeVectorStore(index=index, embedding=embeddings)

    # Process JSON files
    for dirpath, _, filenames in os.walk(json_folder):
        for filename in filenames:
            if filename.endswith('.json'):
                file_path = os.path.join(dirpath, filename)
                print(f"\nProcessing {filename}...")
                
                try:
                    documents = process_file(file_path, text_splitter)
                    num_chunks = len(documents)
                    
                    batch_upsert(vectordb, documents, filename)
                    
                    processed_files.append({
                        'filename': clean_filename(filename),
                        'num_chunks': num_chunks,
                        'file_path': file_path
                    })
                    
                    total_chunks += num_chunks
                    print(f"Successfully processed {filename}: {num_chunks} chunks")
                    
                except Exception as e:
                    print(f"Error processing {filename}: {e}")
                    continue

    return total_chunks, processed_files

def main():
    folder_path = get_folder_path()
    if not folder_path:
        print("No folder selected. Exiting...")
        return

    persist_directory = "embeddings_db"
    
    try:
        num_chunks, processed_files = create_embeddings(folder_path, persist_directory)
        
        print(f"\nUpload complete! Created embeddings for {num_chunks} text chunks")
        print("\nProcessed files summary:")
        for file_info in processed_files:
            print(f"- {file_info['filename']}: {file_info['num_chunks']} chunks")
            
        # Save processing log
        log_file_path = os.path.join(persist_directory, 'processed_files.txt')
        with open(log_file_path, 'w', encoding='utf-8') as log_file:
            for file_info in processed_files:
                log_file.write(f"{file_info['filename']}\t{file_info['num_chunks']} chunks\n")
        
        print(f"\nProcessed files log saved to: {log_file_path}")
        
    except Exception as e:
        print(f"An error occurred: {str(e)}")

if __name__ == "__main__":
    main()