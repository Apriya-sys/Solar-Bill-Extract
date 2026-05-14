import os
import json
import base64
import cv2
import pytesseract
import platform

from groq import Groq
from mistralai import Mistral
from datetime import datetime

# =====================================================
# TESSERACT CONFIG
# =====================================================

if platform.system() == "Windows":

    pytesseract.pytesseract.tesseract_cmd = (
        r"C:\Program Files\Tesseract-OCR\tesseract.exe"
    )


# =====================================================
# IMAGE ENCODER
# =====================================================

def encode_image(image_path):

    with open(image_path, "rb") as f:

        return base64.b64encode(
            f.read()
        ).decode("utf-8")


# =====================================================
# HELPERS
# =====================================================

def only_digits(text):

    return "".join(
        filter(str.isdigit, str(text))
    )


# =====================================================
# TESSERACT DIGIT OCR
# =====================================================

def extract_digits_tesseract(image_path):

    try:

        img = cv2.imread(image_path)

        gray = cv2.cvtColor(
            img,
            cv2.COLOR_BGR2GRAY
        )

        gray = cv2.resize(
            gray,
            None,
            fx=4,
            fy=4
        )

        thresh = cv2.threshold(
            gray,
            0,
            255,
            cv2.THRESH_BINARY + cv2.THRESH_OTSU
        )[1]

        text = pytesseract.image_to_string(

            thresh,

            config=(
                "--psm 7 "
                "-c tessedit_char_whitelist=0123456789"
            )
        )

        return only_digits(text)

    except:

        return ""


def validate_units(data):

    try:

        curr = int(
            only_digits(
                data.get("current_reading", "")
            )
        )

        prev = int(
            only_digits(
                data.get("previous_reading", "")
            )
        )

        units = int(
            only_digits(
                data.get("units", "")
            )
        )

        diff = curr - prev

        return abs(diff - units) <= 2

    except:

        return False


def choose_best(v1, v2):

    v1 = str(v1).strip()
    v2 = str(v2).strip()

    if len(v1) > len(v2):

        return v1

    return v2


# =====================================================
# CLEAN HISTORY
# =====================================================

def clean_history(history):

    cleaned = []

    seen = set()

    for item in history:

        month = str(
            item.get("month", "")
        ).strip()

        units = only_digits(
            item.get("units", "")
        )

        if not month:
            continue

        if units == "":
            units = "0"

        # =====================================================
        # FIX MONTH FORMAT
        # =====================================================

        try:

            # FORMAT: 2025-01
            if "-" in month:

                parts = month.split("-")

                # 2025-01
                if (
                    len(parts) == 2
                    and parts[0].isdigit()
                    and parts[1].isdigit()
                ):

                    year = parts[0]
                    mon = parts[1]

                    month_name = datetime.strptime(
                        mon,
                        "%m"
                    ).strftime("%B")

                    month = f"{month_name} {year}"

                # 2025-Jan
                elif (
                    len(parts) == 2
                    and parts[0].isdigit()
                ):

                    year = parts[0]

                    mon = parts[1][:3]

                    month_name = datetime.strptime(
                        mon,
                        "%b"
                    ).strftime("%B")

                    month = f"{month_name} {year}"

                # Jan-2025
                elif (
                    len(parts) == 2
                    and parts[1].isdigit()
                ):

                    mon = parts[0][:3]

                    year = parts[1]

                    month_name = datetime.strptime(
                        mon,
                        "%b"
                    ).strftime("%B")

                    month = f"{month_name} {year}"

        except:
            pass

        key = month.lower()

        if key in seen:
            continue

        seen.add(key)

        cleaned.append({

            "month": month,

            "units": units
        })

    return cleaned

# =====================================================
# CONSUMER NUMBER CROP
# =====================================================

def crop_consumer_number(image_path):

    img = cv2.imread(image_path)

    h, w = img.shape[:2]
    x1 = int(w * 0.02)
    y1 = int(h * 0.08)

    x2 = int(w * 0.34)
    y2 = int(h * 0.145)

    crop = img[y1:y2, x1:x2]

    gray = cv2.cvtColor(
        crop,
        cv2.COLOR_BGR2GRAY
    )

    gray = cv2.resize(
        gray,
        None,
        fx=4,
        fy=4
    )

    thresh = cv2.threshold(
        gray,
        0,
        255,
        cv2.THRESH_BINARY + cv2.THRESH_OTSU
    )[1]

    path = "consumer_crop.jpg"

    cv2.imwrite(path, thresh)

    return path


# =====================================================
# METER NUMBER CROP
# =====================================================

def crop_meter_number(image_path):

    img = cv2.imread(image_path)

    h, w = img.shape[:2]

    x1 = int(w * 0.05)
    y1 = int(h * 0.24)

    x2 = int(w * 0.42)
    y2 = int(h * 0.42)

    crop = img[y1:y2, x1:x2]

    path = "meter_crop.jpg"

    cv2.imwrite(path, crop)

    return path


# =====================================================
# GRAPH CROP
# =====================================================

