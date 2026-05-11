from openpyxl import Workbook
from openpyxl.styles import Font, PatternFill, Border, Side
from datetime import datetime
import os


def fill_excel_multi(all_data):

    os.makedirs("outputs", exist_ok=True)

    wb = Workbook()
    ws = wb.active

    ws.title = "Solar Report"

    # -------------------------------------------------
    # STYLES
    # -------------------------------------------------

    bold = Font(bold=True)

    header_fill = PatternFill(
        start_color="FFA500",
        end_color="FFA500",
        fill_type="solid"
    )

    thin = Side(style='thin')

    border = Border(
        left=thin,
        right=thin,
        top=thin,
        bottom=thin
    )

    # -------------------------------------------------
    # CUSTOMER DETAILS
    # -------------------------------------------------

    first = all_data[0]

    details = [
        ("Consumer Name", first.get("consumer_name", "")),
        ("Consumer Number", first.get("consumer_number", "")),
        ("Bill Amount", first.get("bill_amount", "")),
        ("Sanctioned Load", f"{first.get('load_kw', '')} KW"),
        ("Tariff", first.get("tariff", "")),
    ]

    row = 1

    for label, value in details:

        ws[f"A{row}"] = label
        ws[f"B{row}"] = value

        ws[f"A{row}"].font = bold
        ws[f"A{row}"].fill = header_fill

        ws[f"A{row}"].border = border
        ws[f"B{row}"].border = border

        row += 1

    # -------------------------------------------------
    # TABLE HEADER
    # -------------------------------------------------

    start_row = 10

    headers = ["Sr.No", "Month", "Units"]

    for col, header in enumerate(headers, start=1):

        cell = ws.cell(row=start_row, column=col)

        cell.value = header
        cell.font = bold
        cell.fill = header_fill
        cell.border = border

    # -------------------------------------------------
    # MONTHLY HISTORY DATA
    # -------------------------------------------------

    monthly_history = first.get("monthly_history", [])

    total_units = 0

    for index, item in enumerate(monthly_history):

        row = start_row + index + 1

        ws[f"A{row}"] = index + 2
        ws[f"B{row}"] = item.get("month", "")
        ws[f"C{row}"] = item.get("units", 0)

        ws[f"A{row}"].border = border
        ws[f"B{row}"].border = border
        ws[f"C{row}"].border = border

        total_units += item.get("units", 0)

    # -------------------------------------------------
    # CALCULATIONS
    # -------------------------------------------------

    calc_row = start_row + len(monthly_history) + 3

    if len(monthly_history) > 0:
        avg_units = total_units / len(monthly_history)
    else:
        avg_units = 0

    kw = avg_units / 106

    solar_panels = kw / 0.6

    solar_capacity = round(solar_panels * 0.7, 1)

    num_panels = round(solar_capacity / 0.6)

    calculations = [
        ("Average Units", round(avg_units, 2)),
        ("Required kW", round(kw, 2)),
        ("Solar Panels", round(solar_panels, 2)),
        ("Solar Capacity", solar_capacity),
        ("Number of Panels", num_panels),
    ]

    for label, value in calculations:

        ws[f"A{calc_row}"] = label
        ws[f"B{calc_row}"] = value

        ws[f"A{calc_row}"].font = bold
        ws[f"A{calc_row}"].fill = header_fill

        ws[f"A{calc_row}"].border = border
        ws[f"B{calc_row}"].border = border

        calc_row += 1

    # -------------------------------------------------
    # COLUMN WIDTH
    # -------------------------------------------------

    ws.column_dimensions["A"].width = 25
    ws.column_dimensions["B"].width = 30
    ws.column_dimensions["C"].width = 15

    # -------------------------------------------------
    # SAVE
    # -------------------------------------------------

    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")

    output_file = f"outputs/all_bills_{timestamp}.xlsx"

    wb.save(output_file)

    print(f"\n✅ Excel saved: {output_file}")

    return output_file