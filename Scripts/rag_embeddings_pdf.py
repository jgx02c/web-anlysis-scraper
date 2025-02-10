import os
from dotenv import load_dotenv
from tkinter import filedialog, Tk
from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain_pinecone import PineconeVectorStore
from pinecone import Pinecone, ServerlessSpec
from langchain_openai import OpenAIEmbeddings
from langchain.schema import Document
from langchain_community.document_loaders import PyPDFLoader
from typing import List, Dict, Tuple
import time
import warnings
import urllib3

# Suppress warnings
warnings.filterwarnings('ignore', category=DeprecationWarning)
warnings.filterwarnings('ignore', category=urllib3.exceptions.NotOpenSSLWarning)
os.environ['TK_SILENCE_DEPRECATION'] = '1'

def get_folder_path():
    """Open a folder selection dialog and return the selected path."""
    root = Tk()
    root.withdraw()
    folder_path = filedialog.askdirectory(title="Select Folder Containing PDF Files")
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

def clean_text(text: str) -> str:
    """Clean and normalize PDF text while preserving structure."""
    import re
    # Remove multiple spaces
    text = re.sub(r'\s+', ' ', text)
    # Remove multiple newlines while preserving paragraph structure
    text = re.sub(r'\n{3,}', '\n\n', text)
    # Clean up any PDF artifacts (common issues in PDF extraction)
    text = re.sub(r'•', '- ', text)  # Replace bullets with dashes
    text = re.sub(r'([^\n])(\n- )', r'\1\n\n- ', text)  # Format lists properly
    text = re.sub(r'(\w)-\n(\w)', r'\1\2', text)  # Fix hyphenated words
    return text.strip()

def process_file(file_path: str, text_splitter: RecursiveCharacterTextSplitter) -> List[Document]:
    """Process a single PDF file using PyPDFLoader."""
    try:
        # Use PyPDFLoader for PDF processing
        loader = PyPDFLoader(file_path)
        pages = loader.load()
        
        split_docs = []
        for page in pages:
            # Clean the extracted text
            cleaned_text = clean_text(page.page_content)
            # Update page metadata
            page_num = page.metadata.get('page', 0) + 1
            
            # Split the cleaned text
            splits = text_splitter.split_text(cleaned_text)

            print(f"\n=== Processing Page {page_num} ({len(splits)} chunks) ===")
            for i, split in enumerate(splits[:3]):  # Print first 3 chunks for inspection
                print(f"\nChunk {i+1}:\n{split[:200]}...\n{'-'*50}")

            # Create documents with page metadata
            for split in splits:
                metadata = {
                    'page': page_num,
                    'source': file_path
                }
                split_docs.append(Document(page_content=split.strip(), metadata=metadata))
        
        return split_docs
    except Exception as e:
        print(f"Error processing {file_path}: {e}")
        raise

def batch_upsert(vectordb: PineconeVectorStore, documents: List[Document], filename: str, batch_size: int = 50):
    """Upsert documents in batches with rate limiting."""
    total_docs = len(documents)
    clean_name = clean_filename(filename)
    
    for i in range(0, total_docs, batch_size):
        batch = documents[i:i + batch_size]
        print(f"Upserting batch {i//batch_size + 1}/{(total_docs + batch_size - 1)//batch_size} "
              f"({len(batch)} documents)")
        
        # Update metadata for each document in batch
        for doc in batch:
            doc.metadata.update({'filename': clean_name})
        
        vectordb.add_documents(documents=batch)
        time.sleep(2)  # Rate limit delay

def create_embeddings(pdf_folder: str, persist_directory: str) -> Tuple[int, List[Dict]]:
    """Process PDF files and create embeddings in Pinecone."""
    os.makedirs(persist_directory, exist_ok=True)
    load_dotenv()
    
    pc = Pinecone(api_key=os.getenv('PINECONE_API_KEY'))
    embeddings = OpenAIEmbeddings(model="text-embedding-ada-002", api_key=os.getenv('OPENAI_API_KEY'))
    
    # Configure text splitter for PDF content
    text_splitter = RecursiveCharacterTextSplitter(
        chunk_size=1000,
        chunk_overlap=200,  # Increased overlap for better context preservation
        length_function=len,
        separators=[
            "\n\n",  # Paragraph breaks
            "\n",    # Line breaks
            ". ",    # Sentences
            "? ",    # Questions
            "! ",    # Exclamations
            ";",     # Semi-colons
            ":",     # Colons
            " ",     # Words
            ""       # Characters
        ],
        keep_separator=True
    )

    processed_files = []
    total_chunks = 0

    # Setup Pinecone index
    index_name = "leaps"
    is_new_index = ensure_index_exists(pc, index_name)
    
    if is_new_index:
        print("Waiting for index to initialize...")
        time.sleep(20)

    index = pc.Index(index_name)
    vectordb = PineconeVectorStore(index=index, embedding=embeddings)

    # Process PDF files
    for dirpath, _, filenames in os.walk(pdf_folder):
        for filename in filenames:
            if filename.endswith('.pdf'):
                file_path = os.path.join(dirpath, filename)
                print(f"\nProcessing {filename}...")
                
                try:
                    # Process single PDF file
                    documents = process_file(file_path, text_splitter)
                    num_chunks = len(documents)
                    
                    # Batch upsert for this file
                    batch_upsert(vectordb, documents, filename)
                    
                    # Record successful processing
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