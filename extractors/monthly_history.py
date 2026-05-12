import cv2
import re
from preprocess import preprocess_for_ocr

def extract_history(image_crop, ocr_engine=None, ocr_type=None, full_text=None):
    """
    Extracts monthly units from the graph region, with an optional full_text fallback.
    """
    if image_crop is None and not full_text:
        return []
        
    items = []
    if image_crop is not None:
        preprocessed = preprocess_for_ocr(image_crop)
        if ocr_type == "paddle" and ocr_engine:
            try:
                result = ocr_engine.ocr(preprocessed)
                if result and result[0]:
                    items = sorted(result[0], key=lambda x: (x[0][0][1], x[0][0][0]))
            except: pass
            
    # If no items found from crop, try regex on full text
    if not items and full_text:
        return regex_history_search(full_text)

    marathi_to_eng = {
        "जानेवारी": "January", "फेब्रुवारी": "February", "मार्च": "March",
        "एप्रिल": "April", "मे": "May", "जून": "June",
        "जुलै": "July", "ऑगस्ट": "August", "सप्टेंबर": "September",
        "ऑक्टोबर": "October", "नोव्हेंबर": "November", "डिसेंबर": "December",
        "JAN": "January", "FEB": "February", "MAR": "March", "APR": "April",
        "MAY": "May", "JUN": "June", "JUL": "July", "AUG": "August",
        "SEP": "September", "OCT": "October", "NOV": "November", "DEC": "December"
    }
    
    extracted_pairs = []
    for i, item in enumerate(items):
        text = item[1][0].strip().upper()
        
        found_month = None
        for m_key, m_val in marathi_to_eng.items():
            if m_key in text:
                found_month = m_val
                break
        
        if found_month:
            # Look for adjacent number
            current_y = item[0][0][1]
            for j in range(i + 1, min(i + 5, len(items))):
                other_text = items[j][1][0].strip()
                other_y = items[j][0][0][1]
                if re.match(r'^\d+$', other_text) and abs(other_y - current_y) < 50:
                    extracted_pairs.append({"month": found_month, "units": int(other_text)})
                    break

    return extracted_pairs

def regex_history_search(text):
    """Search for month-unit patterns in raw text."""
    results = []
    months = ["JAN", "FEB", "MAR", "APR", "MAY", "JUN", "JUL", "AUG", "SEP", "OCT", "NOV", "DEC"]
    for m in months:
        # Match "JAN 250" or "JAN-250" or "JAN:250"
        match = re.search(rf'{m}[^0-9]*(\d{{1,4}})', text.upper())
        if match:
            results.append({"month": m, "units": int(match.group(1))})
    return results
