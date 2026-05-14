import os
import json
import base64
import cv2

from groq import Groq
from mistralai import Mistral


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

    x1 = int(w * 0.03)
    y1 = int(h * 0.09)

    x2 = int(w * 0.28)
    y2 = int(h * 0.14)

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

        if len(consumer) > 12:

            consumer = consumer[-12:]

        final["consumer_number"] = consumer

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

        final["meter_number"] = only_digits(
            meter_data["meter_number"]
        )

    # =====================================================
    # GRAPH EXTRACTION
    # =====================================================

    graph_image = crop_history_graph(
        image_path
    )

    graph_history = extract_graph_history(
        graph_image,
        mistral_key
    )

    final["monthly_history"] = clean_history(
        graph_history
    )

    print(
        json.dumps(
            final,
            indent=2,
            ensure_ascii=False
        )
    )

    return final