import tiktoken
import os

# --- Configuration ---
# Replace these with your actual file paths for ONE pair
XML_FILE1 = "../adult-care-guideline-output/cdc-guidelines-2022-opiods-for-pain.grobid.tei.xml" 
TXT_FILE1 = "../xml_to_txt_output/cdc-guidelines-2022-opiods-for-pain.txt"
XML_FILE2 = "../adult-care-guideline-output/perioperative-care-in-adults-pdf-66142014963397.grobid.tei.xml"
TXT_FILE2 = "../xml_to_txt_output/perioperative-care-in-adults-pdf-66142014963397_Structured_Context.txt"
XML_FILE3 = "../adult-care-guideline-output/surgery-and-opioids-2021_4.grobid.tei.xml"
TXT_FILE3 = "../xml_to_txt_output/surgery-and-opioids-2021_4.txt"

# Model encoding
ENCODING_MODEL = "o200k_base" 

def count_tokens(text, encoding_name=ENCODING_MODEL):
    try:
        encoding = tiktoken.get_encoding(encoding_name)
        return len(encoding.encode(text))
    except Exception as e:
        print(f"Error: {e}")
        return 0

def calculate_single_pair(xml_path, txt_path):
    print(f"--- Processing Pair ---")
    print(f"XML: {os.path.basename(xml_path)}")
    print(f"TXT: {os.path.basename(txt_path)}")

    # Read XML
    if os.path.exists(xml_path):
        with open(xml_path, 'r', encoding='utf-8') as f:
            xml_text = f.read()
        xml_count = count_tokens(xml_text)
    else:
        print("Error: XML file not found.")
        return

    # Read TXT
    if os.path.exists(txt_path):
        with open(txt_path, 'r', encoding='utf-8') as f:
            txt_text = f.read()
        txt_count = count_tokens(txt_text)
    else:
        print("Error: TXT file not found.")
        return

    # Calculate
    reduction = xml_count - txt_count
    pct = (reduction / xml_count) * 100 if xml_count > 0 else 0

    print(f"XML Tokens: {xml_count}")
    print(f"TXT Tokens: {txt_count}")
    print(f"Reduction:  {reduction} tokens ({pct:.1f}%)")
    print("-" * 30)

if __name__ == "__main__":
    # You can just call this function 3 times with your 3 different pairs
    calculate_single_pair(XML_FILE1, TXT_FILE1)
    calculate_single_pair(XML_FILE2, TXT_FILE2)
    calculate_single_pair(XML_FILE3, TXT_FILE3)