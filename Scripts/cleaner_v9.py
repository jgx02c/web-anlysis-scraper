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
os.makedirs(output_path, exist_ok=True)

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
    internal_links = [link for link in links if link and (link.startswith("/") or "domain.com" in link)]
    external_links = [link for link in links if link and "domain.com" not in link and not link.startswith("/")]

    # Extract headings by level
    headings = {f"h{i}": [h.get_text(strip=True) for h in soup.find_all(f"h{i}")] for i in range(1, 7)}

    # Extract images with src and alt text
    images = {}
    for img in soup.find_all("img"):
        src = img.get("src", "")
        alt = img.get("alt", "")
        width = img.get("width", "")
        height = img.get("height", "")
        images[src] = {
            "alt": alt if alt else "MISSING ALT TEXT",
            "width": width,
            "height": height,
            "lazy_loading": img.get("loading") == "lazy"
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
    text_content = soup.get_text(separator=' ', strip=True)
    word_count = len(text_content.split())

    # Check for frames and iframes
    frames = soup.find_all(['frame', 'iframe'])
    
    # Check for login forms
    login_forms = bool(soup.find('form', {'type': 'login'}) or soup.find('input', {'type': 'password'}))

    # Check for JavaScript-dependent content
    js_content = soup.find_all('div', {'data-js-content': True})

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
        "content": text_content,
        "word_count": word_count,
        "frames": len(frames),
        "requires_login": login_forms,
        "js_dependent_content": len(js_content),
        "html_lang": soup.find('html').get('lang', '')
    }

def generate_insights(seo_data):
    """Generates SEO insights based on technical SEO requirements."""
    insights = {
        "Immediate Action Required": [],
        "Needs Attention": [],
        "Good Practice": []
    }

    # Title Checks
    if not seo_data["title"] or seo_data["title"] == "No Title":
        insights["Immediate Action Required"].append("Missing or empty <title> tag. Every page must have a unique title.")
    elif len(seo_data["title"]) > 60:
        insights["Needs Attention"].append(f"Title length is {len(seo_data['title'])} characters. Consider keeping it under 60 characters.")
    else:
        insights["Good Practice"].append("Title tag is present and within recommended length.")

    # Meta Description Checks
    meta_seo = seo_data["meta"]["SEO"]
    meta_tech = seo_data["meta"]["Technical"]
    
    if not meta_seo.get("description"):
        insights["Immediate Action Required"].append("No meta description found. This is crucial for SEO.")
    elif len(meta_seo.get("description", "")) > 160:
        insights["Needs Attention"].append("Meta description exceeds 160 characters. Consider shortening it.")
    
    # Mobile Responsiveness Check
    if not meta_tech.get("viewport"):
        insights["Needs Attention"].append("Missing viewport meta tag. Required for mobile-first indexing.")

    # Content Length Check
    if seo_data["word_count"] < 300:
        insights["Needs Attention"].append(f"Page contains only {seo_data['word_count']} words. Consider adding more quality content.")

    # Robots Meta Tag Check
    robots_content = meta_seo.get("robots", "")
    if "noindex" in robots_content or "nofollow" in robots_content:
        insights["Immediate Action Required"].append("Robots meta tag is preventing indexing or following links.")

    # Frame Usage Check
    if seo_data["frames"] > 0:
        insights["Needs Attention"].append(f"Found {seo_data['frames']} frames/iframes. Ensure important content isn't hidden in frames.")

    # Login Requirement Check
    if seo_data["requires_login"]:
        insights["Needs Attention"].append("Page may require login to access. This could prevent Google from crawling content.")

    # JavaScript Dependency Check
    if seo_data["js_dependent_content"] > 0:
        insights["Needs Attention"].append(f"Found {seo_data['js_dependent_content']} elements that require JavaScript. Ensure critical content is available without JavaScript.")

    # Image Checks
    missing_alt = sum(1 for img in seo_data["images"].values() if img["alt"] == "MISSING ALT TEXT")
    missing_dimensions = sum(1 for img in seo_data["images"].values() if not img["width"] or not img["height"])
    
    if missing_alt > 0:
        insights["Needs Attention"].append(f"{missing_alt} images missing alt text")
    if missing_dimensions > 0:
        insights["Needs Attention"].append(f"{missing_dimensions} images missing width/height attributes")

    # Language Declaration Check
    if not seo_data["html_lang"]:
        insights["Needs Attention"].append("Missing language declaration in <html> tag. Add lang attribute.")

    # Heading Structure Check
    if len(seo_data["headings"]["h1"]) == 0:
        insights["Immediate Action Required"].append("No H1 tag found. Each page should have exactly one H1.")
    elif len(seo_data["headings"]["h1"]) > 1:
        insights["Needs Attention"].append(f"Multiple H1 tags found ({len(seo_data['headings']['h1'])}). Use only one H1 per page.")

    # URL Structure Check (only checking the path portion)
    url = seo_data["website_url"]
    path = re.sub(r'^https?://[^/]+', '', url)
    path = re.sub(r'\.com/', '', path)
    
    if re.search(r'[A-Z]', path):
        insights["Needs Attention"].append("URL path contains uppercase letters. URLs should be lowercase.")
    if re.search(r'[\s]', path):
        insights["Immediate Action Required"].append("URL path contains spaces. Use hyphens instead.")

    return insights

def extract_url_from_filename(file_name):
    """Converts a filename into a formatted website URL."""
    base_url = file_name.replace("_", "/")
    base_url = re.sub(r"(\.html)$", "", base_url)
    base_url = re.sub(r"^.*?domain\.com", "domain.com", base_url)
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
            insights = generate_insights(seo_data)
            seo_data["insights"] = insights
            write_seo_and_content_to_json(seo_data, output_file)

            print(f"Processed {file_name} -> {output_file}")
        except Exception as e:
            print(f"Error processing {file_name}: {str(e)}")

print("All HTML files have been processed.")