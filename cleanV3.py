from bs4 import BeautifulSoup

def extract_seo_and_content_with_labels(file_path):
    # Load the HTML file
    with open(file_path, 'r', encoding='utf-8') as file:
        html = file.read()

    # Parse the HTML with BeautifulSoup
    soup = BeautifulSoup(html, "html.parser")

    # Remove all <script> tags
    for script in soup(['script']):
        script.decompose()

    # Extract <meta> tags (for SEO-related content)
    meta_tags = {}
    for meta in soup.find_all('meta'):
        name = meta.get('name') or meta.get('property')  # Some SEO-related metadata use 'property'
        if name:
            content = meta.get('content')
            meta_tags[name] = content

    # Extract <title> tag
    title = soup.title.string.strip() if soup.title else 'No Title'

    # Extract <link> tags (e.g., for canonical links)
    links = []
    for link in soup.find_all('link'):
        href = link.get('href')
        if href:
            links.append(href)

    # Extract headings like <h1>, <h2>, etc.
    headings = {}
    for i in range(1, 7):  # <h1> to <h6>
        headings[f'h{i}'] = [heading.get_text(strip=True) for heading in soup.find_all(f'h{i}')]

    # Extract content and organize it based on <div>, <section>, <article>, etc.
    sections = []
    for section in soup.find_all(['div', 'section', 'article']):
        section_text = section.get_text(separator=' ', strip=True)
        # Skip empty sections
        if section_text:
            section_label = f"Section: {section.name}, Class: {section.get('class')}, ID: {section.get('id')}"
            sections.append({
                'label': section_label,
                'content': section_text
            })
    
    # Combine and clean the content
    cleaned_sections = "\n".join([f"{s['label']}\n{s['content']}" for s in sections])

    return {
        'meta': meta_tags,
        'title': title,
        'links': links,
        'headings': headings,
        'sections': cleaned_sections
    }

def write_seo_and_content_to_txt_with_labels(seo_data, output_file):
    with open(output_file, 'w', encoding='utf-8') as f:
        # Write the Title
        f.write(f"• Title: {seo_data['title']}\n\n")
        
        # Write the Meta Tags
        f.write("• Meta Tags:\n")
        for name, content in seo_data['meta'].items():
            f.write(f"    - {name}: {content}\n")
        
        # Write the Links
        f.write("\n• Links:\n")
        for link in seo_data['links']:
            f.write(f"    - {link}\n")
        
        # Write the Headings
        f.write("\n• Headings:\n")
        for heading_level, headings in seo_data['headings'].items():
            for heading in headings:
                f.write(f"    - {heading_level}: {heading}\n")
        
        # Write the sections (organized by div, section, article)
        f.write("\n• Sections:\n")
        f.write(seo_data['sections'])

# Example usage
file_path = 'leapsandrebounds.com_.html'
output_file = 'seo_and_organized_content_V3.txt'

# Extract SEO-related data and content from the HTML file
seo_data = extract_seo_and_content_with_labels(file_path)

# Write the extracted data to a text file
write_seo_and_content_to_txt_with_labels(seo_data, output_file)

print(f"SEO data and organized content have been written to {output_file}")
