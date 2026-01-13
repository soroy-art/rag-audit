import os
from lxml import etree as ET

# --- Configuration ---
INPUT_XML_FILE = "data/grobid_xml/adult_care/surgery-and-opioids-2021_4.grobid.tei.xml"
OUTPUT_TEXT_FILE = "data/pseudo_xml/surgery-and-opioids-2021_4.txt"
TEI_NAMESPACE = {'tei': 'http://www.tei-c.org/ns/1.0'}

# List of tags to REMOVE completely (content and all)
TAGS_TO_REMOVE = [
    '{http://www.tei-c.org/ns/1.0}biblStruct',  # The bibliography entries
    '{http://www.tei-c.org/ns/1.0}note',        # Often noise/footnotes
    '{http://www.tei-c.org/ns/1.0}ref'          # Cross-references (optional to remove)
]

def extract_clean_pseudo_xml(xml_path):
    if not os.path.exists(xml_path): return "Error: File not found."
    
    parser = ET.XMLParser(recover=True)
    tree = ET.parse(xml_path, parser)
    root = tree.getroot()

    # --- STEP 1: Pruning the Tree (Removing Noise) ---
    # We iterate through the tree and remove the specific tags we don't want.
    # We use a while loop to modify the tree in place safely.
    
    for tag_name in TAGS_TO_REMOVE:
        # Find all instances of the tag
        elements = root.findall(f".//{tag_name}")
        for element in elements:
            # Get the parent to remove the child
            parent = element.getparent()
            if parent is not None:
                parent.remove(element)
    
    print(f"Removed {len(TAGS_TO_REMOVE)} types of noisy tags from the tree.")

    # --- STEP 2: Extracting the Remaining Structure ---
    structured_content = []
    
    # 1. Get Title
    title = root.find('.//tei:titleStmt/tei:title', namespaces=TEI_NAMESPACE)
    if title is not None and title.text:
        structured_content.append(f"<docTitle>{title.text.strip()}</docTitle>\n")
        
    # 2. Iterate through Body (now cleaned of bibliographies)
    body = root.find('.//tei:body', namespaces=TEI_NAMESPACE)
    if body is not None:
        for element in body.iterdescendants():
            tag_name = ET.QName(element).localname
            text = (element.text or "").strip()
            
            if not text: continue

            # Keep the XML tag structure explicitly in the text output
            if tag_name == 'head':
                structured_content.append(f"\n<sectionHeader>{text}</sectionHeader>\n")
            elif tag_name == 'p':
                structured_content.append(f"<paragraph>{text}</paragraph>\n")
            elif tag_name == 'item':
                structured_content.append(f"<recommendationItem>{text}</recommendationItem>\n")
            elif tag_name == 'row': 
                 structured_content.append(f"<tableRow>{text}</tableRow>\n")
            # Note: Bibliographies are already gone, so we don't need to filter them here.

    return "".join(structured_content)

def save_file(content, output_path):
    try:
        with open(output_path, 'w', encoding='utf-8') as f:
            f.write(content)
        print(f"✅ Saved cleaned pseudo-XML to: {output_path}")
    except Exception as e:
        print(f"Error saving file: {e}")

if __name__ == "__main__":
    # Update this path to where your XML file lives
    xml_input_path = os.path.join(os.getcwd(), INPUT_XML_FILE) 
    final_content = extract_clean_pseudo_xml(xml_input_path)
    if final_content and not final_content.startswith("Error:"):
        save_file(final_content, OUTPUT_TEXT_FILE)
    else:
        print(final_content)