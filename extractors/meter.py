from regex_extractors import get_meter_number, get_load_kw, get_tariff

def extract_meter_info(ocr_text):
    """
    Extracts meter number, load, and tariff from OCR text.
    """
    return {
        "meter_number": get_meter_number(ocr_text),
        "load_kw": get_load_kw(ocr_text),
        "tariff": get_tariff(ocr_text)
    }
