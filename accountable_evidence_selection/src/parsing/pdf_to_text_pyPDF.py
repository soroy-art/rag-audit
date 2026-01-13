import PyPDF2
import os

def extract_pdf_to_text(pdf_path, output_path):
    """
    Extract text from a PDF file and save it to a text file.
    
    Args:
        pdf_path (str): Path to the input PDF file
        output_path (str): Path to the output text file
    """
    try:
        # Open the PDF file in binary read mode
        with open(pdf_path, 'rb') as file:
            # Create a PDF reader object
            reader = PyPDF2.PdfReader(file)
            
            # Initialize empty string to store extracted text
            raw_text = ""
            
            # Get total number of pages
            total_pages = len(reader.pages)
            print(f"Total pages in PDF: {total_pages}")
            
            # Iterate through every page and extract text
            for page_num, page in enumerate(reader.pages, 1):
                print(f"Processing page {page_num}/{total_pages}...")
                page_text = page.extract_text()
                raw_text += page_text + "\n\n" + "="*50 + f" PAGE {page_num} " + "="*50 + "\n\n"
            
            # Save the aggregated text to a new file with UTF-8 encoding
            with open(output_path, 'w', encoding='utf-8') as output_file:
                output_file.write(raw_text)
            
            print(f"Text extraction completed successfully!")
            print(f"Output saved to: {output_path}")
            print(f"Total characters extracted: {len(raw_text)}")
            
    except FileNotFoundError:
        print(f"Error: PDF file '{pdf_path}' not found.")
    except Exception as e:
        print(f"Error during PDF processing: {str(e)}")


if __name__ == "__main__":
    # Define file paths
    pdf_file = "EASL-recommendations-on-treatment-of-hepatitis-C.pdf"
    output_file = "raw_guideline.txt"
    
    # Check if PDF file exists
    if os.path.exists(pdf_file):
        print(f"Found PDF file: {pdf_file}")
        extract_pdf_to_text(pdf_file, output_file)
    else:
        print(f"PDF file '{pdf_file}' not found in current directory.")
        print("Available files:")
        for file in os.listdir("."):
            if file.endswith(".pdf"):
                print(f"  - {file}")
