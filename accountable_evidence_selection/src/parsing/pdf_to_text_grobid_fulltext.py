import os
import shutil
import tempfile
from grobid_client.grobid_client import GrobidClient

# --- Configuration ---
# The PDF file you want to process (can be relative or absolute path)
PDF_FILE_PATH = "/Users/aristotle_co/Documents/Boussard Lab/Project/adult-care-guidelines/2014DeliriumGuidelineEvidence.pdf"
# The service endpoint for full-text structuring
SERVICE_NAME = "processFulltextDocument" 
# The directory to save the structured output
OUTPUT_DIRECTORY = "/Users/aristotle_co/Documents/Boussard Lab/Project/adult-care-guideline-output"

def process_single_pdf_to_xml(pdf_path, output_dir):
    """
    Processes a single PDF file using GROBID's fulltext service and outputs XML.
    
    Args:
        pdf_path (str): Full path to the PDF file to process
        output_dir (str): Directory where the XML output should be saved
    """
    print("Starting GROBID processing...")
    
    # 1. Validate input file
    if not os.path.exists(pdf_path):
        print(f"❌ Error: PDF file not found: {pdf_path}")
        return None
    
    if not pdf_path.lower().endswith('.pdf'):
        print(f"❌ Error: File is not a PDF: {pdf_path}")
        return None
    
    # 2. Ensure the output directory exists
    if not os.path.exists(output_dir):
        os.makedirs(output_dir)
    
    # 3. Initialize the GROBID client
    try:
        client = GrobidClient(config_path=None) 
    except Exception as e:
        print(f"❌ Error initializing GrobidClient. Ensure the server is running on http://localhost:8070.")
        print(f"   Details: {e}")
        return None
    
    # 4. Create a temporary directory with only the PDF file we want to process
    # This ensures GROBID only processes the specific file
    temp_dir = None
    pdf_filename = os.path.basename(pdf_path)
    expected_xml_filename = pdf_filename.replace('.pdf', '.grobid.tei.xml')
    final_output_path = os.path.join(output_dir, expected_xml_filename)
    
    try:
        temp_dir = tempfile.mkdtemp(prefix="grobid_single_file_")
        temp_pdf_path = os.path.join(temp_dir, pdf_filename)
        
        print(f"📄 Processing: {pdf_path}")
        print(f"📋 Creating temporary directory for single-file processing...")
        shutil.copy2(pdf_path, temp_pdf_path)
        
        # 5. Process the document from the temporary directory
        print(f"🔄 Processing PDF with GROBID fulltext service...")
        client.process(
            service=SERVICE_NAME,
            input_path=temp_dir,  # Temporary directory with only our PDF
            output=output_dir,
            n=1,  # Number of concurrent threads
            force=True,  # Overwrite existing files
            consolidate_header=True,  # Attempt to resolve and clean up header metadata
            verbose=True  # More detailed processing information
        )
        
        # 6. Find the output XML file
        # GROBID might create it in a subdirectory, so we need to search for it
        actual_output = None
        for root, dirs, files in os.walk(output_dir):
            for file in files:
                if file == expected_xml_filename:
                    actual_output = os.path.join(root, file)
                    break
            if actual_output:
                break
        
        if actual_output:
            # If the file is in a subdirectory, move it to the root of output_dir
            if actual_output != final_output_path:
                print(f"📦 Moving output from subdirectory to main output directory...")
                shutil.move(actual_output, final_output_path)
                
                # Try to remove empty subdirectories
                try:
                    subdir = os.path.dirname(actual_output)
                    if subdir != output_dir and os.path.exists(subdir):
                        if not os.listdir(subdir):
                            os.rmdir(subdir)
                            print(f"🧹 Removed empty subdirectory: {subdir}")
                except:
                    pass  # Directory not empty or doesn't exist
            
            print(f"\n✅ Processing complete!")
            print(f"📄 XML output saved to: {final_output_path}")
            return final_output_path
        else:
            # Check if there are any error files or other outputs
            print(f"\n⚠️  XML output file not found at expected location.")
            print(f"   Expected: {expected_xml_filename}")
            print(f"   Searching for any output files...")
            
            # List all files in output directory
            for root, dirs, files in os.walk(output_dir):
                for file in files:
                    if file.endswith('.xml') or file.endswith('.tei.xml'):
                        print(f"   Found: {os.path.join(root, file)}")
                    elif file.endswith('.txt'):
                        print(f"   Found (possibly error): {os.path.join(root, file)}")
            
            return None
        
    except Exception as e:
        print(f"❌ Error during processing: {e}")
        return None
        
    finally:
        # 7. Clean up temporary directory
        if temp_dir and os.path.exists(temp_dir):
            print(f"🧹 Cleaning up temporary directory...")
            shutil.rmtree(temp_dir)

if __name__ == "__main__":
    result = process_single_pdf_to_xml(PDF_FILE_PATH, OUTPUT_DIRECTORY)
    
    if result:
        print("\n✅ Success! You can now use an XML parsing library (like ElementTree or BeautifulSoup)")
        print("   to extract the text and formatting from the XML file.")
    else:
        print("\n❌ Processing failed. Please check the error messages above.")
