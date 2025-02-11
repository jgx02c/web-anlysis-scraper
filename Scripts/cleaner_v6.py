import os
import json
import re
from bs4 import BeautifulSoup

def extract_seo_and_content(file_path):
    """Extracts metadata, links, headings, images, and content from an HTML file."""
    with open(file_path, 'r', encoding='utf-8') as file:
        html = file.read()

    soup = BeautifulSoup(html, "html.parser")

    # Remove unnecessary scripts and styles
    for tag in soup(['script', 'style']):
        tag.decompose()

    # Categorize meta tags
    meta_tags = {
        "SEO": {},
        "Technical": {},
        "Social Media": {}
    }

    for meta in soup.find_all('meta'):
        name = meta.get('name') or meta.get('property')
        content = meta.get('content')

        if name and content:
            if name in ["description", "keywords", "robots", "canonical"] or name.startswith("og:"):
                meta_tags["SEO"][name] = content
            elif name.startswith("twitter:"):
                meta_tags["Social Media"][name] = content
            else:
                meta_tags["Technical"][name] = content

    # Extract page title
    title = soup.title.string.strip() if soup.title else "No Title"

    # Extract all links
    links = [link.get('href') for link in soup.find_all('a', href=True)]
    internal_links = [link for link in links if link.startswith("/") or "leapsandrebounds.com" in link]
    external_links = [link for link in links if "leapsandrebounds.com" not in link and not link.startswith("/")]

    # Extract headings by level
    headings = {f"h{i}": [h.get_text(strip=True) for h in soup.find_all(f"h{i}")] for i in range(1, 7)}

    # Extract images and detect missing alt text
    images = {img.get("src"): img.get("alt") or "MISSING ALT TEXT" for img in soup.find_all("img")}

    # Extract structured data (JSON-LD)
    json_ld_scripts = [json.loads(script.string) for script in soup.find_all("script", type="application/ld+json") if script.string]

    # Extract text content
    paragraphs = [p.get_text(strip=True) for p in soup.find_all('p')]
    divs = [div.get_text(separator=' ', strip=True) for div in soup.find_all(['div', 'section', 'article'])]
    cleaned_content = ' '.join(paragraphs + divs)

    return {
        "website_url": extract_url_from_filename(file_path),
        "title": title,
        "meta": meta_tags,
        "links": {
            "internal": internal_links,
            "external": external_links
        },
        "headings": headings,
        "images": images,
        "structured_data": json_ld_scripts,
        "content": cleaned_content
    }

def generate_insights(seo_data):
    """Generates SEO insights categorized into 'Immediate Action', 'Needs Attention', and 'Good Practice'."""
    insights = {"Immediate Action Required": [], "Needs Attention": [], "Good Practice": []}

    # Extract SEO metadata
    meta_seo = seo_data["meta"]["SEO"]
    meta_tech = seo_data["meta"]["Technical"]

    # Immediate Action Required
    if "robots" in meta_seo and "noindex" in meta_seo["robots"]:
        insights["Immediate Action Required"].append("Page is set to 'noindex' and will not be indexed by search engines. This must be corrected immediately.")
    
    if not meta_seo.get("description"):
        insights["Immediate Action Required"].append("No meta description found. This is crucial for SEO and should be added immediately.")
    
    if not meta_seo.get("canonical"):
        insights["Immediate Action Required"].append("No canonical tag found. This can lead to duplicate content issues, which needs to be fixed.")

    # Needs Attention
    if not meta_seo.get("og:title"):
        insights["Needs Attention"].append("No Open Graph title found. This may impact social media sharing and should be added.")
    
    if not seo_data["headings"]["h1"]:
        insights["Needs Attention"].append("No H1 tag found. This is important for SEO and should be added.")

    if len(seo_data["content"].split()) < 100:
        insights["Needs Attention"].append(f"Page has only {len(seo_data['content'].split())} words. Consider adding more content for better SEO.")

    # Good Practice
    if seo_data["headings"]["h1"]:
        insights["Good Practice"].append(f"H1 tag found: '{seo_data['headings']['h1'][0]}'. Good practice for SEO.")

    if seo_data["links"]["internal"]:
        insights["Good Practice"].append(f"Page contains {len(seo_data['links']['internal'])} internal links. Good for internal linking SEO.")

    if seo_data["images"]:
        missing_alt_images = [src for src, alt in seo_data["images"].items() if alt == "MISSING ALT TEXT"]
        if missing_alt_images:
            insights["Needs Attention"].append(f"{len(missing_alt_images)} images are missing alt text. This should be corrected for better SEO and accessibility.")
    
    if seo_data["structured_data"]:
        insights["Good Practice"].append("Structured data (JSON-LD) found. This helps search engines understand the page.")

    seo_data["insights"] = insights
    return seo_data


def extract_url_from_filename(file_name):
    """Converts a filename into a formatted website URL."""
    base_url = file_name.replace("_", "/")
    base_url = re.sub(r"(\.html)$", "", base_url)  # Remove the .html extension
    base_url = re.sub(r"^.*?leapsandrebounds\.com", "leapsandrebounds.com", base_url)  # Remove folder and ensure it starts with domain
    return f"https://{base_url}"

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
        output_file = os.path.join(output_folder, f"{file_name.rsplit('.', 1)[0]}.json")

        seo_data = extract_seo_and_content(input_file)
        seo_data = generate_insights(seo_data)  # Add insights
        write_seo_and_content_to_json(seo_data, output_file)

        print(f"Processed {file_name} -> {output_file}")

print("All HTML files have been processed.")
