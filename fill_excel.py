# ================================
# fill_excel.py
# ================================

from openpyxl import Workbook
from openpyxl.styles import Font, PatternFill, Border, Side
from datetime import datetime
import os
import math


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

        consumer_no = consumer_no[:12]

        load_kw = str(
            data.get("load_kw", "")
        ).replace("KW", "").strip()

        tariff = data.get(
            "tariff",
            "90/LT I Res 1-Phase"
        )

        # -------------------------------------------------
        # DETAILS
        # -------------------------------------------------

        details = [
            ("Consumer Name", data.get("consumer_name", "")),
            ("Consumer No", consumer_no),
            ("Fixed Charges", data.get("fixed_charges", "130")),
            ("Sanct. Load (kW)", f"{load_kw}KW"),
            ("Connection Type", tariff),
            ("Contract Demand (KVA)", ""),
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

        ws.cell(8, lc).value = "Solar Panel used"

        ws.cell(8, lc + 2).value = 600

        ws.cell(8, lc).fill = orange
        ws.cell(8, lc + 2).fill = yellow

        ws.cell(8, lc).font = bold

        ws.cell(8, lc).border = border
        ws.cell(8, lc + 2).border = border

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

        total_units = 0

        # -------------------------------------------------
        # WRITE HISTORY
        # -------------------------------------------------

        for index in range(13):

            row_idx = start_row + index + 1

            ws.cell(
                row=row_idx,
                column=lc
            ).value = index + 1

            # ---------------------------------------------
            # SAFE ITEM
            # ---------------------------------------------

            if index < len(history):

                item = history[index]

            else:

                item = {
                    "month": "",
                    "units": 0
                }

            month_name = item.get(
                "month",
                ""
            )

            ws.cell(
                row=row_idx,
                column=lc + 1
            ).value = month_name

            units_value = item.get(
                "units",
                0
            )

            try:

                units_value = int(
                    float(units_value)
                )

            except:

                units_value = 0

            ws.cell(
                row=row_idx,
                column=lc + 2
            ).value = units_value

            total_units += units_value

            # ---------------------------------------------
            # BORDERS
            # ---------------------------------------------

            for col in range(lc, lc + 5):

                ws.cell(
                    row=row_idx,
                    column=col
                ).border = border

        # -------------------------------------------------
        # CALCULATIONS
        # -------------------------------------------------

        avg_units = round(
            total_units / 12,
            2
        )

        # ---------------------------------------------
        # kW CALCULATION
        # ---------------------------------------------

        kw = round(
            avg_units / 106,
            3
        )

        # ---------------------------------------------
        # PANEL DETAILS
        # ---------------------------------------------

        panel_watts = 600

        panel_kw = panel_watts / 1000

        # ---------------------------------------------
        # REQUIRED PANELS
        # ---------------------------------------------

        number_panels = math.ceil(
            kw / panel_kw
        )

        # ---------------------------------------------
        # SOLAR CAPACITY
        # ---------------------------------------------

        solar_capacity = round(
            number_panels * panel_kw,
            1
        )

        # ---------------------------------------------
        # SOLAR PANELS VALUE
        # ---------------------------------------------

        solar_panels = round(
            kw / panel_kw,
            3
        )

        # ---------------------------------------------
        # TOTALS
        # ---------------------------------------------

        total_capacity += solar_capacity
        total_panels += number_panels

        # -------------------------------------------------
        # BILL AMOUNT + UNIT COST
        # -------------------------------------------------

        bill_amount = safe_float(
            data.get("bill_amount", 0)
        )

        units_main = safe_float(
            data.get("units", 0)
        )

        unit_cost = 0

        if units_main > 0:

            unit_cost = round(
                bill_amount / units_main,
                2
            )

        # -------------------------------------------------
        # WRITE CALCULATIONS
        # -------------------------------------------------

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
        # BILL AMOUNT + UNIT COST BESIDE AVERAGE
        # -------------------------------------------------

        ws.cell(
            row=24,
            column=lc + 3
        ).value = bill_amount

        ws.cell(
            row=24,
            column=lc + 4
        ).value = unit_cost

        ws.cell(
            row=24,
            column=lc + 3
        ).border = border

        ws.cell(
            row=24,
            column=lc + 4
        ).border = border

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

    ws["D32"].font = bold
    ws["D33"].font = bold

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