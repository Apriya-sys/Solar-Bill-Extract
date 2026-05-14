# ================================
# fill_excel.py
# ================================

from openpyxl import Workbook
from openpyxl.styles import Font, PatternFill, Border, Side
from datetime import datetime
import os


# -------------------------------------------------
# SAFE FLOAT
# -------------------------------------------------

def safe_float(v):

    try:

        return float(
            str(v)
            .replace(",", "")
            .replace("KW", "")
            .strip()
        )

    except:

        return 0


# -------------------------------------------------
# NORMALIZE MONTH
# -------------------------------------------------

def normalize_month(text):

    return (
        str(text)
        .replace("-", " ")
        .replace("_", " ")
        .replace("  ", " ")
        .strip()
        .lower()
    )


# -------------------------------------------------
# MAIN
# -------------------------------------------------

def fill_excel_multi(all_data):

    os.makedirs(
        "outputs",
        exist_ok=True
    )

    wb = Workbook()

    ws = wb.active

    ws.title = "Solar_Output"

    # -------------------------------------------------
    # STYLES
    # -------------------------------------------------

    bold = Font(bold=True)

    orange = PatternFill(
        start_color="F4B183",
        end_color="F4B183",
        fill_type="solid"
    )

    yellow = PatternFill(
        start_color="FFFF00",
        end_color="FFFF00",
        fill_type="solid"
    )

    green = PatternFill(
        start_color="92D050",
        end_color="92D050",
        fill_type="solid"
    )

    thin = Side(style="thin")

    border = Border(
        left=thin,
        right=thin,
        top=thin,
        bottom=thin
    )

    positions = [
        {"label_col": 2},
        {"label_col": 8}
    ]

    total_capacity = 0
    total_panels = 0

    expected_months = [
        "February 2025",
        "March 2025",
        "April 2025",
        "May 2025",
        "June 2025",
        "July 2025",
        "August 2025",
        "September 2025",
        "October 2025",
        "November 2025",
        "December 2025",
        "January 2026"
    ]

    # -------------------------------------------------
    # LOOP
    # -------------------------------------------------

    for idx, data in enumerate(all_data[:2]):

        lc = positions[idx]["label_col"]

        # -------------------------------------------------
        # CLEAN VALUES
        # -------------------------------------------------

        consumer_no = str(
            data.get("consumer_number", "")
        ).replace(" ", "").replace("-", "")

        if len(consumer_no) == 10:

            consumer_no = "43" + consumer_no

        load_kw = str(
            data.get("load_kw", "")
        ).replace("KW", "").strip()

        tariff = "90/LT I Res 1-Phase"

        # -------------------------------------------------
        # DETAILS
        # -------------------------------------------------

        details = [
            ("Consumer Name", data.get("consumer_name", "")),
            ("Consumer No", consumer_no),
            ("Fixed Charges", data.get("fixed_charges", "130")),
            ("Sanct. Load (kW)", f"{load_kw}KW"),
            ("Connection Type", tariff),
            ("Contract Demand (KVA) :", ""),
        ]

        row = 2

        for label, value in details:

            ws.cell(row, lc).value = label
            ws.cell(row, lc + 2).value = value

            ws.cell(row, lc).fill = orange
            ws.cell(row, lc).font = bold

            ws.cell(row, lc).border = border
            ws.cell(row, lc + 2).border = border

            row += 1

        # -------------------------------------------------
        # SOLAR PANEL USED
        # -------------------------------------------------

        ws.cell(8, lc).value = "Solar Pannel used"

        ws.cell(8, lc + 2).value = 600

        ws.cell(8, lc).fill = orange

        ws.cell(8, lc + 2).fill = yellow

        ws.cell(8, lc).font = bold

        # -------------------------------------------------
        # HEADERS
        # -------------------------------------------------

        headers = [
            "Sr.No",
            "Month",
            "Units",
            "Bill Amount",
            "Unit Cost"
        ]

        start_row = 10

        for h_idx, header in enumerate(headers):

            cell = ws.cell(
                start_row,
                lc + h_idx
            )

            cell.value = header

            cell.fill = orange

            cell.font = bold

            cell.border = border

        # -------------------------------------------------
        # HISTORY
        # -------------------------------------------------

        history = data.get(
            "monthly_history",
            []
        )

        history_map = {}

        for item in history:

            month = normalize_month(
                item.get("month", "")
            )

            units = safe_float(
                item.get("units", 0)
            )

            history_map[month] = units

        total_units = 0

        # Mappings for full month names
        month_map = {

            "JAN 2024": "January 2024",
            "FEB 2024": "February 2024",
            "MAR 2024": "March 2024",
            "APR 2024": "April 2024",
            "MAY 2024": "May 2024",
            "JUN 2024": "June 2024",
            "JUL 2024": "July 2024",
            "AUG 2024": "August 2024",
            "SEP 2024": "September 2024",
            "OCT 2024": "October 2024",
            "NOV 2024": "November 2024",
            "DEC 2024": "December 2024",

            "JAN 2025": "January 2025",
            "FEB 2025": "February 2025",
            "MAR 2025": "March 2025",
            "APR 2025": "April 2025",
            "MAY 2025": "May 2025",
            "JUN 2025": "June 2025",
            "JUL 2025": "July 2025",
            "AUG 2025": "August 2025",
            "SEP 2025": "September 2025",
            "OCT 2025": "October 2025",
            "NOV 2025": "November 2025",
            "DEC 2025": "December 2025",

            "JAN 2026": "January 2026",
            "FEB 2026": "February 2026",
            "MAR 2026": "March 2026"
        }

        for index in range(13): # Show 13 rows like in original
            row_idx = start_row + index + 1
            ws.cell(row=row_idx, column=2).value = index + 2
                    
        if index < len(monthly_history):

            item = monthly_history[index]

            m_short = item.get("month", "")

            ws.cell(
                row=row_idx,
                column=3
            ).value = month_map.get(
                m_short,
                m_short
            )

            units_value = item.get("units", 0)

            try:
                units_value = int(units_value)

            except:
                units_value = 0

            ws.cell(
                row=row_idx,
                column=4
            ).value = units_value

            total_units += units_value
            
            for col in range(2, 7):
                ws.cell(row=row_idx, column=col).border = border

        # -------------------------------------------------
        # CALCULATIONS
        # -------------------------------------------------

        avg_units = round(
            total_units / 12,
            2
        )

        kw = round(
            avg_units / 106,
            9
        )

        solar_panels = round(
            kw / 0.6,
            9
        )

        solar_capacity = round(
            solar_panels * 0.7,
            1
        )

        number_panels = round(
            solar_capacity / 0.6
        )

        total_capacity += solar_capacity

        total_panels += number_panels

        calc_start = 24

        calculations = [
            ("Average", avg_units),
            ("kW", kw),
            ("Solar Panels", solar_panels),
            ("Solar capacity", solar_capacity),
            ("Number of Panels", number_panels),
        ]

        for label, value in calculations:

            ws.cell(
                calc_start,
                lc + 1
            ).value = label

            ws.cell(
                calc_start,
                lc + 2
            ).value = value

            ws.cell(
                calc_start,
                lc + 1
            ).border = border

            ws.cell(
                calc_start,
                lc + 2
            ).border = border

            ws.cell(
                calc_start,
                lc + 1
            ).font = bold

            if label == "Solar capacity":

                ws.cell(
                    calc_start,
                    lc + 1
                ).fill = orange

                ws.cell(
                    calc_start,
                    lc + 2
                ).fill = yellow

            if label == "Number of Panels":

                ws.cell(
                    calc_start,
                    lc + 1
                ).fill = green

                ws.cell(
                    calc_start,
                    lc + 2
                ).fill = green

            calc_start += 1

    # -------------------------------------------------
    # TOTALS
    # -------------------------------------------------

    ws["D32"] = "Total solar capacity"

    ws["E32"] = round(
        total_capacity,
        1
    )

    ws["D33"] = "Number of solar panels"

    ws["E33"] = total_panels

    # -------------------------------------------------
    # WIDTHS
    # -------------------------------------------------

    widths = {
        "B":18,
        "C":28,
        "D":18,
        "E":18,
        "F":18,
        "H":18,
        "I":28,
        "J":18,
        "K":18,
        "L":18,
    }

    for col, width in widths.items():

        ws.column_dimensions[col].width = width

    # -------------------------------------------------
    # SAVE
    # -------------------------------------------------

    timestamp = datetime.now().strftime(
        "%Y%m%d_%H%M%S"
    )

    output_file = (
        f"outputs/solar_output_{timestamp}.xlsx"
    )

    wb.save(output_file)

    return output_file