from openpyxl import Workbook
from openpyxl.styles import Font, PatternFill, Border, Side
from datetime import datetime
import os
import re


def fill_excel_multi(all_data):

    os.makedirs("outputs", exist_ok=True)

    wb = Workbook()
    
    # Remove default sheet
    default_sheet = wb.active
    wb.remove(default_sheet)

    for i, data in enumerate(all_data):
        # Create a new sheet for each bill
        sheet_name = f"Bill_{i+1}"
        if data.get("consumer_name"):
            # Clean sheet name (max 31 chars, no special chars)
            sheet_name = re.sub(r'[\\*?:/\[\]]', '', data.get("consumer_name"))[:30]
        
        ws = wb.create_sheet(title=sheet_name)

        # -------------------------------------------------
        # STYLES
        # -------------------------------------------------

        bold = Font(bold=True)

        header_fill = PatternFill(
            start_color="FFA500",
            end_color="FFA500",
            fill_type="solid"
        )

        yellow_fill = PatternFill(start_color="FFFF00", end_color="FFFF00", fill_type="solid")
        green_fill = PatternFill(start_color="90EE90", end_color="90EE90", fill_type="solid")

        thin = Side(style='thin')
        border = Border(left=thin, right=thin, top=thin, bottom=thin)

        # -------------------------------------------------
        # CUSTOMER DETAILS (Columns B and D)
        # -------------------------------------------------

        # Row 1: Consumer Name
        ws["B1"] = "Consumer Name"
        ws["D1"] = data.get("consumer_name", "")
        ws["B1"].font = bold
        ws["B1"].fill = header_fill
        ws["B1"].border = border
        ws["D1"].border = border

        # Row 2: Consumer No
        ws["B2"] = "Consumer No"
        ws["D2"] = data.get("consumer_number", "")
        ws["B2"].font = bold
        ws["B2"].fill = header_fill
        ws["B2"].border = border
        ws["D2"].border = border

        # Row 3: Fixed Charges
        ws["B3"] = "Fixed Charges"
        ws["D3"] = data.get("fixed_charges", "130")
        ws["B3"].font = bold
        ws["B3"].fill = header_fill
        ws["B3"].border = border
        ws["D3"].border = border

        # Row 4: Sanct. Load (kW)
        ws["B4"] = "Sanct. Load (kW)"
        ws["D4"] = f"{data.get('load_kw', '')}KW"
        ws["B4"].font = bold
        ws["B4"].fill = header_fill
        ws["B4"].border = border
        ws["D4"].border = border

        # Row 5: Connection Type
        ws["B5"] = "Connection Type"
        ws["D5"] = data.get("tariff", "")
        ws["B5"].font = bold
        ws["B5"].fill = header_fill
        ws["B5"].border = border
        ws["D5"].border = border

        # Row 7: Solar Panel Used
        ws["B7"] = "Solar Pannel used"
        ws["C7"] = 600
        ws["B7"].font = bold
        ws["B7"].fill = header_fill
        ws["B7"].border = border
        ws["C7"].fill = yellow_fill
        ws["C7"].border = border

        # -------------------------------------------------
        # TABLE HEADER
        # -------------------------------------------------

        start_row = 10
        headers = ["Sr.No", "Month", "Units", "Bill Amount", "Unit Cost"]

        for col, header in enumerate(headers, start=2):
            cell = ws.cell(row=start_row, column=col)
            cell.value = header
            cell.font = bold
            cell.fill = header_fill
            cell.border = border

        # -------------------------------------------------
        # MONTHLY HISTORY DATA
        # -------------------------------------------------

        monthly_history = data.get("monthly_history", [])
        total_units = 0

        for index, item in enumerate(monthly_history):
            row_idx = start_row + index + 1
            ws.cell(row=row_idx, column=2).value = index + 2
            ws.cell(row=row_idx, column=3).value = item.get("month", "")
            ws.cell(row=row_idx, column=4).value = item.get("units", 0)
            
            for col in range(2, 7):
                ws.cell(row=row_idx, column=col).border = border

            total_units += item.get("units", 0)

        # -------------------------------------------------
        # CALCULATIONS
        # -------------------------------------------------

        calc_row = start_row + len(monthly_history) + 1

        if len(monthly_history) > 0:
            avg_units = total_units / len(monthly_history)
        else:
            avg_units = 0

        kw = avg_units / 106
        solar_panels = kw / 0.6
        solar_capacity = round(solar_panels * 0.7, 1)
        num_panels = round(solar_capacity / 0.6)

        calculations = [
            ("Average", round(avg_units, 2)),
            ("kW", round(kw, 2)),
            ("Solar Panels", round(solar_panels, 2)),
            ("Solar capacity", solar_capacity),
            ("Number of Panels", num_panels),
        ]

        for label, value in calculations:
            ws.cell(row=calc_row, column=3).value = label
            ws.cell(row=calc_row, column=4).value = value
            ws.cell(row=calc_row, column=3).font = bold
            ws.cell(row=calc_row, column=3).border = border
            ws.cell(row=calc_row, column=4).border = border
            
            if label == "Solar capacity":
                ws.cell(row=calc_row, column=4).fill = yellow_fill
            if label == "Number of Panels":
                ws.cell(row=calc_row, column=4).fill = green_fill

            calc_row += 1

        # Bottom summary
        ws.cell(row=calc_row+2, column=3).value = "Total solar capacity"
        ws.cell(row=calc_row+2, column=4).value = solar_capacity * 2
        ws.cell(row=calc_row+3, column=3).value = "Number of solar panels"
        ws.cell(row=calc_row+3, column=4).value = num_panels * 2

        # Column widths
        ws.column_dimensions["A"].width = 10
        ws.column_dimensions["B"].width = 25
        ws.column_dimensions["C"].width = 30
        ws.column_dimensions["D"].width = 25
        ws.column_dimensions["E"].width = 15
        ws.column_dimensions["F"].width = 15

    # -------------------------------------------------
    # SAVE
    # -------------------------------------------------

    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    output_file = f"outputs/all_bills_{timestamp}.xlsx"

    wb.save(output_file)

    print(f"\nExcel saved: {output_file}")

    return output_file