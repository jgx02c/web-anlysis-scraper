import os
from langchain.text_splitter import CharacterTextSplitter
from langchain_pinecone import PineconeVectorStore
from pinecone import Pinecone, ServerlessSpec
from uuid import uuid4
from langchain_openai import OpenAIEmbeddings
from langchain.schema import Document  # Ensure you import the Document class

# Initialize Pinecone
pc = Pinecone(api_key="6d324250-d2de-411e-9bbe-31986b58d074")

# Initialize embeddings
embeddings = OpenAIEmbeddings()

def create_embeddings(html_folder, persist_directory):
    os.makedirs(persist_directory, exist_ok=True)

    all_documents = []

    # Iterate over all .html files in the given folder
    for filename in os.listdir(html_folder):
        if filename.endswith(".html"):
            file_path = os.path.join(html_folder, filename)

            with open(file_path, 'r', encoding='utf-8') as file:
                text = file.read()

            # Split the text into chunks
            text_splitter = CharacterTextSplitter(
                separator="\n\n",
                chunk_size=1600,
                chunk_overlap=50,
                length_function=len,
                is_separator_regex=False,
            )
            chunks = text_splitter.split_text(text)

            # Create a Document object for each chunk
            for chunk in chunks:
                doc = Document(page_content=chunk, metadata={'source': filename})
                all_documents.append(doc)  # Append the Document object

    # Ensure the index is created only once
    index_name = "leaps"

    existing_indexes = [index_info["name"] for index_info in pc.list_indexes()]

    # Create the Pinecone index
    if index_name not in existing_indexes:
        pc.create_index(
            name=index_name,
            dimension=1536,  # Use the model's dimension
            metric="cosine",  # Replace with your model metric
            spec=ServerlessSpec(
                cloud="aws",
                region="us-east-1"
            ) 
        )

    index = pc.Index(index_name)

    # Initialize the Pinecone vector store
    vectordb = PineconeVectorStore(index=index, embedding=embeddings)

    # Add documents to the vector store
    vectordb.add_documents(documents=all_documents)

    return len(all_documents)

if __name__ == "__main__":
    HTML_FOLDER = "./pages"  # Replace with your actual folder path
    PERSIST_DIRECTORY = "embeddings_db"
    
    try:
        num_chunks = create_embeddings(HTML_FOLDER, PERSIST_DIRECTORY)
        print(f"Created embeddings for {num_chunks} text chunks from HTML files in the folder")
    except Exception as e:
        print(f"An error occurred: {str(e)}")