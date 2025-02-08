import os
import json
import time
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from webdriver_manager.chrome import ChromeDriverManager  # Import webdriver-manager

# Configuration
FOLDER_NAME = "downloaded_pages"  # Change to your desired folder name
URLS_JSON_FILE = "urls.json"  # JSON file containing the list of URLs

# Ensure the folder exists
os.makedirs(FOLDER_NAME, exist_ok=True)

# Load URLs from JSON file
with open(URLS_JSON_FILE, "r", encoding="utf-8") as file:
    URLS = json.load(file)

# Configure Selenium WebDriver
chrome_options = Options()
chrome_options.add_argument("--headless")  # Run in headless mode
chrome_options.add_argument("--disable-gpu")
chrome_options.add_argument("--no-sandbox")
chrome_options.add_argument("--disable-dev-shm-usage")

# Use webdriver-manager to automatically manage the ChromeDriver
service = Service(ChromeDriverManager().install())  # Automatically handles driver installation
driver = webdriver.Chrome(service=service, options=chrome_options)

# Function to download and save HTML content
def download_html(url):
    try:
        driver.get(url)
        time.sleep(5)  # Wait for JavaScript to execute, adjust as needed

        html_content = driver.page_source

        # Create a valid filename
        filename = url.replace("https://", "").replace("http://", "").replace("/", "_") + ".html"
        filepath = os.path.join(FOLDER_NAME, filename)

        # Save HTML to file
        with open(filepath, "w", encoding="utf-8") as file:
            file.write(html_content)
        
        print(f"Saved: {filepath}")

    except Exception as e:
        print(f"Error processing {url}: {e}")

# Loop through URLs and download pages
for url in URLS:
    download_html(url)

# Close WebDriver
driver.quit()
