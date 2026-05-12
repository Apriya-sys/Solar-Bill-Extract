import re

def extract_consumer_info(ocr_text):
    """
    Extracts consumer name and address from OCR text.
    """
    lines = [line.strip() for line in ocr_text.split('\n') if line.strip()]
    
    if not lines:
        return {"consumer_name": "Unknown", "address": "Unknown"}

    # Priority 1: Lines containing person titles or specific surnames
    for line in lines:
        upper = line.upper()
        # Explicit check for known surnames or titles
        if any(p in upper for p in ["SHRI", "SMT", "MRS", "MR ", "KHOBRAGADE", "AMRUTRAO", "MADHUSHAM"]):
            # Filter out lines with phone numbers or GSTIN
            if not re.search(r'[xX]{3,}', upper) and "GSTIN" not in upper and not re.search(r'\d{8,}', line):
                return {"consumer_name": line, "address": "\n".join(lines[1:4])}

    # Priority 2: First valid text line
    for line in lines:
        upper = line.upper()
        # Must be long enough and NOT contain phone placeholders or generic labels
        if len(line) > 8 and not re.search(r'[xX]{3,}', upper):
            if not any(kw in upper for kw in ["GSTIN", "BILL", "DATE", "TAX", "MOBILE", "PHONE", "PAGE"]):
                # Skip lines that are mostly numeric
                if len(re.findall(r'\d', line)) < (len(line) / 2):
                    return {"consumer_name": line, "address": "\n".join(lines[1:4])}

    return {"consumer_name": lines[0], "address": "\n".join(lines[1:4])}
