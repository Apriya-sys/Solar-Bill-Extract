import pandas as pd
import os
from datetime import datetime


COLUMNS = [
    "consumer_number",
    "consumer_name",
    "address",
    "meter_number",
    "load_kw",
    "tariff",
    "bill_date",
    "due_date",
    "current_reading",
    "previous_reading",
    "units",
    "bill_amount",
    "late_amount",
]


def fill_excel(data):
    """Save a single bill to its own Excel file."""
    os.makedirs("outputs", exist_ok=True)

    df = pd.DataFrame([data], columns=COLUMNS)

    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    output_file = f"outputs/{data.get('consumer_number', 'bill')}_{timestamp}.xlsx"

    df.to_excel(output_file, index=False)

    print(f"\n✅ Excel saved: {output_file}")
    return output_file


def fill_excel_multi(data_list):
    """Save multiple bills into a single Excel file (one row per bill)."""
    os.makedirs("outputs", exist_ok=True)

    df = pd.DataFrame(data_list, columns=COLUMNS)

    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    output_file = f"outputs/all_bills_{timestamp}.xlsx"

    # Auto-size columns for readability
    with pd.ExcelWriter(output_file, engine="openpyxl") as writer:
        df.to_excel(writer, index=False, sheet_name="Bills")

        ws = writer.sheets["Bills"]

        for col in ws.columns:
            max_len = max(
                len(str(cell.value)) if cell.value else 0
                for cell in col
            )
            ws.column_dimensions[col[0].column_letter].width = max_len + 4

    print(f"\n✅ Combined Excel saved: {output_file}")
    print(f"   Total bills saved: {len(data_list)}")

    # Also print a clean summary to console
    print("\n" + "=" * 55)
    print("  EXTRACTED BILL SUMMARY")
    print("=" * 55)

    for i, data in enumerate(data_list, 1):
        print(f"\n--- Bill {i} ---")
        for key in COLUMNS:
            print(f"  {key}: {data.get(key, '')}")

    return output_file