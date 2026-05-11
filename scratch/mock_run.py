import sys
import os
sys.path.append(os.getcwd())
import extract_bill
from fill_excel import fill_excel_multi
import json

# Mock get_ocr_lines to use saved text files
def mock_get_ocr_lines(image_path):
    if "bill2" in image_path:
        filename = "b2_loose.txt"
    else:
        filename = "b1_ocr.txt"
        
    if os.path.exists(filename):
        with open(filename, "r", encoding="utf-8") as f:
            return [line.strip() for line in f if line.strip()]
    return []

# Mock other blocking functions
extract_bill.get_ocr_lines = mock_get_ocr_lines
extract_bill.initialize_ocr = lambda: "paddle"
extract_bill.extract_monthly_history = lambda x: [
    {"month": "February 2025", "units": 99},
    {"month": "March 2025", "units": 151},
    {"month": "April 2025", "units": 258},
    {"month": "May 2025", "units": 208},
    {"month": "June 2025", "units": 262},
    {"month": "July 2025", "units": 96},
    {"month": "August 2025", "units": 86},
    {"month": "September 2025", "units": 157},
    {"month": "October 2025", "units": 380},
    {"month": "November 2025", "units": 146},
    {"month": "December 2025", "units": 121},
    {"month": "January 2026", "units": 25},
]

bill_images = ["assets/bill1.jpeg", "assets/bill2.jpeg"]
all_data = []

for image_path in bill_images:
    print(f"Processing mock data for: {image_path}")
    data = extract_bill.extract_bill_data(image_path)
    all_data.append(data)

if all_data:
    output_file = fill_excel_multi(all_data)
    print(f"\nMock run completed. Excel generated: {output_file}")
    
    # Show data for bill2
    print("\n========== FINAL DATA FOR BILL 2 ==========\n")
    print(json.dumps(all_data[1], indent=4))
