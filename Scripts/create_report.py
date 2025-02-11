import os
from pymongo import MongoClient
from dotenv import load_dotenv
import json
from collections import defaultdict
from datetime import datetime

# Load environment variables
load_dotenv()

# Get MongoDB URI and database name from .env
MONGO_URI = os.getenv("MONGO_URI")
DB_NAME = os.getenv("DB_NAME")

# Initialize MongoDB connection
client = MongoClient(MONGO_URI)
db = client[DB_NAME]

# Ask for the business_id to generate the report for
business_id = int(input("Enter the business_id (integer) for the report: ").strip())

def generate_report(business_id):
    # Get the 'webpages_json' collection and the 'reports' collection
    webpages_collection = db['webpages_json']
    reports_collection = db['reports']

    # Fetch all documents for the given business_id from the 'webpages_json' collection
    webpages = webpages_collection.find({"business_id": business_id})

    # Initialize counts for insights and a breakdown of issues
    insights_count = {"Immediate Action Required": 0, "Needs Attention": 0, "Good Practice": 0}
    insights_breakdown = defaultdict(int)
    total_insights = 0

    # Initialize a list to store individual page reports
    page_reports = []

    # Iterate over each webpage document
    for webpage in webpages:
        webpage_url = webpage.get("data", {}).get("website_url")
        insights = webpage.get("data", {}).get("insights", {})
        
        # Initialize counters for the current page report
        page_insights_count = {"Immediate Action Required": 0, "Needs Attention": 0, "Good Practice": 0}
        page_error_citations = []

        # Analyze insights for each section
        for section, section_insights in insights.items():
            page_insights_count[section] += len(section_insights)
            total_insights += len(section_insights)

            # Count individual insight types
            for insight in section_insights:
                insights_breakdown[insight] += 1
                page_error_citations.append({
                    "section": section,
                    "insight": insight,
                    "webpage_url": webpage_url,
                    "filename": webpage["filename"],
                    "business_id": business_id
                })

        # Prepare the page-level report
        page_report = {
            "website_url": webpage_url,
            "insights_count": page_insights_count,
            "error_citations": page_error_citations,
            "filename": webpage["filename"]
        }
        page_reports.append(page_report)

        # Update the overall insights count
        for section, count in page_insights_count.items():
            insights_count[section] += count

    # Generate the overall report
    report = {
        "business_id": business_id,
        "report_date": datetime.utcnow(),  # Store the current UTC time for the report creation
        "insights_count": insights_count,
        "insights_breakdown": dict(insights_breakdown),
        "total_insights": total_insights,
        "page_reports": page_reports
    }

    # Insert the overall report into the 'reports' collection
    result = reports_collection.insert_one(report)

    # Return the report ID for confirmation
    print(f"Overview Report generated and stored with ID {result.inserted_id}")

# Run the report generation
generate_report(business_id)

print("Report generation complete!")
