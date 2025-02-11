import os
from pymongo import MongoClient
from dotenv import load_dotenv
import json

# Load environment variables
load_dotenv()

# Get MongoDB URI and database name from .env
MONGO_URI = os.getenv("MONGO_URI")
DB_NAME = os.getenv("DB_NAME")

# Initialize MongoDB connection
client = MongoClient(MONGO_URI)
db = client[DB_NAME]

# Ask for folder name (assumes it's in the same directory)
folder_name = input("Enter the folder name (inside this directory): ").strip()
folder_path = os.path.join(os.getcwd(), folder_name)

# Ask for collection name
collection_name = input("Enter the collection name: ").strip()
collection = db[collection_name]

# Ask if it's admin_Business and get business_id
is_admin_business = input("Is this for admin_Business? (yes/no): ").strip().lower() == "yes"
business_id = int(input("Enter the business_id (integer): ").strip())

def upload_files(folder_path):
    if not os.path.isdir(folder_path):
        print(f"Error: Folder '{folder_name}' does not exist.")
        return
    
    for filename in os.listdir(folder_path):
        if filename.endswith(".json"):  # Process only .json files containing SEO insights
            file_path = os.path.join(folder_path, filename)
            with open(file_path, "r", encoding="utf-8") as f:
                file_content = json.load(f)  # Read and parse the JSON file

            # Create document structure with SEO insights data
            document = {
                "filename": filename,
                "admin_Business": is_admin_business,
                "business_id": business_id,
                "data": file_content  # Directly insert the parsed JSON as 'data'
            }

            # Insert into MongoDB
            result = collection.insert_one(document)
            print(f"Uploaded: {filename} with ID {result.inserted_id}")

# Run the upload process
upload_files(folder_path)

print("All files uploaded successfully!")
