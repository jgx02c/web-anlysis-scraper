import os
from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import letter
from reportlab.lib.styles import ParagraphStyle
from reportlab.platypus import Paragraph, SimpleDocTemplate, Spacer
from reportlab.lib.units import inch
import argparse

def detect_structure(text):
    """Detect and categorize different parts of the text structure."""
    sections = []
    current_section = []
    is_list = False
    
    for line in text.split('\n'):
        # Detect list items
        if line.strip().startswith('- ') or line.strip().startswith('• '):
            if not is_list:
                # If we have content before the list, add it as a paragraph
                if current_section:
                    sections.append(('paragraph', '\n'.join(current_section)))
                    current_section = []
                is_list = True
            current_section.append(line.strip())
        # Detect meta tags (assuming they're in < >)
        elif line.strip().startswith('<') and line.strip().endswith('>'):
            if current_section:
                sections.append(('paragraph' if not is_list else 'list', '\n'.join(current_section)))
                current_section = []
            is_list = False
            sections.append(('meta', line.strip()))
        # Handle empty lines as section breaks
        elif not line.strip():
            if current_section:
                sections.append(('paragraph' if not is_list else 'list', '\n'.join(current_section)))
                current_section = []
            is_list = False
        # Regular text lines
        else:
            if is_list and not line.strip().startswith('- '):
                # End of list
                sections.append(('list', '\n'.join(current_section)))
                current_section = []
                is_list = False
            current_section.append(line.strip())
    
    # Add any remaining content
    if current_section:
        sections.append(('paragraph' if not is_list else 'list', '\n'.join(current_section)))
    
    return sections

def create_paragraph_styles():
    """Create different styles for different types of text."""
    return {
        'normal': ParagraphStyle(
            'normal',
            fontSize=11,
            leading=14,
            spaceAfter=10
        ),
        'meta': ParagraphStyle(
            'meta',
            fontSize=11,
            leading=14,
            textColor='blue',
            spaceAfter=12
        ),
        'list': ParagraphStyle(
            'list',
            fontSize=11,
            leading=14,
            leftIndent=20,
            spaceAfter=3
        )
    }

def convert_txt_to_pdf(input_folder, output_folder=None):
    """
    Convert all .txt files in the input folder to PDF format while preserving structure.
    
    Args:
        input_folder (str): Path to the folder containing .txt files
        output_folder (str, optional): Path to save the PDF files. If None, uses input folder
    """
    
    if output_folder is None:
        output_folder = input_folder
    
    if not os.path.exists(output_folder):
        os.makedirs(output_folder)
    
    styles = create_paragraph_styles()
    converted_count = 0
    errors = []
    
    txt_files = [f for f in os.listdir(input_folder) if f.endswith('.txt')]
    
    for txt_file in txt_files:
        try:
            txt_path = os.path.join(input_folder, txt_file)
            pdf_name = os.path.splitext(txt_file)[0] + '.pdf'
            pdf_path = os.path.join(output_folder, pdf_name)
            
            # Read text content
            with open(txt_path, 'r', encoding='utf-8') as file:
                text_content = file.read()
            
            # Create PDF document
            doc = SimpleDocTemplate(
                pdf_path,
                pagesize=letter,
                rightMargin=72,
                leftMargin=72,
                topMargin=72,
                bottomMargin=72
            )
            
            # Process the text structure
            story = []
            sections = detect_structure(text_content)
            
            for section_type, content in sections:
                if section_type == 'meta':
                    # Meta tags in blue
                    story.append(Paragraph(content, styles['meta']))
                elif section_type == 'list':
                    # Process list items
                    lines = content.split('\n')
                    for line in lines:
                        story.append(Paragraph(line, styles['list']))
                else:
                    # Regular paragraphs
                    story.append(Paragraph(content, styles['normal']))
                    story.append(Spacer(1, 12))
            
            # Build the PDF
            doc.build(story)
            converted_count += 1
            print(f"Converted: {txt_file} -> {pdf_name}")
            
        except Exception as e:
            errors.append(f"Error converting {txt_file}: {str(e)}")
    
    # Print summary
    print(f"\nConversion complete!")
    print(f"Successfully converted: {converted_count} files")
    if errors:
        print("\nErrors encountered:")
        for error in errors:
            print(error)

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Convert TXT files to PDF format")
    parser.add_argument("input_folder", help="Folder containing TXT files")
    parser.add_argument("--output_folder", help="Optional output folder for PDF files")
    args = parser.parse_args()
    
    convert_txt_to_pdf(args.input_folder, args.output_folder)