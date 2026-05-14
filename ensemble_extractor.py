import os
import re
import json
import base64

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
# VALIDATORS
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

    # Prefer longer meaningful value
    if len(v1) > len(v2):
        return v1

    return v2


# =====================================================
# MONTH HISTORY CLEAN
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

        if not units:
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
# PROMPT
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
- Monthly history exact

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
monthly_history

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
                "role": "user",

                "content": [

                    {
                        "type": "text",
                        "text": PROMPT
                    },

                    {
                        "type": "image_url",

                        "image_url": f"data:image/jpeg;base64,{base64_image}"
                    }
                ]
            }
        ],

        response_format={
            "type": "json_object"
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
                "role": "user",

                "content": [

                    {
                        "type": "text",
                        "text": PROMPT
                    },

                    {
                        "type": "image_url",

                        "image_url": {
                            "url": f"data:image/jpeg;base64,{base64_image}"
                        }
                    }
                ]
            }
        ],

        response_format={
            "type": "json_object"
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
# MERGE LOGIC
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

        # Exact match
        if str(m_val).strip() == str(l_val).strip():

            final[field] = m_val

        else:

            # Prefer better value
            final[field] = choose_best(
                m_val,
                l_val
            )

    # Monthly history
    m_history = mistral_data.get(
        "monthly_history",
        []
    )

    l_history = llama_data.get(
        "monthly_history",
        []
    )

    final["monthly_history"] = clean_history(
        m_history if len(m_history) >= len(l_history)
        else l_history
    )

    # Validation
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

    print(
        json.dumps(
            final,
            indent=2,
            ensure_ascii=False
        )
    )

    return final