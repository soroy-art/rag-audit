#!/usr/bin/env python3
"""
Raw GROBID LangChain Output - No Custom Formatting
This script shows the raw output from LangChain's GrobidParser without any custom processing.
"""

import os
import json
from langchain_community.document_loaders.generic import GenericLoader
from langchain_community.document_loaders.parsers import GrobidParser

def extract_pdf_raw_langchain(pdf_path, output_path, grobid_url="http://localhost:8070"):
    """
    Extract text from PDF using GROBID with LangChain - RAW OUTPUT ONLY.
    Shows what LangChain's GrobidParser actually returns without custom formatting.
    
    Args:
        pdf_path (str): Path to the input PDF file
        output_path (str): Path to the output text file
        grobid_url (str): URL of the GROBID server
    """
    try:
        print(f"Starting raw GROBID extraction for: {pdf_path}")
        print(f"GROBID server URL: {grobid_url}")
        
        # Create GROBID parser with sentence segmentation enabled
        parser = GrobidParser(segment_sentences=True)
        
        # Create loader for the PDF file
        loader = GenericLoader.from_filesystem(
            os.path.dirname(pdf_path),
            glob=os.path.basename(pdf_path),
            suffixes=[".pdf"],
            parser=parser,
        )
        
        # Load documents - this returns Document objects
        print("Processing PDF with GROBID...")
        docs = loader.load()
        
        if not docs:
            print("No documents were extracted.")
            return
        
        print(f"Successfully extracted {len(docs)} document sections")
        print(f"\n📊 Raw Document Structure:")
        print(f"   - Type: {type(docs[0])}")
        print(f"   - Has 'page_content': {hasattr(docs[0], 'page_content')}")
        print(f"   - Has 'metadata': {hasattr(docs[0], 'metadata')}")
        
        # Output raw content - just dump what LangChain gives us
        with open(output_path, 'w', encoding='utf-8') as output_file:
            output_file.write("=" * 80 + "\n")
            output_file.write("RAW LANGCHAIN GROBID OUTPUT (No Custom Formatting)\n")
            output_file.write("=" * 80 + "\n\n")
            
            for i, doc in enumerate(docs):
                output_file.write(f"\n{'='*80}\n")
                output_file.write(f"DOCUMENT {i+1} of {len(docs)}\n")
                output_file.write(f"{'='*80}\n\n")
                
                # Write the page content (text)
                output_file.write("CONTENT:\n")
                output_file.write("-" * 80 + "\n")
                output_file.write(doc.page_content)
                output_file.write("\n\n")
                
                # Write the metadata
                output_file.write("METADATA:\n")
                output_file.write("-" * 80 + "\n")
                output_file.write(json.dumps(doc.metadata, indent=2))
                output_file.write("\n\n")
        
        # Also create a JSON file with all documents for easier inspection
        json_output_path = output_path.replace('.txt', '_raw.json')
        with open(json_output_path, 'w', encoding='utf-8') as json_file:
            json_data = []
            for doc in docs:
                json_data.append({
                    'page_content': doc.page_content,
                    'metadata': doc.metadata
                })
            json.dump(json_data, json_file, indent=2, ensure_ascii=False)
        
        print(f"\n✅ Raw extraction completed!")
        print(f"📄 Text output saved to: {output_path}")
        print(f"📄 JSON output saved to: {json_output_path}")
        print(f"📈 Total documents: {len(docs)}")
        print(f"\n💡 Note: LangChain's GrobidParser returns TEXT (not XML).")
        print(f"   It internally calls GROBID, parses the XML, and extracts text content.")

    except Exception as e:
        print(f"❌ Error during GROBID processing: {str(e)}")
        import traceback
        traceback.print_exc()

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
    pdf_file = "clinical guideline/EASL-recommendations-on-treatment-of-hepatitis-C.pdf"
    output_file = "grobid_langchain_raw_output.txt"
    
    # Check if PDF file exists
    if not os.path.exists(pdf_file):
        print(f"❌ PDF file '{pdf_file}' not found in current directory.")
        exit(1)
    
    print(f"📁 Found PDF file: {pdf_file}")
    
    # Check GROBID server
    if not check_grobid_server():
        print("\n⚠️  Please start GROBID server first.")
        exit(1)
    
    # Extract PDF with raw output
    extract_pdf_raw_langchain(pdf_file, output_file)

