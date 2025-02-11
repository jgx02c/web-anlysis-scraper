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
    """Generates SEO insights categorized into 'good' and 'bad'."""
    insights = {"good": [], "bad": []}

    # Extract SEO metadata
    meta_seo = seo_data["meta"]["SEO"]
    meta_tech = seo_data["meta"]["Technical"]

    # Check for missing important meta tags
    if meta_seo.get("description"):
        insights["good"].append(f"Meta description found: '{meta_seo['description']}'.")
    else:
        insights["bad"].append("No meta description found. This can negatively impact SEO.")

    if meta_seo.get("og:title"):
        insights["good"].append(f"Open Graph title found: '{meta_seo['og:title']}'.")
    else:
        insights["bad"].append("No Open Graph title found. This may impact social media sharing.")

    if meta_seo.get("canonical"):
        insights["good"].append(f"Canonical tag found: '{meta_seo['canonical']}'.")
    else:
        insights["bad"].append("No canonical tag found. This could lead to duplicate content issues.")

    if "robots" in meta_seo and "noindex" in meta_seo["robots"]:
        insights["bad"].append("Page is set to 'noindex' and will not be indexed by search engines.")

    # Check for heading structure
    if seo_data["headings"]["h1"]:
        insights["good"].append(f"H1 tag found: '{seo_data['headings']['h1'][0]}'.")
    else:
        insights["bad"].append("No H1 tag found. Every page should have an H1 for SEO.")

    # Check content length
    word_count = len(seo_data["content"].split())
    if word_count < 100:
        insights["bad"].append(f"The page has only {word_count} words. This is too low for SEO.")
    elif word_count > 1000:
        insights["good"].append(f"The page has {word_count} words, which is ideal for in-depth SEO content.")

    # Check for internal and external links
    if len(seo_data["links"]["internal"]) > 0:
        insights["good"].append(f"Page contains {len(seo_data['links']['internal'])} internal links.")
    else:
        insights["bad"].append("No internal links found. Internal linking helps SEO and user navigation.")

    if len(seo_data["links"]["external"]) > 0:
        insights["good"].append(f"Page contains {len(seo_data['links']['external'])} external links.")
    else:
        insights["bad"].append("No external links found. Linking to high-authority sources is beneficial for SEO.")

    # Check for missing alt text in images
    missing_alt_images = [src for src, alt in seo_data["images"].items() if alt == "MISSING ALT TEXT"]
    if missing_alt_images:
        insights["bad"].append(f"{len(missing_alt_images)} images are missing alt text. This affects accessibility and SEO.")

    # Check for structured data (JSON-LD)
    if seo_data["structured_data"]:
        insights["good"].append("Structured data (JSON-LD) found, which helps search engines understand the page.")
    else:
        insights["bad"].append("No structured data (JSON-LD) found. Adding structured data can improve SEO.")

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