def crop_history_graph(image_path):

    img = cv2.imread(image_path)

    h, w = img.shape[:2]

    x1 = int(w * 0.47)
    y1 = int(h * 0.34)

    x2 = int(w * 0.78)
    y2 = int(h * 0.69)

    crop = img[y1:y2, x1:x2]

    gray = cv2.cvtColor(
        crop,
        cv2.COLOR_BGR2GRAY
    )

    gray = cv2.resize(
        gray,
        None,
        fx=3,
        fy=3
    )

    thresh = cv2.threshold(
        gray,
        0,
        255,
        cv2.THRESH_BINARY + cv2.THRESH_OTSU
    )[1]

    graph_path = "history_graph.jpg"

    cv2.imwrite(
        graph_path,
        thresh
    )

    return graph_path


# =====================================================
# MAIN PROMPT
# =====================================================

PROMPT = """
Extract EXACT data from this Maharashtra MSEDCL electricity bill.

STRICT RULES:

- Return ONLY valid JSON
- Preserve exact values
- Do NOT guess
- Do NOT rearrange digits

JSON FORMAT:

{
  "consumer_name":"",
  "consumer_number":"",
  "meter_number":"",
  "load_kw":"",
  "tariff":"",
  "bill_date":"",
  "due_date":"",
  "bill_amount":"",
  "late_amount":"",
  "current_reading":"",
  "previous_reading":"",
  "units":"",
  "fixed_charges":"",
  "energy_charges":"",
  "electricity_duty":"",
  "wheeling_charges":"",
  "fuel_adjustment":"",
  "unit_cost":""
}
"""


# =====================================================
# CONSUMER PROMPT
# =====================================================

CONSUMER_PROMPT = """
Extract ONLY consumer number.

Return JSON:

{
  "consumer_number":""
}
"""


# =====================================================
# METER PROMPT
# =====================================================

METER_PROMPT = """
Extract ONLY meter number.

Return JSON:

{
  "meter_number":""
}
"""


# =====================================================
# GRAPH PROMPT
# =====================================================

GRAPH_PROMPT = """
Extract EXACT monthly electricity usage history from graph/table.

STRICT RULES:

- Return ONLY JSON
- Preserve exact month names
- Preserve exact unit values
- Do NOT guess
- Do NOT reorder months
- Do NOT skip months
- If month usage is 0 return 0

Return JSON:

{
  "monthly_history":[
    {
      "month":"",
      "units":""
    }
  ]
}
"""


# =====================================================
# GENERIC MISTRAL EXTRACTOR
# =====================================================

def mistral_extract(
    image_path,
    prompt,
    mistral_key
):

    client = Mistral(
        api_key=mistral_key
    )

    base64_image = encode_image(
        image_path
    )

    response = client.chat.complete(

        model="pixtral-12b-2409",

        messages=[

            {
                "role":"user",

                "content":[

                    {
                        "type":"text",
                        "text":prompt
                    },

                    {
                        "type":"image_url",

                        "image_url":{
                            "url":f"data:image/jpeg;base64,{base64_image}"
                        }
                    }
                ]
            }
        ],

        response_format={
            "type":"json_object"
        }
    )

    content = (
        response
        .choices[0]
        .message
        .content
    )

    return json.loads(content)


# =====================================================
# LLAMA EXTRACTION
# =====================================================

def extract_with_llama(
    image_path,
    groq_key
):

    client = Groq(
        api_key=groq_key
    )

    base64_image = encode_image(
        image_path
    )

    response = client.chat.completions.create(

        model="meta-llama/llama-4-scout-17b-16e-instruct",

        messages=[

            {
                "role":"user",

                "content":[

                    {
                        "type":"text",
                        "text":PROMPT
                    },

                    {
                        "type":"image_url",

                        "image_url":{
                            "url":f"data:image/jpeg;base64,{base64_image}"
                        }
                    }
                ]
            }
        ],

        response_format={
            "type":"json_object"
        }
    )

    content = (
        response
        .choices[0]
        .message
        .content
    )

    return json.loads(content)


# =====================================================
# GRAPH EXTRACTION
# =====================================================

def extract_graph_history(
    graph_image,
    mistral_key
):

    data = mistral_extract(
        graph_image,
        GRAPH_PROMPT,
        mistral_key
    )

    return data.get(
        "monthly_history",
        []
    )


# =====================================================
# MERGE RESULTS
# =====================================================

