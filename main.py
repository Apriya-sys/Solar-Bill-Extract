import os
from extract_bill import extract_bill_data
from fill_excel import fill_excel_multi

# ─────────────────────────────────────────────
# Add all bill image paths here
# ─────────────────────────────────────────────
bill_images = [
    "assets/bill1.jpeg",
    "assets/bill2.jpeg",
]

all_data = []

for image_path in bill_images:

    if not os.path.exists(image_path):
        print(f"\n[SKIP] File not found: {image_path}")
        continue

    print(f"\n{'='*50}")
    print(f"Processing: {image_path}")
    print(f"{'='*50}")

    data = extract_bill_data(image_path)
    all_data.append(data)

# Save all bills into one Excel sheet
if all_data:
    fill_excel_multi(all_data)
    print("\n✅ Task Completed Successfully")
else:
    print("\n⚠️ No bills processed.")