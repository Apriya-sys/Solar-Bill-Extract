import os
import base64
import json
import cv2

try:
    from mistralai import Mistral
except ImportError:
    from mistralai.client import Mistral

from groq import Groq
from dotenv import load_dotenv

load_dotenv()


# -------------------------------------------------
# IMAGE ENCODER
# -------------------------------------------------

def encode_image(image_path):
    """
    Encodes image to base64
    """
    with open(image_path, "rb") as image_file:
        return base64.b64encode(
            image_file.read()
        ).decode("utf-8")


# -------------------------------------------------
# IMAGE PREPROCESSING
# -------------------------------------------------

def preprocess_image(image_path):
    """
    Clean bill image for better OCR
    """

    img = cv2.imread(image_path)

    # grayscale
    gray = cv2.cvtColor(
        img,
        cv2.COLOR_BGR2GRAY
    )

    # denoise
    gray = cv2.GaussianBlur(
        gray,
        (3, 3),
        0
    )

    # threshold
    thresh = cv2.threshold(
        gray,
        150,
        255,
        cv2.THRESH_BINARY
    )[1]

    cleaned_path = "cleaned_bill.jpg"

    cv2.imwrite(
        cleaned_path,
        thresh
    )

    return cleaned_path


# -------------------------------------------------
# MAIN EXTRACTION
# -------------------------------------------------

def extract_with_ensemble(
    image_path,
    mistral_key=None,
    groq_key=None
):

    """
    Ensemble extraction:
    1. OpenCV preprocessing
    2. Mistral OCR
    3. Llama JSON parsing
    """

    # -------------------------------------------------
    # API KEYS
    # -------------------------------------------------

    m_key = mistral_key or os.environ.get(
        "MISTRAL_API_KEY"
    )

    g_key = groq_key or os.environ.get(
        "GROQ_API_KEY"
    )

    if not m_key:
        return {
            "error": "Mistral API Key missing."
        }

    if not g_key:
        return {
            "error": "Groq API Key missing."
        }

    # -------------------------------------------------
    # CLIENTS
    # -------------------------------------------------

    m_client = Mistral(api_key=m_key)

    g_client = Groq(api_key=g_key)

    try:

        # -------------------------------------------------
        # STEP 1 : PREPROCESS IMAGE
        # -------------------------------------------------

        cleaned_image = preprocess_image(
            image_path
        )

        # -------------------------------------------------
        # STEP 2 : ENCODE IMAGE
        # -------------------------------------------------

        base64_image = encode_image(
            cleaned_image
        )

        # -------------------------------------------------
        # STEP 3 : OCR PROMPT
        # -------------------------------------------------

        ocr_prompt = """
        Perform high-quality OCR on this electricity bill.

        Extract:
        - all text
        - tables
        - readings
        - monthly history
        - bill amounts
        - dates

        Maintain structure clearly.

        Return OCR result in Markdown.
        """

        # -------------------------------------------------
        # STEP 4 : MISTRAL OCR
        # -------------------------------------------------

        ocr_response = m_client.chat.complete(

            model="mistral-large-latest",

            messages=[
                {
                    "role": "user",

                    "content": [

                        {
                            "type": "text",
                            "text": ocr_prompt
                        },

                        {
                            "type": "image_url",

                            "image_url": {
                                "url": f"data:image/jpeg;base64,{base64_image}"
                            }
                        }
                    ]
                }
            ]
        )

        markdown_text = (
            ocr_response
            .choices[0]
            .message
            .content
        )

        # -------------------------------------------------
        # DEBUG OCR OUTPUT
        # -------------------------------------------------

        print("\n================ OCR OUTPUT ================\n")

        print(markdown_text)

        # -------------------------------------------------
        # STEP 5 : JSON EXTRACTION PROMPT
        # -------------------------------------------------

        parsing_prompt = f"""
        You are an OCR BILL DATA EXTRACTOR.

        Your ONLY job is to COPY exact visible values from OCR text.

        STRICT RULES:

        - NEVER guess values
        - NEVER calculate values
        - NEVER swap fields
        - NEVER infer missing data
        - ONLY copy EXACT text visible in OCR
        - If value not clearly visible return ""
        - Preserve numbers exactly as shown
        - Preserve month names exactly
        - Preserve reading order exactly

        VERY IMPORTANT:

        - "A50" is NOT meter number
        - "A50" is NOT tariff
        - Meter number is numeric
        - Tariff contains LT/Res/Phase
        - Current reading must be larger than previous reading
        - Units must equal current - previous
        - Monthly history must come ONLY from visible table/graph
        - Do NOT invent monthly history
        - Do NOT create fake months
        - Do NOT modify years

        EXTRACT THESE FIELDS EXACTLY:

        1. consumer_name
        2. consumer_number
        3. meter_number
        4. fixed_charges
        5. load_kw
        6. tariff
        7. bill_date
        8. due_date
        9. bill_amount
        10. late_amount
        11. current_reading
        12. previous_reading
        13. units
        14. monthly_history

        RETURN ONLY VALID JSON.

        JSON FORMAT:

        {{
            "consumer_name":"",
            "consumer_number":"",
            "meter_number":"",
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
                {{
                    "month":"",
                    "units":""
                }}
            ]
        }}

        OCR TEXT:

        {markdown_text}

        """

        # -------------------------------------------------
        # STEP 6 : LLAMA PARSING
        # -------------------------------------------------

        llama_response = g_client.chat.completions.create(

            model="llama-3.3-70b-versatile",

            messages=[
                {
                    "role": "user",
                    "content": parsing_prompt
                }
            ],

            response_format={
                "type": "json_object"
            }
        )

        json_content = (
            llama_response
            .choices[0]
            .message
            .content
        )

        # -------------------------------------------------
        # DEBUG JSON OUTPUT
        # -------------------------------------------------

        print("\n================ JSON OUTPUT ================\n")

        print(json_content)

        # -------------------------------------------------
        # RETURN JSON
        # -------------------------------------------------

        return json.loads(json_content)

    except Exception as e:

        print("\n================ ERROR ================\n")

        print(str(e))

        return {
            "error": f"Ensemble Error: {str(e)}"
        }