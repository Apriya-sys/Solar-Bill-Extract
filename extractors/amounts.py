from regex_extractors import get_amounts_with_labels

def extract_amount_info(ocr_text):
    """
    Extracts bill and late amounts.
    """
    bill_amount, late_amount = get_amounts_with_labels(ocr_text)
    return {
        "bill_amount": bill_amount,
        "late_amount": late_amount
    }

