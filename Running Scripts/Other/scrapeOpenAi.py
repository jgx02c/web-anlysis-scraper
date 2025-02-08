import os
import json
from typing import Dict, Any
from datetime import datetime
from pymongo import MongoClient
import requests

# MongoDB connection setup
mongo_uri = os.getenv('mongo_uri')
client = MongoClient(mongo_uri)
db = client['Cluster07388']
company_collection = db['company']

# Perplexity API setup
PERPLEXITY_API_KEY = "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"
PERPLEXITY_API_URL = "https://api.perplexity.ai/chat/completions"

def get_sonar_response(prompt: str, website_url: str) -> str:
    """Get response from Perplexity Sonar API"""
    try:
        headers = {
            "Authorization": f"Bearer {PERPLEXITY_API_KEY}",
            "Content-Type": "application/json"
        }
        
        data = {
            "model": "sonar-reasoning",
            "messages": [
                {"role": "system", "content": f"You are analyzing the website page. In your response exclude <think>. Follow the instrutions exactly and only give the data on the webpage. Do not give instructions on how to get the data. Give the result, bullet points preffered.: {website_url}"},
                {"role": "user", "content": prompt}
            ]
        }
        
        response = requests.post(PERPLEXITY_API_URL, headers=headers, json=data)
        response.raise_for_status()
        
        result = response.json()
        return result['choices'][0]['message']['content'].strip()
    except Exception as e:
        print(f"Error getting Sonar response for {website_url}: {str(e)}")
        return ""


def load_prompts() -> Dict[str, Dict[str, Dict[str, Dict[str, str]]]]:
    """Load prompts from JSON file"""
    try:
        current_dir = os.path.dirname(os.path.abspath(__file__))
        prompts_path = os.path.join(current_dir, 'prompts.json')
        
        with open(prompts_path, 'r') as file:
            prompts = json.load(file)
            
        if "overview_prompts" not in prompts:
            raise KeyError("Missing 'overview_prompts' in prompts.json")
        if "page_prompts" not in prompts:
            raise KeyError("Missing 'page_prompts' in prompts.json")
            
        return prompts
    except Exception as e:
        print(f"Error loading prompts: {str(e)}")
        raise

def get_website_pages(website_url: str) -> list:
    """Get all pages from a website"""
    prompt = """List all the product or service pages on this website. 
    Return only the URLs, one per line, with no additional text or formatting."""
    
    response = get_sonar_response(prompt, website_url)
    pages = [page.strip() for page in response.split('\n') if page.strip()]
    return pages

def update_database_with_response(website_url: str, section_type: str, section_url: str, 
                                label: str, response: str, prompt_number: str):
    """Update database with individual prompt response"""
    try:
        section_key = "overview" if section_type == "overview" else f"page_{section_url}"
        update_path = f"sections.{section_key}.data.{label}"
        
        company_collection.update_one(
            {"url": website_url},
            {
                "$set": {
                    update_path: {
                        "response": response,
                        "prompt_number": prompt_number,
                        "timestamp": datetime.utcnow()
                    },
                    "last_updated": datetime.utcnow()
                }
            },
            upsert=True
        )
        print(f"Updated {website_url} - {section_type} - {label}")
    except Exception as e:
        print(f"Error updating database: {str(e)}")

def process_prompts_for_target(prompts: Dict[str, Dict[str, Dict[str, str]]], 
                             website_url: str, 
                             target_url: str,
                             prompt_type: str) -> Dict[str, Any]:
    """Process numbered prompts for a given URL and update database in real-time"""
    results = {}
    type_prompts = prompts[prompt_type]
    section_type = "overview" if prompt_type == "overview_prompts" else "page"
    
    # Initialize document in database if it doesn't exist
    company_collection.update_one(
        {"url": website_url},
        {
            "$setOnInsert": {
                "created_at": datetime.utcnow(),
                "is_main": website_url == main_website
            }
        },
        upsert=True
    )
    
    for prompt_num in type_prompts:
        prompt_data = type_prompts[prompt_num]
        print(f"Processing {prompt_type} - {prompt_data['label']} for {target_url}")
        
        response = get_sonar_response(prompt_data["prompt"], target_url)
        
        update_database_with_response(
            website_url=website_url,
            section_type=section_type,
            section_url=target_url if section_type == "page" else "",
            label=prompt_data["label"],
            response=response,
            prompt_number=prompt_num
        )
        
        results[prompt_data["label"]] = {
            "response": response,
            "prompt_number": prompt_num,
            "timestamp": datetime.utcnow()
        }
    
    return results

def process_website(website_url: str, is_main: bool, prompts: Dict) -> None:
    """Process a single website and update database in real-time"""
    print(f"Processing overview for {website_url}")
    process_prompts_for_target(prompts, website_url, website_url, "overview_prompts")
    
    print(f"Getting pages for {website_url}")
    pages = get_website_pages(website_url)
    
    for page in pages:
        print(f"Processing page: {page}")
        process_prompts_for_target(prompts, website_url, page, "page_prompts")

def main():
    # Load configuration
    prompts = load_prompts()
    global main_website
    main_website = "https://leapsandrebounds.com/"
    websites = [
        "https://www.bellicon.com",
        "https://www.jumpsport.com",
        "https://www.boogiebounce.com/",
        "https://www.decathlon.com/products/fit-trampo-500-fitness-trampoline",
        "https://www.amazon.com/Kanchimi-Folding-Fitness-Trampoline-Handlebar/dp/B07Y5Y5Y5Y",
        "https://www.bouncefitness.com.au/",
        "https://www.reboundfitness.com.au/",
        "https://www.argos.co.uk/product/12345678",
        "https://www.networldsports.com/forza-mini-exercise-trampoline.html",
        "https://www.bouncefitness.com.au/"
    ]

    # Process main website
    print(f"Processing main website: {main_website}")
    process_website(main_website, True, prompts)

    # Process competitor websites
    for website in websites:
        print(f"Processing competitor website: {website}")
        process_website(website, False, prompts)

if __name__ == "__main__":
    main()