import os
import base64
import json
import re
from mistralai import Mistral

def encode_image(image_path):
    """Encodes an image file to base64."""
    with open(image_path, "rb") as image_file:
        return base64.b64encode(image_file.read()).decode('utf-8')

def extract_with_mistral(image_path, api_key=None):
    """
    Uses Mistral Pixtral to extract structured data from a bill image.
    """
    # Use provided key or fallback to environment variable
    final_api_key = api_key or os.environ.get("MISTRAL_API_KEY")
    
    if not final_api_key:
        return {"error": "Mistral API Key is missing. Please provide it in the sidebar or set MISTRAL_API_KEY env var."}

    client = Mistral(api_key=final_api_key)

    
    try:
        base64_image = encode_image(image_path)
        
        prompt = """
        You are a specialized document extractor for MSEDCL (Maharashtra State Electricity Distribution Co. Ltd.) bills.
        Extract the following fields from the image and return ONLY a valid JSON object.
        
        Required Fields:
        - consumer_name (String)
        - consumer_number (12-digit string starting with 43)
        - meter_number (String)
        - fixed_charges (String, default "130")
        - load_kw (String, e.g. "3.30")
        - tariff (String, e.g. "90/ LT I Res 1-Phase")
        - bill_date (String format DD-MM-YYYY)
        - due_date (String format DD-MM-YYYY)
        - bill_amount (Decimal string)
        - late_amount (Decimal string)
        - current_reading (String)
        - previous_reading (String)
        - units (String, current_reading - previous_reading)
        - monthly_history (List of objects: {"month": "Jan 25", "units": 100})
        
        Instructions:
        1. If a value is not found, use an empty string.
        2. Ensure the JSON is properly formatted.
        3. Do not include any conversation or markdown markers in your response, just the JSON.
        """

        messages = [
            {
                "role": "user",
                "content": [
                    {
                        "type": "text",
                        "text": prompt
                    },
                    {
                        "type": "image_url",
                        "image_url": f"data:image/jpeg;base64,{base64_image}"
                    }
                ]
            }
        ]

        # Using Pixtral 12B for vision tasks
        response = client.chat.complete(
            model="pixtral-12b-2409",
            messages=messages,
            response_format={"type": "json_object"}
        )

        content = response.choices[0].message.content
        data = json.loads(content)
        
        return data

    except Exception as e:
        return {"error": f"Mistral AI Error: {str(e)}"}
