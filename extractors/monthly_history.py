import cv2
import pytesseract
import re
from preprocess import preprocess_for_ocr

def extract_history(image_crop, ocr_engine=None, ocr_type=None):
    """
    Extracts monthly units from the graph region.
    """
    if image_crop is None:
        return []
        
    preprocessed = preprocess_for_ocr(image_crop)
    
    # OCR
    history_text = ""
    if ocr_type == "paddle" and ocr_engine:
        try:
            result = ocr_engine.ocr(preprocessed)
            if result and result[0]:
                history_text = "\n".join([line[1][0] for line in result[0]])
        except:
            pass
            
    if not history_text:
        try:
            from PIL import Image
            pil_img = Image.fromarray(preprocessed)
            config = r'--oem 3 --psm 6'
            history_text = pytesseract.image_to_string(pil_img, lang="eng+mar", config=config)
        except Exception as e:
            print(f"OCR failed for history: {e}")
            return []
    
    lines = history_text.splitlines()
    units_found = []
    
    for line in lines:
        numbers = re.findall(r'\d+', line)
        for n in numbers:
            value = int(n)
            if 0 < value <= 500:
                units_found.append(value)
                
    # Keep last 12 values
    units_found = units_found[-12:]
    
    # Dynamic month calculation fallback
    from datetime import datetime, timedelta
    current_date = datetime.now()
    months_found = []
    for i in range(12, 0, -1):
        d = current_date - timedelta(days=30 * i)
        months_found.append(d.strftime("%B %Y"))
    
    # If OCR found months, use them (simplified regex)
    ocr_months = re.findall(r'(?:Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct|Nov|Dec)[a-z]*\s*\d{2,4}', history_text)
    if len(ocr_months) >= 6:
        # Format the OCR months nicely
        months_found = ocr_months[-12:]

    history = []
    for i, unit in enumerate(units_found):
        m_label = months_found[i] if i < len(months_found) else "Unknown"
        history.append({
            "month": m_label,
            "units": unit
        })
            
    return history

