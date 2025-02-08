from bs4 import BeautifulSoup

def extract_seo_content(file_path):
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

    # Extract the main content (you could define this more specifically based on the structure of your HTML)
    content = soup.get_text(separator=' ', strip=True)

    # Clean up content if necessary (for example, remove excessive spaces)
    cleaned_content = ' '.join(content.split())

    return {
        'meta': meta_tags,
        'title': title,
        'links': links,
        'headings': headings,
        'content': cleaned_content
    }

def write_seo_data_to_txt(seo_data, output_file):
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
        
        # Write the main content
        f.write("\n• Content:\n")
        f.write(f"    {seo_data['content']}\n")

# Example usage
file_path = 'leapsandrebounds.com_.html'
output_file = 'seo_data.txt'

# Extract SEO-related data from the HTML file
seo_data = extract_seo_content(file_path)

# Write the extracted data to a text file
write_seo_data_to_txt(seo_data, output_file)

print(f"SEO data has been written to {output_file}")
