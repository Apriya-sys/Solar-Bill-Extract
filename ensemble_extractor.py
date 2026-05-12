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
        
        ocr_prompt = "Extract all text from this electricity bill exactly. Preserve the tables and structure. Return the output in Markdown format."
        
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
        print("--- Mistral OCR Output (Markdown) ---")
        # print(markdown_text)
        
        # Step 2: Llama Parsing (Groq)
        parsing_prompt = f"""
        You are an expert data parser. Below is the text extracted from an MSEDCL Electricity Bill in Markdown format.
        Parse this text and return ONLY a valid JSON object with these fields:
        
        - consumer_name
        - consumer_number (12 digits)
        - meter_number
        - fixed_charges (usually 130)
        - load_kw (e.g. 3.30)
        - tariff (e.g. 90/ LT I Res 1-Phase)
        - bill_date (DD-MM-YYYY)
        - due_date (DD-MM-YYYY)
        - bill_amount
        - late_amount
        - current_reading
        - previous_reading
        - units
        - monthly_history (List of objects: {{"month": "Jan 25", "units": 100}})
        
        OCR TEXT:
        {markdown_text}
        
        Return ONLY the JSON. No explanations.
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
