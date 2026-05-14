import os
import re
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
# HISTORY CLEAN
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
            continue

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
- Do NOT explain
- Do NOT calculate
- Do NOT modify values
- Do NOT guess missing values
- Preserve exact bill values

IMPORTANT:

- Consumer number must be exact
- Meter number must be exact
- Bill amount exact
- Late amount exact
- Readings exact
- Units exact
- Load exact

- Units means electricity consumption only
- Do NOT return multiplier
- Do NOT return MF value
- Units must match:
  current_reading - previous_reading

Extract:

consumer_name
consumer_number
meter_number
load_kw
tariff
bill_date
due_date
bill_amount
late_amount
current_reading
previous_reading
units

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
  "units":""
}
"""


# =====================================================
# GRAPH PROMPT
# =====================================================

GRAPH_PROMPT = """
Extract ONLY monthly electricity usage history.

STRICT RULES:

- Return ONLY JSON
- Ignore axis labels like 100 200 300
- Ignore QR codes
- Ignore other text
- Extract exact month + units
- If usage is 0 return 0 exactly

JSON FORMAT:

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
# MISTRAL EXTRACTION
# =====================================================

def extract_with_mistral(
    image_path,
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
    groq_key
):

    client = Groq(
        api_key=groq_key
    )

    base64_image = encode_image(
        graph_image
    )

    response = client.chat.completions.create(

        model="meta-llama/llama-4-scout-17b-16e-instruct",

        messages=[

            {
                "role":"user",

                "content":[

                    {
                        "type":"text",
                        "text":GRAPH_PROMPT
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

    data = json.loads(content)

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
        "units"
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

    # =====================================================
    # FIX CONSUMER NUMBER
    # =====================================================

    consumer = only_digits(
        final.get("consumer_number", "")
    )

    if len(consumer) > 12:

        consumer = consumer[:12]

    final["consumer_number"] = consumer

    # =====================================================
    # VALIDATION
    # =====================================================

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

    print("\n========== MISTRAL EXTRACTION ==========\n")

    mistral_data = extract_with_mistral(
        image_path,
        mistral_key
    )

    print(
        json.dumps(
            mistral_data,
            indent=2,
            ensure_ascii=False
        )
    )

    print("\n========== LLAMA EXTRACTION ==========\n")

    llama_data = extract_with_llama(
        image_path,
        groq_key
    )

    print(
        json.dumps(
            llama_data,
            indent=2,
            ensure_ascii=False
        )
    )

    print("\n========== MERGING ==========\n")

    final = merge_results(
        mistral_data,
        llama_data
    )

    # =====================================================
    # GRAPH EXTRACTION
    # =====================================================

    graph_image = crop_history_graph(
        image_path
    )

    graph_history = extract_graph_history(
        graph_image,
        groq_key
    )

    if graph_history:

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