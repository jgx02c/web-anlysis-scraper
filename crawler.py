import requests
from bs4 import BeautifulSoup
import json
import urllib.parse

def extract_links(url):
    # Send a GET request to the URL
    response = requests.get(url)
    
    # Check if the request was successful
    if response.status_code == 200:
        # Parse the HTML content of the page
        soup = BeautifulSoup(response.content, 'html.parser')
        
        # Find all <a> tags, which represent links
        links = soup.find_all('a', href=True)
        
        # Extract the href attributes and resolve relative URLs
        urls = []
        for link in links:
            href = link['href']
            # Resolve relative URLs to absolute URLs
            full_url = urllib.parse.urljoin(url, href)
            urls.append(full_url)
        
        return urls
    else:
        print(f"Error: Unable to fetch the page (status code: {response.status_code})")
        return []

def save_to_json(data, filename='urls.json'):
    # Save the data to a JSON file
    with open(filename, 'w') as json_file:
        json.dump(data, json_file, indent=4)
    print(f"Data has been saved to {filename}")

if __name__ == "__main__":
    # Input URL
    input_url = input("Enter the URL: ")
    
    # Extract links from the given URL
    urls = extract_links(input_url)
    
    # Save the list of URLs to a JSON file
    save_to_json(urls)
