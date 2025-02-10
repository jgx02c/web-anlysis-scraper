import os
from dotenv import load_dotenv
from tkinter import filedialog, Tk
from langchain.text_splitter import CharacterTextSplitter
from langchain_pinecone import PineconeVectorStore
from pinecone import Pinecone, ServerlessSpec
from langchain_openai import OpenAIEmbeddings
from langchain.schema import Document
from langchain.document_loaders import UnstructuredFileLoader
from typing import List, Dict, Tuple
import time

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

def process_file(file_path: str, text_splitter: CharacterTextSplitter) -> List[Document]:
    """Process a single file using UnstructuredFileLoader."""
    loader = UnstructuredFileLoader(file_path)
    documents = loader.load()
    
    # Split the documents
    split_docs = []
    for doc in documents:
        splits = text_splitter.split_text(doc.page_content)
        filename = os.path.basename(file_path)
        prefix = filename.replace('.txt', '').upper()
        
        for i, split in enumerate(splits):
            split_docs.append(
                Document(
                    page_content=split,
                    metadata={
                        'source': prefix,
                        'filename': filename,
                        'chunk_index': i,
                        'total_chunks': len(splits)
                    }
                )
            )
    
    return split_docs

def batch_upsert(vectordb: PineconeVectorStore, documents: List[Document], batch_size: int = 50):
    """Upsert documents in batches to handle rate limits."""
    total_docs = len(documents)
    for i in range(0, total_docs, batch_size):
        batch = documents[i:i + batch_size]
        print(f"Upserting batch {i//batch_size + 1}/{(total_docs + batch_size - 1)//batch_size} "
              f"({len(batch)} documents)")
        vectordb.add_documents(documents=batch)
        # Add a small delay between batches to respect rate limits
        time.sleep(2)

def create_embeddings(txt_folder: str, persist_directory: str) -> Tuple[int, List[Dict]]:
    """Process text files and create embeddings in Pinecone."""
    os.makedirs(persist_directory, exist_ok=True)
    load_dotenv()
    
    pc = Pinecone(api_key=os.getenv('PINECONE_API_KEY'))
    embeddings = OpenAIEmbeddings(api_key=os.getenv('OPENAI_API_KEY'))
    
    # Initialize text splitter
    text_splitter = CharacterTextSplitter(
        separator="\n\n",
        chunk_size=2000,
        chunk_overlap=50,
        length_function=len,
        is_separator_regex=False,
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
                    batch_upsert(vectordb, documents)
                    
                    # Record successful processing
                    processed_files.append({
                        'filename': filename,
                        'prefix': filename.replace('.txt', '').upper(),
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