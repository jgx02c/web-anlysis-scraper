import os
from dotenv import load_dotenv
from tkinter import filedialog, Tk
from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain_pinecone import PineconeVectorStore
from pinecone import Pinecone, ServerlessSpec
from langchain_openai import OpenAIEmbeddings
from langchain.schema import Document
from langchain_community.document_loaders import TextLoader
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
    folder_path = filedialog.askdirectory(title="Select Folder Containing Text Files")
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
        # Remove the domain part and keep only the path
        return '_'.join(parts[1:])
    return filename

def clean_text(text: str) -> str:
    """Clean text by removing extra spaces and normalizing whitespace."""
    # Replace multiple spaces with single space
    text = ' '.join(text.split())
    # Remove unnecessary Unicode characters
    text = ''.join(char for char in text if ord(char) < 128)
    return text.strip()

def process_file(file_path: str, text_splitter: RecursiveCharacterTextSplitter) -> List[Document]:
    """Process a single file using TextLoader."""
    try:
        loader = TextLoader(file_path, encoding='utf-8')
        docs = loader.load()
        
        split_docs = []
        for doc in docs:
            # Clean the text before splitting
            cleaned_text = clean_text(doc.page_content)
            splits = text_splitter.split_text(cleaned_text)
            filename = os.path.basename(file_path)
            clean_name = clean_filename(filename)
            
            for split in splits:
                # No metadata - we'll pass it separately during upsert
                split_docs.append(
                    Document(
                        page_content=clean_text(split),
                        metadata={}
                    )
                )
        
        return split_docs
    except Exception as e:
        print(f"Error loading file {file_path}: {str(e)}")
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

def create_embeddings(txt_folder: str, persist_directory: str) -> Tuple[int, List[Dict]]:
    """Process text files and create embeddings in Pinecone."""
    os.makedirs(persist_directory, exist_ok=True)
    load_dotenv()
    
    pc = Pinecone(api_key=os.getenv('PINECONE_API_KEY'))
    embeddings = OpenAIEmbeddings(model="text-embedding-3-large", api_key=os.getenv('OPENAI_API_KEY'))
    
    # Use RecursiveCharacterTextSplitter with careful splitting
    text_splitter = RecursiveCharacterTextSplitter(
        chunk_size=1000,
        chunk_overlap=50,
        length_function=len,
        separators=["\n\n", "\n", ". ", ", ", " ", ""],
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