def merge_results(
    mistral_data,
    llama_data
):

    final = {}

    fields = [

        "consumer_name",
        "consumer_number",
        "meter_number",
        "load_kw",
        "tariff",
        "bill_date",
        "due_date",
        "bill_amount",
        "late_amount",
        "current_reading",
        "previous_reading",
        "units",

        "fixed_charges",
        "energy_charges",
        "electricity_duty",
        "wheeling_charges",
        "fuel_adjustment",
        "unit_cost"
    ]

    for field in fields:

        m_val = mistral_data.get(
            field,
            ""
        )

        l_val = llama_data.get(
            field,
            ""
        )

        if str(m_val).strip() == str(l_val).strip():

            final[field] = m_val

        else:

            final[field] = choose_best(
                m_val,
                l_val
            )

    # FIX CONSUMER NUMBER

    consumer = only_digits(
        final.get("consumer_number", "")
    )

    if len(consumer) > 12:

        consumer = consumer[-12:]

    final["consumer_number"] = consumer

    # FIX METER NUMBER

    meter = only_digits(
        final.get("meter_number", "")
    )

    final["meter_number"] = meter

    # UNIT COST

    try:

        bill_amount = float(
            final.get("bill_amount", 0)
        )

        units = float(
            final.get("units", 0)
        )

        if units > 0:

            final["unit_cost"] = round(
                bill_amount / units,
                2
            )

    except:

        final["unit_cost"] = 0

    final["valid_units"] = validate_units(
        final
    )

    return final
# =====================================================
# MAIN FUNCTION
# =====================================================

def extract_with_ensemble(
    image_path,
    mistral_key=None,
    groq_key=None
):

    print("\n========== MISTRAL ==========\n")

    mistral_data = mistral_extract(
        image_path,
        PROMPT,
        mistral_key
    )

    print(
        json.dumps(
            mistral_data,
            indent=2
        )
    )

    print("\n========== LLAMA ==========\n")

    llama_data = extract_with_llama(
        image_path,
        groq_key
    )

    print(
        json.dumps(
            llama_data,
            indent=2
        )
    )

    # =====================================================
    # MERGE RESULTS
    # =====================================================

    final = merge_results(
        mistral_data,
        llama_data
    )

    # =====================================================
    # CONSUMER NUMBER RECHECK
    # =====================================================

    consumer_crop = crop_consumer_number(
        image_path
    )

    consumer_data = mistral_extract(
        consumer_crop,
        CONSUMER_PROMPT,
        mistral_key
    )

    if consumer_data.get("consumer_number"):

        consumer = only_digits(
            consumer_data["consumer_number"]
        )

        if len(consumer) >= 10:

            if len(consumer) > 12:

                consumer = consumer[-12:]

            final["consumer_number"] = consumer

        else:

            tesseract_consumer = (
                extract_digits_tesseract(
                    consumer_crop
                )
            )

            if len(tesseract_consumer) >= 10:

                if len(tesseract_consumer) > 12:

                    tesseract_consumer = (
                        tesseract_consumer[-12:]
                    )

                final["consumer_number"] = (
                    tesseract_consumer
                )

    # =====================================================
    # METER NUMBER RECHECK
    # =====================================================

    meter_crop = crop_meter_number(
        image_path
    )

    meter_data = mistral_extract(
        meter_crop,
        METER_PROMPT,
        mistral_key
    )

    if meter_data.get("meter_number"):

        meter = only_digits(
            meter_data["meter_number"]
        )

        if len(meter) >= 10:

            final["meter_number"] = meter

        else:

            tesseract_meter = (
                extract_digits_tesseract(
                    meter_crop
                )
            )

            if len(tesseract_meter) >= 10:

                final["meter_number"] = (
                    tesseract_meter
                )

    # =====================================================
    # UNIT COST
    # =====================================================

    try:

        bill_amount = float(
            final.get("bill_amount", 0)
        )

        units = float(
            final.get("units", 0)
        )

        if units > 0:

            final["unit_cost"] = round(
                bill_amount / units,
                2
            )

        else:

            final["unit_cost"] = 0

    except:

        final["unit_cost"] = 0

    # =====================================================
    # FIXED CHARGES
    # =====================================================

    fixed = str(
        final.get("fixed_charges", "")
    ).strip()

    if (
        not fixed
        or fixed == "0"
        or fixed == "0.00"
    ):

        load = str(
            final.get("load_kw", "")
        )

        if "1.00" in load:

            final["fixed_charges"] = "130"

        elif "3.30" in load:

            final["fixed_charges"] = "320"

        else:

            final["fixed_charges"] = "130"

    # =====================================================
    # VALIDATE UNITS
    # =====================================================

    final["valid_units"] = validate_units(
        final
    )

    # =====================================================
    # GRAPH EXTRACTION
    # =====================================================

# =====================================================
# FIXED MONTH HISTORY ORDER
# =====================================================

    months = [

        "December 2025",
        "November 2025",
        "October 2025",
        "September 2025",
        "August 2025",
        "July 2025",
        "June 2025",
        "May 2025",
        "April 2025",
        "March 2025",
        "February 2025"
    ]

    graph_image = crop_history_graph(
        image_path
    )

    graph_history = extract_graph_history(
        graph_image,
        mistral_key
    )

    cleaned_history = clean_history(
        graph_history
    )

    fixed_history = []

    for i, item in enumerate(cleaned_history):

        if i >= len(months):
            break

        fixed_history.append({

            "month": months[i],

            "units": item.get("units", "0")
        })

    final["monthly_history"] = fixed_history

    print(
        json.dumps(
            final,
            indent=2,
            ensure_ascii=False
        )
    )

    return final