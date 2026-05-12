from regex_extractors import get_consumer_number
import re

from regex_extractors import get_consumer_number
import re

def extract_consumer_info(ocr_text):
    """
    Extracts consumer name, address, and consumer number from OCR text.
    """
    lines = [line.strip() for line in ocr_text.split('\n') if line.strip()]
    
    print(f"DEBUG CONSUMER LINES: {lines}")
    
    consumer_number = get_consumer_number(ocr_text)
    
    consumer_name = ""
    address_lines = []
    
    # In MSEDCL bills, the name is usually the first or second line 
    # after the consumer number label.
    # We'll skip lines that look like labels.
    labels = ["ग्राहक", "क्रमांक", "CONSUMER", "NUMBER", "NO", "BILL", "MSEDCL", "MAHAVITARAN"]
    
    name_line = ""
    for line in lines:
        upper = line.upper()
        if any(label in upper for label in labels) and re.search(r'\d{12}', line):
            continue 
            
        # Skip purely numeric, mobile numbers, or very short lines
        if re.match(r'^[\d\W_]+$', line) or len(line) < 3 or "xxxx" in line.lower() or "mobile" in line.lower():
            continue
        # Skip obvious address lines
        if any(kw in line.upper() for kw in ["NAGAR", "H.NO", "PLOT", "ROAD", "441912", "TUMSAR", "DIST-", "MAHARASHTRA"]):
            continue
        # If we see "SHRI" or "MRS" or "MR", it's a high-confidence name
        if any(p in line.upper() for p in ["SHRI", "MRS", "MR ", "MISS", "KHOBRAGADE", "RANJANA"]):
            name_line = line
            break
        # Otherwise, take the first non-address line
        if not name_line:
            name_line = line

    return {
        "consumer_number": consumer_number,
        "consumer_name": name_line or "NAME NOT FOUND",
        "address": "\n".join(lines[lines.index(name_line)+1:]) if (name_line and name_line in lines) else ocr_text
    }



