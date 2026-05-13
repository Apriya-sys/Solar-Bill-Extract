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

    # denoise

    gray = cv2.fastNlMeansDenoising(gray)

    # blur

    gray = cv2.GaussianBlur(
        gray,
        (3, 3),
        0
    )

    # adaptive threshold better for Hindi bills

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

        "jan": "January",
        "feb": "February",
        "mar": "March",
        "apr": "April",
        "jun": "June",
        "jul": "July",
        "aug": "August",
        "sep": "September",
        "oct": "October",
        "nov": "November",
        "dec": "December",
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

    valid_months = [
        "January",
        "February",
        "March",
        "April",
        "May",
        "June",
        "July",
        "August",
        "September",
        "October",
        "November",
        "December"
    ]

    month_order = {
        "january": 1,
        "february": 2,
        "march": 3,
        "april": 4,
        "may": 5,
        "june": 6,
        "july": 7,
        "august": 8,
        "september": 9,
        "october": 10,
        "november": 11,
        "december": 12
    }

    for item in history:

        # -----------------------------
        # CLEAN MONTH
        # -----------------------------

        month = normalize_month(
            item.get("month", "")
        )

        month = (
            str(month)
            .replace("-", " ")
            .replace("_", " ")
            .replace("  ", " ")
            .strip()
        )

        # -----------------------------
        # CLEAN UNITS
        # -----------------------------

        units = str(
            item.get("units", "")
        )

        units = re.sub(
            r"[^\d]",
            "",
            units
        )

        if units == "":
            continue

        try:

            units_int = int(units)

        except:
            continue

        # realistic electricity range

        if units_int < 0 or units_int > 500:
            continue

        # -----------------------------
        # VALID MONTH CHECK
        # -----------------------------

        valid = False

        month_name = ""

        for m in valid_months:

            if m.lower() in month.lower():

                valid = True
                month_name = m
                break

        if not valid:
            continue

        # -----------------------------
        # YEAR EXTRACTION
        # -----------------------------

        year_match = re.findall(
            r"20\d{2}",
            month
        )

        if year_match:

            year = year_match[0]

        else:

            year = "2025"

        final_month = f"{month_name} {year}"

        # -----------------------------
        # REMOVE DUPLICATES
        # -----------------------------

        key = final_month.lower().strip()

        if key in seen:
            continue

        seen.add(key)

        cleaned.append({

            "month": final_month,

            "units": units_int
        })

    # -------------------------------------------------
    # SORT MONTHS
    # -------------------------------------------------

    try:

        cleaned.sort(
            key=lambda x: (
                int(
                    re.findall(
                        r"20\d{2}",
                        x["month"]
                    )[0]
                ),
                month_order[
                    x["month"].split()[0].lower()
                ]
            )
        )

    except:
        pass

    print("\n================ CLEANED MONTH HISTORY ================\n")

    print(cleaned)

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

    g_client = Groq(api_key=g_key)

    try:

        # preprocess

        cleaned_image = preprocess_image(
            image_path
        )

        # encode image

        base64_image = encode_image(
            cleaned_image
        )

        # -------------------------------------------------
        # PROMPT
        # -------------------------------------------------

        parsing_prompt = """
You are an expert OCR extraction engine for Maharashtra MSEDCL electricity bills.

Bills may contain:
- Hindi
- Marathi
- English

Extract ONLY exact values.

IMPORTANT:
- Return ONLY valid JSON
- No markdown
- No explanation
- Missing values = ""

Extract:

1. consumer_name
2. consumer_number
3. meter_number
4. contract_demand
5. fixed_charges
6. load_kw
7. tariff
8. bill_date
9. due_date
10. bill_amount
11. late_amount
12. current_reading
13. previous_reading
14. units
15. monthly_history

MONTH RULES:

These electricity bills contain monthly usage history near graph bars.

Extract ALL visible month + unit pairs carefully.

IMPORTANT:
- Units are usually between 0 and 500
- Ignore graph axis labels like 100, 200, 300
- Ignore bill amounts
- Ignore meter readings
- Ignore duplicate OCR numbers

Convert Marathi/Hindi months:

जानेवारी = January
फेब्रुवारी = February
मार्च = March
एप्रिल = April
मे = May
जून = June
जुलै = July
ऑगस्ट = August
सप्टेंबर = September
ऑक्टोबर = October
नोव्हेंबर = November
डिसेंबर = December

Return month names EXACTLY like:

February 2025
March 2025
April 2025

JSON FORMAT:

{
    "consumer_name":"",
    "consumer_number":"",
    "meter_number":"",
    "contract_demand":"",
    "fixed_charges":"",
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

        # -------------------------------------------------
        # GROQ REQUEST
        # -------------------------------------------------

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

        print("\n================ JSON OUTPUT ================\n")

        print(json_content)

        data = json.loads(json_content)

        # -------------------------------------------------
        # CLEANUPS
        # -------------------------------------------------

        data["consumer_number"] = clean_consumer_number(
            data.get("consumer_number", "")
        )

        data["load_kw"] = clean_load(
            data.get("load_kw", "")
        )

        data["tariff"] = "90/LT I Res 1-Phase"

        data["contract_demand"] = ""

        history = data.get(
            "monthly_history",
            []
        )

        data["monthly_history"] = clean_month_history(
            history
        )

        return data

    except Exception as e:

        print("\n================ ERROR ================\n")

        print(str(e))

        return {
            "error": f"Ensemble Error: {str(e)}"
        }