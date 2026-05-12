import os
import cv2
import numpy as np
from ensemble_extractor import extract_with_ensemble
from validations import clean_data, validate_units, validate_amounts, validate_consumer_number

def extract_bill_data(image_path, mistral_api_key=None, groq_api_key=None):
    """
    Orchestrates the bill extraction using the Mistral + Llama Ensemble method.
    Bypasses legacy regional OCR for maximum accuracy.
    """
    print(f"--- Starting Ensemble AI Extraction for {image_path} ---")
    
    # 1. AI Ensemble Extraction
    data = extract_with_ensemble(image_path, mistral_key=mistral_api_key, groq_key=groq_api_key)
    
    if "error" in data:
        return data

    # 2. Final Processing & Validation
    data = clean_data(data)
    
    # Add validation flags
    data["valid_units"] = validate_units(data.get("current_reading"), data.get("previous_reading"), data.get("units"))
    data["valid_amounts"] = validate_amounts(data.get("bill_amount"), data.get("late_amount"))
    data["valid_consumer"] = validate_consumer_number(data.get("consumer_number"))
    
    # Default fallback for fixed charges if missing
    if not data.get("fixed_charges"):
        data["fixed_charges"] = "130"
    
    # ── PRINT RESULT ──────────────────────────────────────
    print("\n========== ENSEMBLE EXTRACTED DATA ==========\n")
    for k, v in data.items():
        if k != "monthly_history":
            print(f"{k}: {v}")
    print(f"monthly_history: {len(data.get('monthly_history', []))} items")
    print("────────────────────────────────────────────\n")
    
    return data