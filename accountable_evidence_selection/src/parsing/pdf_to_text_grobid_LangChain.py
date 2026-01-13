#!/usr/bin/env python3
"""
Improved GROBID LangChain Parser for Clinical Guidelines
- Preserves sequential section order without merging
- Handles paragraph continuity across page breaks
- Improves section detection accuracy
- Filters out interrupting tables/figures
"""

import os
from langchain_community.document_loaders.generic import GenericLoader
from langchain_community.document_loaders.parsers import GrobidParser
from collections import defaultdict
import re

def extract_pdf_with_grobid_sequential(pdf_path, output_path, grobid_url="http://localhost:8070"):
    """
    Extract text from PDF using GROBID with sequential section processing.
    
    Args:
        pdf_path (str): Path to the input PDF file
        output_path (str): Path to the output text file
        grobid_url (str): URL of the GROBID server
    """
    try:
        print(f"Starting sequential GROBID extraction for: {pdf_path}")
        print(f"GROBID server URL: {grobid_url}")
        
        # Create GROBID parser with sentence segmentation enabled for better paragraph handling
        parser = GrobidParser(segment_sentences=True)
        
        # Create loader for the PDF file
        loader = GenericLoader.from_filesystem(
            os.path.dirname(pdf_path),
            glob=os.path.basename(pdf_path),
            suffixes=[".pdf"],
            parser=parser,
        )
        
        # Load documents
        print("Processing PDF with GROBID...")
        docs = loader.load()
        
        if not docs:
            print("No documents were extracted.")
            return
        
        print(f"Successfully extracted {len(docs)} document sections")
        
        # Process sections sequentially without merging
        sequential_sections = process_sequential_sections(docs)
        
        # Format the sequential content with de-duplicated headers
        formatted_content = ""
        
        current_title = None
        section_index = 0
        
        for section_data in sequential_sections:
            title = section_data['title']
            content = section_data['content']
            
            # If this is a new section title, open a new section block
            if title != current_title:
                section_index += 1
                current_title = title
                
                # Create section header once per contiguous title
                section_header = f"\n{'='*80}\n"
                section_header += f"SECTION {section_index}: {title}\n"
                section_header += f"{'='*80}\n"
                section_header += f"Page: {section_data['page']}\n"
                section_header += f"{'='*80}\n\n"
                formatted_content += section_header
            
            # Append content under the current section without repeating header
            formatted_content += content + "\n\n"
        
        # Save formatted text
        with open(output_path, 'w', encoding='utf-8') as output_file:
            output_file.write(formatted_content)
        
        print(f"✅ Sequential extraction completed successfully!")
        print(f"📄 Text saved to: {output_path}")
        print(f"📈 Total sections: {section_index}")
        print(f"📝 Total characters: {len(formatted_content)}")
        
    except Exception as e:
        print(f"❌ Error during GROBID processing: {str(e)}")

def process_sequential_sections(docs):
    """
    Process sections sequentially without merging, handling paragraph continuity.
    
    Args:
        docs: List of document objects from GROBID
        
    Returns:
        list: Sequential sections with improved content handling
    """
    # Sort documents by page and paragraph number
    sorted_docs = sorted(docs, key=lambda x: (
        extract_page_number(x.metadata.get('pages', '0')),
        int(x.metadata.get('para', '0'))
    ))
    
    sequential_sections = []
    current_paragraph = None
    paragraph_buffer = []
    seen_sections = set()  # Track seen sections to avoid duplicates
    
    for i, doc in enumerate(sorted_docs):
        metadata = doc.metadata
        content = doc.page_content.strip()
        
        if not content:
            continue
        
        # Determine section type
        section_type = determine_section_type(metadata, content)
        
        # Create section identifier to check for duplicates
        section_id = f"{extract_page_number(metadata.get('pages', '0'))}_{metadata.get('para', '0')}_{content[:50]}"
        
        # Skip duplicate sections
        if section_id in seen_sections:
            continue
        seen_sections.add(section_id)
        
        # Handle paragraph continuity
        if section_type == 'paragraph':
            if should_continue_paragraph(metadata, current_paragraph):
                # Continue current paragraph
                paragraph_buffer.append(content)
                current_paragraph = {
                    'metadata': metadata,
                    'content_parts': paragraph_buffer
                }
            else:
                # Save previous paragraph if exists
                if current_paragraph:
                    sequential_sections.append(create_paragraph_section(current_paragraph))
                
                # Start new paragraph
                paragraph_buffer = [content]
                current_paragraph = {
                    'metadata': metadata,
                    'content_parts': paragraph_buffer
                }
        else:
            # Save current paragraph before processing non-paragraph content
            if current_paragraph:
                sequential_sections.append(create_paragraph_section(current_paragraph))
                current_paragraph = None
                paragraph_buffer = []
            
            # Process non-paragraph content (headers, tables, etc.)
            if should_include_content(section_type, content):
                sequential_sections.append({
                    'title': clean_section_title(metadata.get('section_title', 'Unknown')),
                    'content': content,
                    'page': extract_page_number(metadata.get('pages', '0')),
                    'paragraph': metadata.get('para', '0'),
                    'content_length': len(content),
                    'type': section_type
                })
    
    # Save final paragraph if exists
    if current_paragraph:
        sequential_sections.append(create_paragraph_section(current_paragraph))
    
    return sequential_sections

