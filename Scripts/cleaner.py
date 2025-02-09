import os
from bs4 import BeautifulSoup

def extract_seo_and_content(file_path):
    with open(file_path, 'r', encoding='utf-8') as file:
        html = file.read()

    soup = BeautifulSoup(html, "html.parser")

    for script in soup(['script']):
        script.decompose()

    meta_tags = {}
    for meta in soup.find_all('meta'):
        name = meta.get('name') or meta.get('property')
        if name:
            content = meta.get('content')
            meta_tags[name] = content

    title = soup.title.string.strip() if soup.title else 'No Title'

    links = [link.get('href') for link in soup.find_all('link') if link.get('href')]

    headings = {f'h{i}': [h.get_text(strip=True) for h in soup.find_all(f'h{i}')] for i in range(1, 7)}

    paragraphs = [p.get_text(strip=True) for p in soup.find_all('p')]
    divs = [div.get_text(separator=' ', strip=True) for div in soup.find_all(['div', 'section', 'article'])]
    
    cleaned_content = ' '.join(paragraphs + divs)

    return {
        'meta': meta_tags,
        'title': title,
        'links': links,
        'headings': headings,
        'content': cleaned_content
    }

def write_seo_and_content_to_txt(seo_data, output_file):
    with open(output_file, 'w', encoding='utf-8') as f:
        f.write(f"• Title: {seo_data['title']}\n\n")
        f.write("• Meta Tags:\n")
        for name, content in seo_data['meta'].items():
            f.write(f"    - {name}: {content}\n")
        f.write("\n• Links:\n")
        for link in seo_data['links']:
            f.write(f"    - {link}\n")
        f.write("\n• Headings:\n")
        for level, headings in seo_data['headings'].items():
            for heading in headings:
                f.write(f"    - {level}: {heading}\n")
        f.write("\n• Content:\n")
        f.write(f"    {seo_data['content']}\n")

# Prompt user for folder input
input_folder = input("Enter the folder containing HTML files: ")
output_folder = os.path.join(input_folder, "output")
os.makedirs(output_folder, exist_ok=True)

for file_name in os.listdir(input_folder):
    if file_name.lower().endswith(".html"):
        input_file = os.path.join(input_folder, file_name)
        output_file = os.path.join(output_folder, f"{file_name.rsplit('.', 1)[0]}.txt")
        seo_data = extract_seo_and_content(input_file)
        write_seo_and_content_to_txt(seo_data, output_file)
        print(f"Processed {file_name} -> {output_file}")

print("All HTML files have been processed.")
