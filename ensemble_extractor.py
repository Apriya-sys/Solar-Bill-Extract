import os
import base64
import json
import re
from mistralai import Mistral
from groq import Groq
from dotenv import load_dotenv

load_dotenv()

def encode_image(image_path):
    """Encodes an image file to base64."""
    with open(image_path, "rb") as image_file:
        return base64.b64encode(image_file.read()).decode('utf-8')

def extract_with_ensemble(image_path, mistral_key=None, groq_key=None):
    """
    Ensemble extraction:
    1. Mistral OCR -> Markdown
    2. Groq (Llama 3) -> JSON
    """
    m_key = mistral_key or os.environ.get("MISTRAL_API_KEY")
    g_key = groq_key or os.environ.get("GROQ_API_KEY")
    
    if not m_key:
        return {"error": "Mistral API Key missing."}
    if not g_key:
        return {"error": "Groq API Key missing (for Llama parsing)."}

    m_client = Mistral(api_key=m_key)
    g_client = Groq(api_key=g_key)
    
    try:
        # Step 1: Mistral OCR
        # We'll use Mistral OCR process for high-fidelity extraction
        # Note: Mistral OCR expects a URL or a bytes object.
        # For local files, we'll use base64 or upload if needed.
        # Mistral OCR process can handle images.
        
        # Actually, Mistral OCR is best used via its OCR API
        # but Pixtral is also very good.
        # Let's use Mistral OCR Process for best text.
        
        # We need to upload the file to Mistral or provide a public URL.
        # Mistral OCR API supports local file processing via base64 in some SDK versions, 
        # but let's use the Chat Vision approach as a robust alternative if OCR process is restricted.
        
        # IMPROVED: Use Mistral OCR if possible, else Pixtral Vision.
        # For now, let's use the Chat Vision to get the Markdown.
        
        base64_image = encode_image(image_path)
        
        ocr_prompt = "Perform high-fidelity OCR on this document. Extract all text, maintaining the layout and tabular structures. This is an electricity bill; ensure all numbers and dates are captured clearly. Return the result in Markdown."
        
        ocr_response = m_client.chat.complete(
            model="pixtral-12b-2409",
            messages=[
                {
                    "role": "user",
                    "content": [
                        {"type": "text", "text": ocr_prompt},
                        {"type": "image_url", "image_url": f"data:image/jpeg;base64,{base64_image}"}
                    ]
                }
            ]
        )
        
        markdown_text = ocr_response.choices[0].message.content
        
        # Step 2: Llama Parsing (Groq)
        parsing_prompt = f"""
        You are a Universal Bill Parser. Below is the OCR text of an electricity bill in Markdown format.
        Your goal is to extract the billing data into a structured JSON format, regardless of the bill's specific layout or utility provider.
        
        ### EXTRACTION RULES:
        1. **Consumer Info**: Look for 'Consumer No', 'Account No', 'Service No', or 'CA No'. Map it to 'consumer_number'.
        2. **Dates**: Find the Bill Date and Due Date. Use format DD-MM-YYYY.
        3. **Readings**: Identify Current Reading, Previous Reading, and total Units Consumed.
        4. **Amounts**: Extract the net Bill Amount and the amount payable After Due Date (Late Amount).
        5. **Meter Info**: Find the Meter Number and Sanctioned Load (kW).
        6. **Monthly History**: If there is a table or list of previous months and units, extract as many as possible (at least 6-12 months).
        
        ### REQUIRED JSON FORMAT:
        {{
            "consumer_name": "...",
            "consumer_number": "...",
            "meter_number": "...",
            "fixed_charges": "...",
            "load_kw": "...",
            "tariff": "...",
            "bill_date": "...",
            "due_date": "...",
            "bill_amount": "...",
            "late_amount": "...",
            "current_reading": "...",
            "previous_reading": "...",
            "units": "...",
            "monthly_history": [
                {{"month": "MMM YY", "units": 123}},
                ...
            ]
        }}
        
        OCR TEXT:
        {markdown_text}
        
        Return ONLY the JSON object.
        """

        
        llama_response = g_client.chat.completions.create(
            model="llama-3.1-70b-versatile",
            messages=[{"role": "user", "content": parsing_prompt}],
            response_format={"type": "json_object"}
        )
        
        json_content = llama_response.choices[0].message.content
        return json.loads(json_content)

    except Exception as e:
        return {"error": f"Ensemble Error: {str(e)}"}