def determine_section_type(metadata, content):
    """
    Determine the type of content section.
    
    Args:
        metadata: Document metadata
        content: Document content
        
    Returns:
        str: Section type ('header', 'paragraph', 'table', 'figure', 'other')
    """
    # Check for section titles - only if content is short and looks like a title
    section_title = metadata.get('section_title', '')
    if section_title and section_title != 'None':
        # If content is short and matches the section title, it's likely a header
        if len(content.strip()) < 200 and content.strip().lower() in section_title.lower():
            return 'header'
        # If content is longer, it's likely paragraph content with a section title
        else:
            return 'paragraph'
    
    # Check for table indicators
    if is_table_content(content):
        return 'table'
    
    # Check for figure/image indicators
    if is_figure_content(content):
        return 'figure'
    
    # Default to paragraph
    return 'paragraph'

def is_table_content(content):
    """
    Check if content appears to be a table.
    
    Args:
        content: Document content
        
    Returns:
        bool: True if content appears to be a table
    """
    # Look for table indicators
    table_indicators = [
        r'\|\s*',  # Pipe characters
        r'\s+\|\s+',  # Spaces around pipes
        r'Table\s+\d+',  # "Table 1", "Table 2", etc.
        r'^\s*\d+\s+\d+\s+\d+',  # Number sequences
        r'^\s*[A-Z]\s+[A-Z]\s+[A-Z]',  # Letter sequences
    ]
    
    for pattern in table_indicators:
        if re.search(pattern, content, re.MULTILINE):
            return True
    
    # Check for tabular structure
    lines = content.split('\n')
    if len(lines) > 2:
        # Check if multiple lines have similar structure
        pipe_count = sum(1 for line in lines if '|' in line)
        if pipe_count > len(lines) * 0.3:  # More than 30% of lines have pipes
            return True
    
    return False

def is_figure_content(content):
    """
    Check if content appears to be a figure or image.
    
    Args:
        content: Document content
        
    Returns:
        bool: True if content appears to be a figure
    """
    figure_indicators = [
        r'Figure\s+\d+',
        r'Fig\.\s+\d+',
        r'\[Figure',
        r'\[Image',
        r'\[Graph',
        r'\[Chart',
    ]
    
    for pattern in figure_indicators:
        if re.search(pattern, content, re.IGNORECASE):
            return True
    
    return False

def should_continue_paragraph(current_metadata, previous_paragraph):
    """
    Determine if current content should continue the previous paragraph.
    
    Args:
        current_metadata: Current document metadata
        previous_paragraph: Previous paragraph data
        
    Returns:
        bool: True if should continue paragraph
    """
    if not previous_paragraph:
        return False
    
    prev_metadata = previous_paragraph['metadata']
    
    # Check if same page and consecutive paragraphs
    current_page = extract_page_number(current_metadata.get('pages', '0'))
    prev_page = extract_page_number(prev_metadata.get('pages', '0'))
    
    current_para = int(current_metadata.get('para', '0'))
    prev_para = int(prev_metadata.get('para', '0'))
    
    # Continue if same page and consecutive paragraphs
    if current_page == prev_page and current_para == prev_para + 1:
        return True
    
    # Continue if next page and first paragraph (might be continuation)
    if current_page == prev_page + 1 and current_para == 1:
        return True
    
    return False

