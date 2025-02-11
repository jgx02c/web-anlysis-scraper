import os
import json
from bs4 import BeautifulSoup

def extract_seo_and_content(file_path):
    """Extracts metadata, links, headings, and content from an HTML file."""
    with open(file_path, 'r', encoding='utf-8') as file:
        html = file.read()

    soup = BeautifulSoup(html, "html.parser")

    # Remove unnecessary scripts
    for script in soup(['script', 'style']):
        script.decompose()

    # Categorize meta tags
    meta_tags = {
        "SEO": {},
        "Social Media": {},
        "Technical": {}
    }

    for meta in soup.find_all('meta'):
        name = meta.get('name') or meta.get('property')
        content = meta.get('content')

        if name and content:
            if name in ["description", "keywords"]:
                meta_tags["SEO"][name] = content
            elif name.startswith("og:") or name.startswith("twitter:"):
                meta_tags["Social Media"][name] = content
            else:
                meta_tags["Technical"][name] = content

    # Extract page title
    title = soup.title.string.strip() if soup.title else "No Title"

    # Extract all links
    links = [link.get('href') for link in soup.find_all('link') if link.get('href')]

    # Extract headings by level
    headings = {f"h{i}": [h.get_text(strip=True) for h in soup.find_all(f"h{i}")] for i in range(1, 7)}

    # Extract text content
    paragraphs = [p.get_text(strip=True) for p in soup.find_all('p')]
    divs = [div.get_text(separator=' ', strip=True) for div in soup.find_all(['div', 'section', 'article'])]
    cleaned_content = ' '.join(paragraphs + divs)

    return {
        "title": title,
        "meta": meta_tags,
        "links": links,
        "headings": headings,
        "content": cleaned_content
    }

def generate_insights(seo_data):
    """Generates insights based on the extracted SEO and content data."""
    insights = []

    # SEO Insights
    if "description" in seo_data["meta"]["SEO"]:
        insights.append(f"The page has a meta description: '{seo_data['meta']['SEO']['description']}'. This helps with search engine rankings.")
    else:
        insights.append("No meta description found. This may negatively impact SEO.")

    # Social Media Insights
    if "og:title" in seo_data["meta"]["Social Media"]:
        insights.append(f"The Open Graph title is '{seo_data['meta']['Social Media']['og:title']}', which is used for social media sharing.")

    # Heading Structure Insights
    heading_counts = {level: len(headings) for level, headings in seo_data["headings"].items() if headings}
    if not heading_counts:
        insights.append("No headings detected. This may impact content readability and SEO.")
    else:
        insights.append(f"The page has the following heading structure: {heading_counts}")

    # Content Length Insights
    word_count = len(seo_data["content"].split())
    if word_count < 100:
        insights.append(f"The page has only {word_count} words. This may be too little content for good SEO.")
    elif word_count > 1000:
        insights.append(f"The page has {word_count} words, which is great for in-depth SEO content.")

    seo_data["insights"] = insights
    return seo_data

def write_seo_and_content_to_json(seo_data, output_file):
    """Writes extracted SEO and content data to a JSON file."""
    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump(seo_data, f, indent=4, ensure_ascii=False)

# Prompt user for folder input
input_folder = input("Enter the folder containing HTML files: ")
output_folder = os.path.join(input_folder, "output")
os.makedirs(output_folder, exist_ok=True)

# Process each HTML file
for file_name in os.listdir(input_folder):
    if file_name.lower().endswith(".html"):
        input_file = os.path.join(input_folder, file_name)
        output_file = os.path.join(output_folder, f"{file_name.rsplit('.', 1)[0]}.json")  # JSON output
        seo_data = extract_seo_and_content(input_file)
        seo_data = generate_insights(seo_data)  # Add insights
        write_seo_and_content_to_json(seo_data, output_file)
        print(f"Processed {file_name} -> {output_file}")

print("All HTML files have been processed.")
