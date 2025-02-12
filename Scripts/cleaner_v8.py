import os
import json
import re
from bs4 import BeautifulSoup
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Ask for the folder name containing HTML files
folder_name = input("Enter the folder name (inside this directory): ").strip()
folder_path = os.path.join(os.getcwd(), folder_name)

# Ask for the output folder name where results will be saved
output_folder = input("Enter the output folder name (where results will be saved): ").strip()
output_path = os.path.join(os.getcwd(), output_folder)
os.makedirs(output_path, exist_ok=True)  # Create output folder if it doesn't exist

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

        # Check for charset in meta tag
        if meta.get('charset'):
            meta_tags["Technical"]["charset"] = meta.get('charset')

    # Extract page title
    title = soup.title.string.strip() if soup.title else "No Title"

    # Extract all links
    links = [link.get('href') for link in soup.find_all('a', href=True)]
    internal_links = [link for link in links if link and (link.startswith("/") or "leapsandrebounds.com" in link)]
    external_links = [link for link in links if link and "leapsandrebounds.com" not in link and not link.startswith("/")]

    # Extract headings by level
    headings = {f"h{i}": [h.get_text(strip=True) for h in soup.find_all(f"h{i}")] for i in range(1, 7)}

    # Extract images with src and alt text
    images = {}
    for img in soup.find_all("img"):
        src = img.get("src", "")
        alt = img.get("alt", "")
        images[src] = {
            "alt": alt if alt else "MISSING ALT TEXT",
            "width": img.get("width", ""),
            "height": img.get("height", "")
        }

    # Extract structured data (JSON-LD)
    json_ld_scripts = []
    for script in soup.find_all("script", type="application/ld+json"):
        try:
            if script.string:
                json_ld_scripts.append(json.loads(script.string))
        except json.JSONDecodeError:
            json_ld_scripts.append({"error": "Invalid JSON-LD"})

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
        "content": cleaned_content,
        "html_lang": soup.find('html').get('lang', '')
    }

def generate_insights(seo_data):
    """Generates SEO insights based on technical SEO requirements."""
    insights = {"Immediate Action Required": [], "Needs Attention": [], "Good Practice": []}

    # Title Checks
    if not seo_data["title"] or seo_data["title"] == "No Title":
        insights["Immediate Action Required"].append("Missing or empty <title> tag. Every page must have a unique title.")
    elif len(seo_data["title"]) > 60:
        insights["Needs Attention"].append(f"Title length is {len(seo_data['title'])} characters. Consider keeping it under 60 characters.")
    else:
        insights["Good Practice"].append("Title tag is present and within recommended length.")

    # Meta Description Checks
    meta_seo = seo_data["meta"]["SEO"]
    if not meta_seo.get("description"):
        insights["Immediate Action Required"].append("No meta description found. This is crucial for SEO.")
    elif len(meta_seo.get("description", "")) > 160:
        insights["Needs Attention"].append("Meta description exceeds 160 characters. Consider shortening it.")
    else:
        insights["Good Practice"].append("Meta description is present and within recommended length.")

    # URL Structure Checks
    url = seo_data["website_url"]
    if re.search(r'[A-Z]', url):
        insights["Needs Attention"].append("URL contains uppercase letters. URLs should be lowercase.")
    if re.search(r'[\s]', url):
        insights["Immediate Action Required"].append("URL contains spaces. Use hyphens instead.")
    if re.search(r'[^a-zA-Z0-9\-/_\.]', url):
        insights["Immediate Action Required"].append("URL contains special characters. Use only letters, numbers, and hyphens.")

    # Language Declaration Check
    if not seo_data["html_lang"]:
        insights["Needs Attention"].append("Missing language declaration in <html> tag. Add lang attribute.")

    # Heading Structure Checks
    if len(seo_data["headings"]["h1"]) == 0:
        insights["Immediate Action Required"].append("No H1 tag found. Each page should have exactly one H1.")
    elif len(seo_data["headings"]["h1"]) > 1:
        insights["Needs Attention"].append(f"Multiple H1 tags found ({len(seo_data['headings']['h1'])}). Use only one H1 per page.")
    else:
        insights["Good Practice"].append("Page has exactly one H1 tag.")

    # Technical Meta Tags
    meta_tech = seo_data["meta"]["Technical"]
    if not meta_tech.get("viewport"):
        insights["Needs Attention"].append("Missing viewport meta tag. Important for mobile responsiveness.")
    if not meta_tech.get("charset"):
        insights["Needs Attention"].append("Missing character encoding declaration. Add meta charset tag.")

    # Canonical Tag Check
    if not meta_seo.get("canonical"):
        insights["Needs Attention"].append("No canonical tag found. Consider adding one to prevent duplicate content issues.")

    # Image Checks
    for src, img_data in seo_data["images"].items():
        if not src or src.isspace():
            insights["Immediate Action Required"].append("Found image with empty src attribute.")
        if src.startswith('data:'):
            insights["Needs Attention"].append("Found base64 encoded image. Use proper image files for better performance.")
        if img_data["alt"] == "MISSING ALT TEXT":
            insights["Needs Attention"].append(f"Image missing alt text: {src}")
        if not img_data["width"] or not img_data["height"]:
            insights["Needs Attention"].append(f"Image missing width/height attributes: {src}")

    # Structured Data Validation
    if not seo_data["structured_data"]:
        insights["Needs Attention"].append("No structured data (JSON-LD) found. Consider adding schema markup.")
    else:
        for data in seo_data["structured_data"]:
            if isinstance(data, dict) and data.get("error"):
                insights["Immediate Action Required"].append("Invalid JSON-LD structured data found.")
            elif not data.get("@context") or not data.get("@type"):
                insights["Needs Attention"].append("Structured data missing required @context or @type properties.")

    # Link Checks
    total_internal = len(seo_data["links"]["internal"])
    total_external = len(seo_data["links"]["external"])
    
    if total_internal == 0:
        insights["Needs Attention"].append("No internal links found. Consider adding some for better site structure.")
    else:
        insights["Good Practice"].append(f"Found {total_internal} internal links.")

    seo_data["insights"] = insights
    return seo_data

def extract_url_from_filename(file_name):
    """Converts a filename into a formatted website URL."""
    base_url = file_name.replace("_", "/")
    base_url = re.sub(r"(\.html)$", "", base_url)  # Remove the .html extension
    base_url = re.sub(r"^.*?leapsandrebounds\.com", "leapsandrebounds.com", base_url)
    return f"https://{base_url}"

def write_seo_and_content_to_json(seo_data, output_file):
    """Writes extracted SEO and content data to a JSON file."""
    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump(seo_data, f, indent=4, ensure_ascii=False)

# Process each HTML file
for file_name in os.listdir(folder_path):
    if file_name.lower().endswith(".html"):
        try:
            input_file = os.path.join(folder_path, file_name)
            output_file = os.path.join(output_path, f"{file_name.rsplit('.', 1)[0]}.json")

            seo_data = extract_seo_and_content(input_file)
            seo_data = generate_insights(seo_data)
            write_seo_and_content_to_json(seo_data, output_file)

            print(f"Processed {file_name} -> {output_file}")
        except Exception as e:
            print(f"Error processing {file_name}: {str(e)}")

print("All HTML files have been processed.")