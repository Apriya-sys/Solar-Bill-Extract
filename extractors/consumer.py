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
    
    for line in lines:
        upper = line.upper()
        if any(label in upper for label in labels) and re.search(r'\d{12}', line):
            continue # This is the consumer number line
            
        if not consumer_name:
            # Check if it looks like a name
            # Names usually have more letters than numbers
            letters = sum(c.isalpha() for c in line)
            digits = sum(c.isdigit() for c in line)
            
            # Common prefixes for MSEDCL names
            prefixes = ["SHRI", "SMT", "MRS", "MR", "M/S", "DR", "KU"]
            is_prefixed = any(upper.startswith(p) for p in prefixes)
            
            if (letters > 10 and digits < 10) or is_prefixed:
                consumer_name = line
        else:
            # Following lines are address
            if len(address_lines) < 3:
                address_lines.append(line)

            
    return {
        "consumer_number": consumer_number,
        "consumer_name": consumer_name,
        "address": " ".join(address_lines)
    }

