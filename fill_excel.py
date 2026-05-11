import pandas as pd
import os

from datetime import datetime
from openpyxl import load_workbook


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

    os.makedirs("outputs", exist_ok=True)

    df = pd.DataFrame([data], columns=COLUMNS)

    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")

    output_file = f"outputs/{data.get('consumer_number', 'bill')}_{timestamp}.xlsx"

    df.to_excel(output_file, index=False)

    return output_file


# =========================================================
# NEW MULTI EXCEL FUNCTION
# =========================================================

def fill_excel_multi(all_data):

    os.makedirs("outputs", exist_ok=True)

    template_path = "template.xlsx"

    wb = load_workbook(template_path)
    ws = wb.active

    # -------------------------------------------------
    # CUSTOMER DETAILS
    # -------------------------------------------------

    first = all_data[0]

    ws["D1"] = first.get("consumer_name", "")
    ws["D2"] = first.get("consumer_number", "")
    ws["D3"] = first.get("bill_amount", "")
    ws["D4"] = f"{first.get('load_kw', '')} KW"
    ws["D5"] = first.get("tariff", "")

    # -------------------------------------------------
    # MONTHLY DATA
    # -------------------------------------------------

    start_row = 10

    total_units = 0

    for index, bill in enumerate(all_data):

        row = start_row + index

        bill_date = bill.get("bill_date", "")

        try:
            dt = datetime.strptime(bill_date, "%d-%m-%Y")
            month_name = dt.strftime("%B %Y")
        except:
            month_name = bill_date

        units = float(bill.get("units", 0) or 0)

        ws[f"C{row}"] = month_name
        ws[f"D{row}"] = units

        total_units += units

    # -------------------------------------------------
    # CALCULATIONS
    # -------------------------------------------------

    avg_units = total_units / len(all_data)

    ws["D25"] = round(avg_units, 2)

    kw = avg_units / 106
    ws["D26"] = round(kw, 2)

    solar_panels = kw / 0.6
    ws["D27"] = round(solar_panels, 2)

    solar_capacity = round(solar_panels)
    ws["D28"] = solar_capacity

    num_panels = solar_capacity * 2
    ws["D29"] = num_panels

    # -------------------------------------------------
    # SAVE
    # -------------------------------------------------

    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")

    output_file = f"outputs/all_bills_{timestamp}.xlsx"

    wb.save(output_file)

    print(f"\n✅ Excel saved: {output_file}")

    return output_file