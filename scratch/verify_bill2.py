import sys
import os
sys.path.append(os.getcwd())
import extract_bill
import json

# Mock get_ocr_lines to use b2_loose.txt
def mock_get_ocr_lines(image_path):
    with open("b2_loose.txt", "r", encoding="utf-8") as f:
        return [line.strip() for line in f if line.strip()]

extract_bill.get_ocr_lines = mock_get_ocr_lines

# Also mock initialize_ocr and monthly history to avoid errors
extract_bill.initialize_ocr = lambda: "paddle"
extract_bill.extract_monthly_history = lambda x: []

data = extract_bill.extract_bill_data("assets/bill2.jpeg")

print("\n========== VERIFICATION RESULT ==========\n")
print(json.dumps(data, indent=4))

expected = {
    "consumer_number": "439320095567",
    "consumer_name": "SHRI MADHUSHAM ROOPCHAND KHOBRAGADE",
    "meter_number": "08201154836",
    "load_kw": "3.30", # Reverted to 3.30 as per image
    "bill_date": "10-09-2004",
    "due_date": "05-01-2026",
    "bill_amount": "3490.00",
    "late_amount": "1460.00",
    "fixed_charges": "130"
}

for key, val in expected.items():
    actual = data.get(key)
    if actual == val:
        print(f"PASS {key}: {actual}")
    else:
        print(f"FAIL {key}: Expected '{val}', got '{actual}'")
