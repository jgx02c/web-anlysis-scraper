import os
from dotenv import load_dotenv
from tkinter import filedialog, Tk
from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain_pinecone import PineconeVectorStore
from pinecone import Pinecone
from langchain_openai import OpenAIEmbeddings
from langchain.schema import Document
from langchain_community.document_loaders import TextLoader
from typing import List, Dict, Tuple
import time
import warnings
import urllib3
import re

# Suppress warnings
warnings.filterwarnings('ignore', category=DeprecationWarning)
warnings.filterwarnings('ignore', category=urllib3.exceptions.NotOpenSSLWarning)
os.environ['TK_SILENCE_DEPRECATION'] = '1'

def get_folder_path():
    """Open a folder selection dialog and return the selected path."""
    root = Tk()
    root.withdraw()
    folder_path = filedialog.askdirectory(title="Select Folder Containing Text Files")
    return folder_path

def clean_filename(filename: str) -> str:
    """Clean filename by removing domain and .com part."""
    parts = filename.split('_')
    if len(parts) > 1:
        return '_'.join(parts[1:])
    return filename

def clean_text(text: str) -> str:
    """Normalize text while keeping structure (meta tags, lists, and spacing)."""
    text = re.sub(r'\n{3,}', '\n\n', text)  # Reduce excessive line breaks
    text = re.sub(r'([^\n])(\n- )', r'\1\n\n\2', text)  # Force new lines before bullet points
    text = re.sub(r'[ \t]+', ' ', text)  # Normalize spaces but keep structure
    return text.strip()

def process_file(file_path: str, text_splitter: RecursiveCharacterTextSplitter) -> List[Document]:
    """Process a single file using TextLoader."""
    try:
        loader = TextLoader(file_path, encoding='utf-8')
        docs = loader.load()
        
        split_docs = []
        for doc in docs:
            cleaned_text = clean_text(doc.page_content)
            splits = text_splitter.split_text(cleaned_text)

            print(f"\n=== SPLIT OUTPUT ({len(splits)} chunks) ===")
            for i, split in enumerate(splits[:5]):  # Print first 5 chunks for inspection
                print(f"\nChunk {i+1}:\n{split}\n{'-'*50}")

            for split in splits:
                split_docs.append(Document(page_content=split.strip(), metadata={}))
        
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
        
        # Add minimal metadata during upsert
        for doc in batch:
            doc.metadata = {'filename': clean_name}
        
        vectordb.add_documents(documents=batch)
        time.sleep(2)  # Rate limit delay

def upsert_documents(txt_folder: str) -> Tuple[int, List[Dict]]:
    """Process text files and upsert to existing Pinecone index."""
    load_dotenv()
    
    # Initialize Pinecone client and connect to existing index
    pc = Pinecone(api_key=os.getenv('PINECONE_API_KEY'))
    index = pc.Index("leaps")  # Make sure this matches your index name
    
    embeddings = OpenAIEmbeddings(
        model="text-embedding-ada-002", 
        api_key=os.getenv('OPENAI_API_KEY')
    )
    
    vectordb = PineconeVectorStore(index=index, embedding=embeddings)
    
    # Configure text splitter
    text_splitter = RecursiveCharacterTextSplitter(
        chunk_size=1000,
        chunk_overlap=100,
        length_function=len,
        separators=[
            "\n\n",  # Paragraph breaks
            "\n- ",  # Bullet points (meta tags)
            "\n",   # Single line breaks
            ". ",   # Sentence boundaries
            "? ",
            "! "
        ],
        keep_separator=True
    )

    processed_files = []
    total_chunks = 0

    # Process files one at a time
    for dirpath, _, filenames in os.walk(txt_folder):
        for filename in filenames:
            if filename.endswith('.txt'):
                file_path = os.path.join(dirpath, filename)
                print(f"\nProcessing {filename}...")
                
                try:
                    # Process single file
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
    
    try:
        num_chunks, processed_files = upsert_documents(folder_path)
        
        print(f"\nUpload complete! Upserted {num_chunks} text chunks")
        print("\nProcessed files summary:")
        for file_info in processed_files:
            print(f"- {file_info['filename']}: {file_info['num_chunks']} chunks")
            
    except Exception as e:
        print(f"An error occurred: {str(e)}")

if __name__ == "__main__":
    main()