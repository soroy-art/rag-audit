#!/usr/bin/env python3
"""
DOC/DOCX to Structured Format Converter
Converts Word documents to Markdown and XML while preserving structure.
This is much more accurate than PDF conversion for clinical guidelines.
"""

import subprocess
import os
import xml.etree.ElementTree as ET
from pathlib import Path
import argparse
from typing import Dict, List, Tuple

class DocumentConverter:
    def __init__(self, input_path: str, output_dir: str = None):
        self.input_path = input_path
        self.output_dir = output_dir or os.path.dirname(input_path)
        self.base_name = Path(input_path).stem
        
        # Ensure output directory exists
        os.makedirs(self.output_dir, exist_ok=True)
        
    def check_pandoc(self) -> bool:
        """Check if Pandoc is installed and accessible."""
        try:
            result = subprocess.run(['pandoc', '--version'], 
                                  capture_output=True, text=True, timeout=10)
            if result.returncode == 0:
                print(f"✅ Pandoc found: {result.stdout.split()[1]}")
                return True
            else:
                print("❌ Pandoc not found")
                return False
        except (subprocess.TimeoutExpired, FileNotFoundError):
            print("❌ Pandoc not installed or not accessible")
            print("📥 Install with: brew install pandoc")
            return False

    def convert_to_markdown(self, preserve_structure: bool = True) -> str:
        """
        Convert DOC/DOCX to Markdown using Pandoc.
        
        Args:
            preserve_structure: If True, uses advanced Pandoc options for better structure preservation
        """
        output_path = os.path.join(self.output_dir, f"{self.base_name}_structured.md")
        
        print(f"🔄 Converting {self.input_path} to Markdown...")
        
        # Base Pandoc command
        command = [
            'pandoc',
            '-f', 'docx' if self.input_path.endswith('.docx') else 'doc',
            '-t', 'markdown',
            '--wrap=none',  # Prevent line wrapping
            '--extract-media=./media',  # Extract images/media
        ]
        
        if preserve_structure:
            # Advanced options for better structure preservation
            command.extend([
                '--standalone',  # Include document metadata
                '--toc',  # Generate table of contents
                '--toc-depth=3',  # Include up to 3 levels of headings
                '--reference-links',  # Use reference-style links
                '--markdown-headings=atx',  # Use ATX-style headings (##)
                '--preserve-tabs',  # Preserve tab characters
            ])
        
        command.extend([self.input_path, '-o', output_path])
        
        try:
            result = subprocess.run(command, check=True, capture_output=True, text=True)
            print(f"✅ Markdown conversion successful!")
            print(f"📄 Output saved to: {output_path}")
            return output_path
            
        except subprocess.CalledProcessError as e:
            print(f"❌ Error during Pandoc conversion:")
            print(f"   Error: {e.stderr}")
            return None
        except FileNotFoundError:
            print("❌ Pandoc not found. Please install it first.")
            return None

    def convert_to_xml(self) -> str:
        """
        Convert DOC/DOCX to structured XML using Pandoc.
        This creates a more detailed XML structure than Markdown.
        """
        output_path = os.path.join(self.output_dir, f"{self.base_name}_structured.xml")
        
        print(f"🔄 Converting {self.input_path} to XML...")
        
        command = [
            'pandoc',
            '-f', 'docx' if self.input_path.endswith('.docx') else 'doc',
            '-t', 'jats',  # Journal Article Tag Suite - good for academic documents
            '--standalone',
            '--toc',
            '--toc-depth=4',
            self.input_path,
            '-o', output_path
        ]
        
        try:
            result = subprocess.run(command, check=True, capture_output=True, text=True)
            print(f"✅ XML conversion successful!")
            print(f"📄 Output saved to: {output_path}")
            return output_path
            
        except subprocess.CalledProcessError as e:
            print(f"❌ Error during XML conversion:")
            print(f"   Error: {e.stderr}")
            return None

    def convert_to_html(self) -> str:
        """
        Convert DOC/DOCX to HTML with embedded CSS for structure.
        Useful for visual inspection of structure preservation.
        """
        output_path = os.path.join(self.output_dir, f"{self.base_name}_structured.html")
        
        print(f"🔄 Converting {self.input_path} to HTML...")
        
        command = [
            'pandoc',
            '-f', 'docx' if self.input_path.endswith('.docx') else 'doc',
            '-t', 'html5',
            '--standalone',
            '--toc',
            '--toc-depth=4',
            '--css=style.css',  # Reference to CSS file
            '--embed-resources',  # Embed images and CSS
            self.input_path,
            '-o', output_path
        ]
        
        try:
            result = subprocess.run(command, check=True, capture_output=True, text=True)
            print(f"✅ HTML conversion successful!")
            print(f"📄 Output saved to: {output_path}")
            return output_path
            
        except subprocess.CalledProcessError as e:
            print(f"❌ Error during HTML conversion:")
            print(f"   Error: {e.stderr}")
            return None

    def analyze_structure(self, markdown_path: str) -> Dict[str, any]:
        """
        Analyze the structure of the converted Markdown file.
        Returns statistics about headings, lists, and other structural elements.
        """
        if not os.path.exists(markdown_path):
            return {"error": "Markdown file not found"}
        
        with open(markdown_path, 'r', encoding='utf-8') as f:
            content = f.read()
        
        # Count different heading levels
        heading_counts = {}
        for i in range(1, 7):
            pattern = f'^{"#" * i}\\s+'
            count = len([line for line in content.split('\n') if line.strip().startswith('#' * i)])
            if count > 0:
                heading_counts[f'H{i}'] = count
        
        # Count lists
        bullet_lists = len([line for line in content.split('\n') if line.strip().startswith('- ')])
        numbered_lists = len([line for line in content.split('\n') if line.strip().startswith(('1. ', '2. ', '3. '))])
        
        # Count tables
        tables = content.count('|')
        
        # Count links
        links = content.count('[') and content.count('](')
        
        structure_analysis = {
            'total_lines': len(content.split('\n')),
            'total_characters': len(content),
            'heading_counts': heading_counts,
            'bullet_lists': bullet_lists,
            'numbered_lists': numbered_lists,
            'tables': tables,
            'links': links,
            'has_toc': 'Table of Contents' in content or 'Contents' in content
        }
        
        return structure_analysis

    def compare_with_grobid(self, grobid_xml_path: str) -> Dict[str, any]:
        """
        Compare the structure of DOCX conversion with GROBID PDF conversion.
        """
        comparison = {
            'docx_conversion': 'Available',
            'grobid_conversion': 'Available' if os.path.exists(grobid_xml_path) else 'Not found',
            'recommendation': 'Use DOCX conversion for better structure preservation'
        }
        
        if os.path.exists(grobid_xml_path):
            # Parse GROBID XML to count sections
            try:
                tree = ET.parse(grobid_xml_path)
                root = tree.getroot()
                
                # Count GROBID sections
                grobid_sections = len(root.findall('.//{http://www.tei-c.org/ns/1.0}div'))
                comparison['grobid_sections'] = grobid_sections
                
            except ET.ParseError:
                comparison['grobid_parsing'] = 'Failed'
        
        return comparison

