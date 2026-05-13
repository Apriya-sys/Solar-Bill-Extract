# ================================
# ensemble_extractor.py
# ================================

import os
import re
import json
import cv2
import base64

from groq import Groq
from dotenv import load_dotenv

load_dotenv()


# -------------------------------------------------
# IMAGE ENCODER
# -------------------------------------------------

def encode_image(image_path):

    with open(image_path, "rb") as image_file:

        return base64.b64encode(
            image_file.read()
        ).decode("utf-8")


# -------------------------------------------------
# IMAGE PREPROCESSING
# -------------------------------------------------

def preprocess_image(image_path):

    img = cv2.imread(image_path)

    gray = cv2.cvtColor(
        img,
        cv2.COLOR_BGR2GRAY
    )

    gray = cv2.fastNlMeansDenoising(gray)

    gray = cv2.GaussianBlur(
        gray,
        (3, 3),
        0
    )

    thresh = cv2.adaptiveThreshold(
        gray,
        255,
        cv2.ADAPTIVE_THRESH_GAUSSIAN_C,
        cv2.THRESH_BINARY,
        11,
        2
    )

    cleaned_path = "cleaned_bill.jpg"

    cv2.imwrite(
        cleaned_path,
        thresh
    )

    return cleaned_path


# -------------------------------------------------
# NORMALIZE MONTH
# -------------------------------------------------

def normalize_month(month_text):

    month_text = str(month_text)

    mapping = {

        "जानेवारी": "January",
        "फेब्रुवारी": "February",
        "मार्च": "March",
        "एप्रिल": "April",
        "मे": "May",
        "जून": "June",
        "जुलै": "July",
        "ऑगस्ट": "August",
        "सप्टेंबर": "September",
        "ऑक्टोबर": "October",
        "नोव्हेंबर": "November",
        "डिसेंबर": "December",
    }

    lower = month_text.lower()

    for k, v in mapping.items():

        if k.lower() in lower:

            year = re.findall(
                r"20\d{2}",
                month_text
            )

            if year:

                return f"{v} {year[0]}"

            return v

    return month_text.strip()


# -------------------------------------------------
# CLEAN MONTH HISTORY
# -------------------------------------------------

def clean_month_history(history):

    cleaned = []

    seen = set()

    for item in history:

        month = normalize_month(
            item.get("month", "")
        )

        units = str(
            item.get("units", "")
        )

        units = re.sub(
            r"\D",
            "",
            units
        )

        if units == "":
            continue

        try:

            units_int = int(units)

        except:
            continue

        if units_int < 0 or units_int > 500:
            continue

        key = month.lower().strip()

        if key in seen:
            continue

        seen.add(key)

        cleaned.append({

            "month": month,

            "units": units_int
        })

    return cleaned


# -------------------------------------------------
# CLEAN CONSUMER NUMBER
# -------------------------------------------------

def clean_consumer_number(number):

    number = re.sub(
        r"\D",
        "",
        str(number)
    )

    if len(number) == 10:

        number = "43" + number

    elif len(number) == 11:

        if not number.startswith("43"):

            number = "4" + number

    return number


# -------------------------------------------------
# CLEAN LOAD
# -------------------------------------------------

def clean_load(load_kw):

    load_kw = str(load_kw)

    load_kw = (
        load_kw
        .replace("KWKW", "KW")
        .replace(" ", "")
        .upper()
    )

    match = re.search(
        r"(\d+(\.\d+)?)",
        load_kw
    )

    if match:

        return match.group(1)

    return ""


# -------------------------------------------------
# MAIN EXTRACTION
# -------------------------------------------------

def extract_with_ensemble(
    image_path,
    mistral_key=None,
    groq_key=None
):

    g_key = groq_key or os.environ.get(
        "GROQ_API_KEY"
    )

    if not g_key:

        return {
            "error": "Groq API Key missing."
        }

    try:

        print("\n========== USING GROQ ==========\n")

        cleaned_image = preprocess_image(
            image_path
        )

        base64_image = encode_image(
            cleaned_image
        )

        g_client = Groq(api_key=g_key)

        parsing_prompt = """
Extract exact JSON from Maharashtra MSEDCL electricity bill.

Return ONLY JSON.

Fields:

consumer_name
consumer_number
meter_number
contract_demand
fixed_charges
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

Extract all visible month + units correctly.

IMPORTANT:
- Ignore graph labels like 100 200 300
- Units are between 0 and 500
- Extract ALL months carefully
- Preserve exact values
"""

        response = g_client.chat.completions.create(

            model="meta-llama/llama-4-scout-17b-16e-instruct",

            messages=[

                {
                    "role": "user",

                    "content": [

                        {
                            "type": "text",
                            "text": parsing_prompt
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

        json_content = (
            response
            .choices[0]
            .message
            .content
        )

        print("\n========== RAW JSON ==========\n")

        print(json_content)

        data = json.loads(
            json_content
        )

        # -------------------------------------------------
        # CLEANUPS
        # -------------------------------------------------

        data["consumer_number"] = clean_consumer_number(
            data.get("consumer_number", "")
        )

        data["load_kw"] = clean_load(
            data.get("load_kw", "")
        )

        history = data.get(
            "monthly_history",
            []
        )

        data["monthly_history"] = clean_month_history(
            history
        )

        return data

    except Exception as e:

        print("\n========== ERROR ==========\n")

        print(str(e))

        return {
            "error": str(e)
        }