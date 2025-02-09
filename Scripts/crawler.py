import requests
from bs4 import BeautifulSoup
import json
import urllib.parse

def extract_links(url):
    response = requests.get(url)
    if response.status_code == 200:
        soup = BeautifulSoup(response.content, 'html.parser')
        links = soup.find_all('a', href=True)
        urls = [urllib.parse.urljoin(url, link['href']) for link in links]
        return urls
    else:
        print(f"Error: Unable to fetch the page (status code: {response.status_code})")
        return []

def save_to_json(data, filename):
    with open(filename, 'w') as json_file:
        json.dump(data, json_file, indent=4)
    print(f"Data has been saved to {filename}")

if __name__ == "__main__":
    input_url = input("Enter the URL: ")
    json_filename = input("Enter the name of the JSON file (with .json extension): ")
    
    urls = extract_links(input_url)
    save_to_json(urls, json_filename)
