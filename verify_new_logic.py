import os
from extract_bill import extract_bill_data, initialize_ocr

def test_extraction(image_path):
    print(f"\n--- Testing {image_path} ---")
    if not os.path.exists(image_path):
        print(f"File {image_path} not found.")
        return

    try:
        data = extract_bill_data(image_path)
        
        print("\nResult Data:")
        for key, value in data.items():
            try:
                if key == "monthly_history":
                    print(f"  {key}: {len(value)} items")
                else:
                    print(f"  {key}: {value}")
            except:
                print(f"  {key}: [Encoding Error]")
    except Exception as e:
        print(f"Error processing {image_path}: {e}")

if __name__ == "__main__":
    # Initialize OCR once
    initialize_ocr()
    
    test_extraction("bill1.jpeg")
    test_extraction("bill2.jpeg")
