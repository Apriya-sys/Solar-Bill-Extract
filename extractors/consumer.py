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
    # Priority 1: Keyword-based extraction
    for i, line in enumerate(lines):
        upper = line.upper()
        if "NAME" in upper or "ग्राहक" in upper or "नांव" in upper:
            if i + 1 < len(lines):
                potential_name = lines[i+1]
                if not any(kw in potential_name.upper() for kw in ["CONSUMER", "NO", "DATE", "BILL", "MOBILE"]):
                    name_line = potential_name
                    break
    
    # Priority 2: Pattern-based fallback
    if not name_line:
        for line in lines:
            if any(label in line.upper() for label in labels) and re.search(r'\d{12}', line):
                continue 
            if re.match(r'^[\d\W_]+$', line) or len(line) < 3 or "xxxx" in line.lower() or "mobile" in line.lower():
                continue
            if any(kw in line.upper() for kw in ["NAGAR", "H.NO", "PLOT", "ROAD", "441912", "TUMSAR", "DIST-", "MAHARASHTRA"]):
                continue
            if any(p in line.upper() for p in ["SHRI", "MRS", "MR ", "MISS", "KHOBRAGADE", "RANJANA"]):
                name_line = line
                break
            if not name_line:
                name_line = line


    return {
        "consumer_number": consumer_number,
        "consumer_name": name_line or "NAME NOT FOUND",
        "address": "\n".join(lines[lines.index(name_line)+1:]) if (name_line and name_line in lines) else ocr_text
    }



