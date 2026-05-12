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
    
    months_found = [
        "Feb 25", "Mar 25", "Apr 25", "May 25", "Jun 25", 
        "Jul 25", "Aug 25", "Sep 25", "Oct 25", "Nov 25", 
        "Dec 25", "Jan 26"
    ]
    
    history = []
    for i, unit in enumerate(units_found):
        if i < len(months_found):
            history.append({
                "month": months_found[i],
                "units": unit
            })
            
    return history