def main():
    """Main function to run document conversion."""
    parser = argparse.ArgumentParser(description='Convert DOC/DOCX to structured formats')
    parser.add_argument('input_file', help='Path to the DOC/DOCX file')
    parser.add_argument('--output-dir', help='Output directory (default: same as input)')
    parser.add_argument('--format', choices=['markdown', 'xml', 'html', 'all'], 
                       default='markdown', help='Output format')
    parser.add_argument('--analyze', action='store_true', 
                       help='Analyze structure after conversion')
    
    args = parser.parse_args()
    
    if not os.path.exists(args.input_file):
        print(f"❌ Input file not found: {args.input_file}")
        return
    
    # Initialize converter
    converter = DocumentConverter(args.input_file, args.output_dir)
    
    # Check Pandoc availability
    if not converter.check_pandoc():
        return
    
    print(f"\n🚀 Starting conversion of: {args.input_file}")
    print("=" * 60)
    
    results = {}
    
    # Convert based on requested format
    if args.format in ['markdown', 'all']:
        md_path = converter.convert_to_markdown()
        if md_path:
            results['markdown'] = md_path
            
            if args.analyze:
                print("\n📊 Structure Analysis:")
                analysis = converter.analyze_structure(md_path)
                for key, value in analysis.items():
                    print(f"   {key}: {value}")
    
    if args.format in ['xml', 'all']:
        xml_path = converter.convert_to_xml()
        if xml_path:
            results['xml'] = xml_path
    
    if args.format in ['html', 'all']:
        html_path = converter.convert_to_html()
        if html_path:
            results['html'] = html_path
    
    # Compare with GROBID if available
    grobid_path = "/Users/aristotle_co/Documents/Boussard Lab/Project/grobid_output/EASL-recommendations-on-treatment-of-hepatitis-C.grobid.tei.xml"
    if os.path.exists(grobid_path):
        print("\n🔍 Comparison with GROBID:")
        comparison = converter.compare_with_grobid(grobid_path)
        for key, value in comparison.items():
            print(f"   {key}: {value}")
    
    print(f"\n✅ Conversion complete!")
    print(f"📁 Output directory: {converter.output_dir}")
    print(f"📄 Generated files:")
    for format_type, path in results.items():
        print(f"   - {format_type.upper()}: {path}")

if __name__ == "__main__":
    main()
