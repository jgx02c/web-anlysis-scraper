import os
import json
from pymongo import MongoClient
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Get MongoDB URI and database name from .env
MONGO_URI = os.getenv("MONGO_URI")
DB_NAME = os.getenv("DB_NAME")

# Initialize MongoDB connection
client = MongoClient(MONGO_URI)
db = client[DB_NAME]
collection = db["business"]  # Use the 'business' collection

# Ask for folder name (assumes it's in the same directory)
folder_name = input("Enter the folder name (inside this directory): ").strip()
folder_path = os.path.join(os.getcwd(), folder_name)

def upload_json_files(folder_path):
    if not os.path.isdir(folder_path):
        print(f"Error: Folder '{folder_name}' does not exist.")
        return
    
    for filename in os.listdir(folder_path):
        if filename.endswith(".json"):  # Process only .json files
            file_path = os.path.join(folder_path, filename)
            with open(file_path, "r", encoding="utf-8") as f:
                try:
                    json_data = json.load(f)
                except json.JSONDecodeError:
                    print(f"Error: Invalid JSON format in {filename}")
                    continue
            
            # Insert JSON data directly into MongoDB
            result = collection.insert_one(json_data)
            print(f"Uploaded: {filename} with ID {result.inserted_id}")

# Run the upload process
upload_json_files(folder_path)

print("All JSON files uploaded successfully!")
