import os
import json
import re
from bs4 import BeautifulSoup
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Load SEO rules
def load_seo_rules():
    script_dir = os.path.dirname(os.path.abspath(__file__))
    rules_path = os.path.join(script_dir, 'seo_rules.json')
    try:
        with open(rules_path, 'r') as f:
            return json.load(f)
    except FileNotFoundError:
        print(f"Warning: SEO rules file not found at {rules_path}")
        return {}
    except json.JSONDecodeError:
        print("Warning: Invalid JSON in SEO rules file")
        return {}

# Load SEO rules
SEO_RULES = load_seo_rules()

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

    # Find canonical link
    canonical_link = soup.find('link', {'rel': 'canonical'})
    if canonical_link:
        meta_tags["SEO"]["canonical"] = canonical_link.get('href')

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
    links = []
    for link in soup.find_all('a', href=True):
        href = link.get('href')
        if href:
            text = link.get_text(strip=True)
            links.append({
                'href': href,
                'text': text,
                'nofollow': 'nofollow' in link.get('rel', [])
            })

    internal_links = [link for link in links if is_internal_link(link['href'])]
    external_links = [link for link in links if not is_internal_link(link['href'])]

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
    js_content = soup.find_all(['[onclick]', '[onload]', '[onscroll]'])

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

def is_internal_link(href):
    """Determines if a link is internal."""
    return href.startswith('/') or 'leapsandrebounds.com' in href

def extract_url_from_filename(file_path):
    """Extracts the domain and path from a file path."""
    # Split the path into parts
    parts = file_path.split('leapsandrebounds.com/')
    if len(parts) < 2:
        return None
        
    # Get everything after leapsandrebounds.com/
    path = parts[1]
    
    # Remove .html extension if present
    path = re.sub(r'\.html$', '', path)
    
    # Return full URL
    return f"https://leapsandrebounds.com/{path}"

def check_url_rules(url, rules):
    """Checks URL against defined rules and returns any violations."""
    insights = []
    
    # Extract just the path if specified
    if rules.get("path_only"):
        url_parts = url.split('.com/')
        if len(url_parts) > 1:
            check_path = url_parts[1]
        else:
            check_path = url
    else:
        check_path = url
        
    # Check each rule
    for rule in rules["rules"]:
        if re.search(rule["pattern"], check_path):
            if rule["severity"] == "immediate":
                category = "Immediate Action Required"
            else:
                category = "Needs Attention"
            insights.append((category, rule["message"]))
            
    return insights

def generate_insights(seo_data):
    """Generates SEO insights based on technical SEO requirements."""
    insights = {
        "Immediate Action Required": [],
        "Needs Attention": [],
        "Good Practice": []
    }

    # Check title rules
    title_rules = SEO_RULES["title"]
    if not seo_data["title"] or seo_data["title"] == "No Title":
        if title_rules["severity"] == "immediate":
            insights["Immediate Action Required"].append(title_rules["messages"]["missing"])
    elif len(seo_data["title"]) > title_rules["max_length"]:
        insights["Needs Attention"].append(title_rules["messages"]["too_long"].format(
            length=len(seo_data["title"])
        ))
    else:
        insights["Good Practice"].append(title_rules["messages"]["good"])

    # Meta tags checks
    meta_seo = seo_data["meta"]["SEO"]
    meta_tech = seo_data["meta"]["Technical"]

    # Check canonical tag
    if not meta_seo.get("canonical"):
        insights["Needs Attention"].append("No canonical tag found. Consider adding one to prevent duplicate content issues.")

    # Meta description check
    meta_desc_rules = SEO_RULES["meta_description"]
    if not meta_seo.get("description"):
        insights["Immediate Action Required"].append(meta_desc_rules["messages"]["missing"])
    elif len(meta_seo.get("description", "")) > meta_desc_rules["max_length"]:
        insights["Needs Attention"].append(meta_desc_rules["messages"]["too_long"])

    # Mobile viewport check
    if not meta_tech.get("viewport"):
        insights["Needs Attention"].append("Missing viewport meta tag. Required for mobile-first indexing.")

    # Content length check
    content_rules = SEO_RULES["content"]
    if seo_data["word_count"] < content_rules["min_words"]:
        insights["Needs Attention"].append(content_rules["messages"]["too_short"].format(
            word_count=seo_data["word_count"]
        ))

    # Robots meta tag check
    robots_content = meta_seo.get("robots", "")
    if "noindex" in robots_content or "nofollow" in robots_content:
        insights["Immediate Action Required"].append("Robots meta tag is preventing indexing or following links.")

    # Frame usage check
    if seo_data["frames"] > 0:
        insights["Needs Attention"].append(f"Found {seo_data['frames']} frames/iframes. Ensure important content isn't hidden in frames.")

    # Login requirement check
    if seo_data["requires_login"]:
        insights["Needs Attention"].append("Page may require login to access. This could prevent Google from crawling content.")

    # JavaScript dependency check
    if seo_data["js_dependent_content"] > 0:
        insights["Needs Attention"].append(f"Found {seo_data['js_dependent_content']} elements that require JavaScript. Ensure critical content is available without JavaScript.")

    # Image checks
    missing_alt = sum(1 for img in seo_data["images"].values() if img["alt"] == "MISSING ALT TEXT")
    missing_dimensions = sum(1 for img in seo_data["images"].values() if not img["width"] or not img["height"])
    
    if missing_alt > 0:
        insights["Needs Attention"].append(f"{missing_alt} images missing alt text")
    if missing_dimensions > 0:
        insights["Needs Attention"].append(f"{missing_dimensions} images missing width/height attributes")

    # Language declaration check
    if not seo_data["html_lang"]:
        insights["Needs Attention"].append("Missing language declaration in <html> tag. Add lang attribute.")

    # Heading structure check
    heading_rules = SEO_RULES["headings"]["h1"]
    h1_count = len(seo_data["headings"]["h1"])
    if h1_count == 0:
        insights["Immediate Action Required"].append(heading_rules["messages"]["missing"])
    elif h1_count > heading_rules["max_count"]:
        insights["Needs Attention"].append(heading_rules["messages"]["too_many"].format(count=h1_count))

    # URL structure check
    url_insights = check_url_rules(seo_data["website_url"], SEO_RULES["url"])
    for category, message in url_insights:
        insights[category].append(message)

    return insights

def write_seo_and_content_to_json(seo_data, output_file):
    """Writes extracted SEO and content data to a JSON file."""
    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump(seo_data, f, indent=4, ensure_ascii=False)

# Main execution
folder_name = input("Enter the folder name (inside this directory): ").strip()
folder_path = os.path.join(os.getcwd(), folder_name)

output_folder = input("Enter the output folder name (where results will be saved): ").strip()
output_path = os.path.join(os.getcwd(), output_folder)
os.makedirs(output_path, exist_ok=True)

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