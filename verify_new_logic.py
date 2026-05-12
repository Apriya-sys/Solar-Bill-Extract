import cv2
from extract_bill import extract_bill_data, initialize_ocr
from crops import get_crop
import os

def test_extraction(image_path):
    print(f"\n--- Testing {image_path} ---")
    if not os.path.exists(image_path):
        print(f"Error: {image_path} not found")
        return
        
    image = cv2.imread(image_path)
    os.makedirs("debug_crops", exist_ok=True)
    
    for region in ["consumer", "bill_details", "meter_info", "readings", "monthly_history"]:

        crop = get_crop(image, region)
        if crop is not None:
            cv2.imwrite(f"debug_crops/{os.path.basename(image_path)}_{region}.jpg", crop)
            
    data = extract_bill_data(image_path)
    print("\nResult Data:")
    for key, value in data.items():
        if key != "monthly_history":
            print(f"  {key}: {value}")
        else:
            print(f"  monthly_history: {len(value)} items")


if __name__ == "__main__":
    test_extraction("bill1.jpeg")
    test_extraction("bill2.jpeg")
