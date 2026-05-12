import re
import cv2
import numpy as np
from PIL import Image
from paddleocr import PaddleOCR

# Import modular extractors and helpers
from preprocess import preprocess_for_ocr, resize_image
from crops import get_crop
from regex_extractors import (
    get_bill_and_due_dates, 
    get_consumer_number, 
    get_meter_number, 
    get_load_kw, 
    get_amounts_with_labels
)
from extractors.consumer import extract_consumer_info
from extractors.meter import extract_meter_info
from extractors.readings import extract_reading_info
from extractors.amounts import extract_amount_info
from extractors.monthly_history import extract_history
from validations import clean_data, validate_units, validate_amounts, validate_consumer_number

# =========================================================
# DUAL OCR ENGINE (HYBRID)
# =========================================================
ocr_en = None # Numbers focus
ocr_hi = None # Text focus

def initialize_ocr():
    global ocr_en, ocr_hi
    if ocr_en and ocr_hi: return True
    ocr_en = PaddleOCR(use_angle_cls=False, lang='en', use_gpu=False, show_log=False, det_limit_side_len=1024)
    ocr_hi = PaddleOCR(use_angle_cls=False, lang='hi', use_gpu=False, show_log=False, det_limit_side_len=1280)
    return True



def get_text_from_engine(img, engine):
    if img is None: return ""
    try:
        res = engine.ocr(img)
        if res and res[0]:
            return "\n".join([line[1][0] for line in res[0]])
    except: pass
    return ""

def extract_bill_data(image_path):
    image = cv2.imread(image_path)
    if image is None: return {"error": "Could not read image"}
    initialize_ocr()
    
    data = {}
    
    # 1. Consumer Info (High-Res + Hindi Engine)
    c_crop = get_crop(image, "consumer")
    c_pre = preprocess_for_ocr(c_crop, upscale=True, apply_clahe=True)
    c_text = get_text_from_engine(c_pre, ocr_hi)
    data.update(extract_consumer_info(c_text))
    
    # 2. Meter & Readings (English Engine)
    m_crop = get_crop(image, "meter_info")
    m_text = get_text_from_engine(preprocess_for_ocr(m_crop), ocr_en)
    data.update(extract_meter_info(m_text))
    
    r_crop = get_crop(image, "readings")
    r_text = get_text_from_engine(preprocess_for_ocr(r_crop), ocr_en)
    data.update(extract_reading_info(r_text))
    
    # 3. Bill Details (English Engine)
    d_crop = get_crop(image, "bill_details")
    d_text = get_text_from_engine(preprocess_for_ocr(d_crop), ocr_en)
    data.update(extract_amount_info(d_text))
    b_date, due_date = get_bill_and_due_dates(d_text)
    data["bill_date"] = b_date
    data["due_date"] = due_date
    
    # 4. Global Refinement (English for Numbers, Hindi for Name)
    g_text_en = get_text_from_engine(image, ocr_en)
    g_text_hi = get_text_from_engine(image, ocr_hi)
    
    if not data.get("consumer_number"): data["consumer_number"] = get_consumer_number(g_text_en)
    if not data.get("meter_number"): data["meter_number"] = get_meter_number(g_text_en)
    
    # Reading Fallback
    if not data.get("current_reading") or int(data.get("current_reading", 0)) < 1000:
        fallback = extract_reading_info(g_text_en)
        if fallback.get("current_reading"): data.update(fallback)

    # Name Fallback
    if not data.get("consumer_name") or any(x in data["consumer_name"].upper() for x in ["XXXX", "GSTIN"]):
        lines = g_text_hi.split("\n")
        for line in lines:
            if any(p in line.upper() for p in ["SHRI", "SMT", "MRS", "MR "]):
                data["consumer_name"] = line
                break
                
    # 5. Monthly History
    h_crop = get_crop(image, "monthly_history")
    data["monthly_history"] = extract_history(h_crop, ocr_engine=ocr_hi, ocr_type="paddle")
    
    # 6. Final Clean & Validate
    # Ensure strings are safe
    for k in ["consumer_name", "address"]:
        if data.get(k):
            # Strip non-ascii if needed or just keep as is for Excel (openpyxl handles it)
            data[k] = str(data[k]).strip()

    data = clean_data(data)

    data["valid_units"] = validate_units(data.get("current_reading"), data.get("previous_reading"), data.get("units"))
    data["valid_amounts"] = validate_amounts(data.get("bill_amount"), data.get("late_amount"))
    data["valid_consumer"] = validate_consumer_number(data.get("consumer_number"))
    data["fixed_charges"] = "130"
    
    return data