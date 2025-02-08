from bs4 import BeautifulSoup

def extract_seo_and_content(file_path):
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

    # Extract paragraphs (<p> tags) and other content-rich tags like <div>, <section>, <article>
    paragraphs = [p.get_text(strip=True) for p in soup.find_all('p')]
    divs = [div.get_text(separator=' ', strip=True) for div in soup.find_all(['div', 'section', 'article'])]
    
    # Combine all relevant content
    main_content = paragraphs + divs
    cleaned_content = ' '.join(main_content)

    return {
        'meta': meta_tags,
        'title': title,
        'links': links,
        'headings': headings,
        'content': cleaned_content
    }

def write_seo_and_content_to_txt(seo_data, output_file):
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
output_file = 'seo_and_content_data_v2.txt'

# Extract SEO-related data and content from the HTML file
seo_data = extract_seo_and_content(file_path)

# Write the extracted data to a text file
write_seo_and_content_to_txt(seo_data, output_file)

print(f"SEO data and content have been written to {output_file}")