def should_include_content(section_type, content):
    """
    Determine if content should be included in output.
    
    Args:
        section_type: Type of content section
        content: Document content
        
    Returns:
        bool: True if content should be included
    """
    # Always include headers and paragraphs
    if section_type in ['header', 'paragraph']:
        return True
    
    # Filter out tables and figures that interrupt paragraphs
    if section_type in ['table', 'figure']:
        # Only include if content is substantial and meaningful
        if len(content.strip()) > 50 and not is_purely_tabular(content):
            return True
    
    return False

def is_purely_tabular(content):
    """
    Check if content is purely tabular data without meaningful text.
    
    Args:
        content: Document content
        
    Returns:
        bool: True if content is purely tabular
    """
    # Count different types of content
    lines = content.split('\n')
    pipe_lines = sum(1 for line in lines if '|' in line)
    number_lines = sum(1 for line in lines if re.match(r'^\s*\d+', line))
    text_lines = sum(1 for line in lines if re.match(r'^\s*[A-Za-z]', line))
    
    total_lines = len([line for line in lines if line.strip()])
    
    if total_lines == 0:
        return True
    
    # If more than 70% are tabular lines, consider it purely tabular
    tabular_ratio = (pipe_lines + number_lines) / total_lines
    return tabular_ratio > 0.7

def create_paragraph_section(paragraph_data):
    """
    Create a section from paragraph data.
    
    Args:
        paragraph_data: Dictionary containing paragraph information
        
    Returns:
        dict: Formatted section data
    """
    metadata = paragraph_data['metadata']
    content_parts = paragraph_data['content_parts']
    
    # Join content parts with proper spacing
    content = ' '.join(content_parts)
    
    return {
        'title': clean_section_title(metadata.get('section_title', 'Paragraph')),
        'content': content,
        'page': extract_page_number(metadata.get('pages', '0')),
        'paragraph': metadata.get('para', '0'),
        'content_length': len(content),
        'type': 'paragraph'
    }

def clean_section_title(title):
    """
    Clean section title without merging similar titles.
    
    Args:
        title (str): Original section title
        
    Returns:
        str: Cleaned section title
    """
    if not title or title == 'None':
        return 'Unknown Section'
    
    # Basic cleaning without merging
    title = title.strip()
    
    # Remove extra whitespace
    title = re.sub(r'\s+', ' ', title)
    
    return title

def extract_page_number(pages_str):
    """
    Extract page number from pages string.
    
    Args:
        pages_str: Pages string from metadata
        
    Returns:
        int: Page number
    """
    try:
        if isinstance(pages_str, tuple):
            return int(pages_str[0])
        elif isinstance(pages_str, str):
            numbers = re.findall(r'\d+', pages_str)
            return int(numbers[0]) if numbers else 0
        return 0
    except:
        return 0

def check_grobid_server(grobid_url="http://localhost:8070"):
    """Check if GROBID server is running and accessible."""
    import requests
    try:
        response = requests.get(f"{grobid_url}/api/isalive", timeout=5)
        if response.status_code == 200:
            print("✅ GROBID server is running and accessible")
            return True
        else:
            print(f"❌ GROBID server responded with status code: {response.status_code}")
            return False
    except requests.exceptions.RequestException as e:
        print(f"❌ Cannot connect to GROBID server: {e}")
        return False

if __name__ == "__main__":
    # Define file paths
    pdf_file = "perioperative-care-in-adults-pdf-66142014963397.pdf"
    output_file = "perioperative-care-in-adults-output.txt"
    
    # Check if PDF file exists
    if not os.path.exists(pdf_file):
        print(f"❌ PDF file '{pdf_file}' not found in current directory.")
        exit(1)
    
    print(f"📁 Found PDF file: {pdf_file}")
    
    # Check GROBID server
    if not check_grobid_server():
        print("\n⚠️  Please start GROBID server first.")
        exit(1)
    
    # Extract PDF with sequential processing
    extract_pdf_with_grobid_sequential(pdf_file, output_file)
