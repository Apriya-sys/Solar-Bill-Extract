import re

def extract_with_regex(text, pattern, flags=re.IGNORECASE | re.DOTALL):
    """
    Helper to extract the first match for a pattern in text.
    """
    match = re.search(pattern, text, flags)
    return match.group(1) if match else ""

def extract_all_with_regex(text, pattern, flags=re.IGNORECASE):
    """
    Helper to extract all matches for a pattern in text.
    """
    return re.findall(pattern, text, flags)

# Specialized extractors

def get_consumer_number(text):
    # MSEDCL consumer numbers are 12 digits, often starting with 43.
    # Exclude GGN numbers starting with 90.
    candidates = re.findall(r'\b(\d{12})\b', text)
    valid = [c for c in candidates if not c.startswith("90")]
    
    # Prioritize 43 prefix
    for v in valid:
        if v.startswith("43"): return v
        
    return valid[0] if valid else (candidates[0] if candidates else "")

def get_meter_number(text):
    # MSEDCL meter numbers are 11 digits, usually starting with 08 or 02.
    candidates = re.findall(r'\b(\d{10,11})\b', text)
    # Prioritize 08 or 02 prefix
    for c in candidates:
        if c.startswith("08") or c.startswith("02"):
            return c
    return candidates[0] if candidates else ""
def get_bill_and_due_dates(text):
    # Clean text: remove spaces in dates like "10-01-20 4" or "10 -01- 2026"
    cleaned_text = re.sub(r'(\d{1,2})\s*[-/]\s*(\d{1,2})\s*[-/]\s*(\d{2,4})', r'\1-\2-\3', text)
    # Join split years like "10-01-20 26"
    cleaned_text = re.sub(r'(\d{2}-\d{2}-\d{2})\s+(\d{2})', r'\1\2', cleaned_text)
    
    dates = re.findall(r'\d{2}[-/]\d{2}[-/]\d{2,4}', cleaned_text)

    # Fix dates and filter out future years (only 2024-2026 expected)
    fixed_dates = []
    for d in dates:
        parts = re.split(r'[-/]', d)
        if len(parts) == 3:
            day = parts[0]
            month = parts[1]
            year = parts[2]
            if len(year) == 2:
                year = "20" + year
            elif len(year) > 4:
                year = year[:4]
            
            if 2000 <= int(year) <= 2030:
                fixed_dates.append(f"{day}-{month}-{year}")
            
    if len(fixed_dates) >= 2:
        # Sort by date value
        def parse_d(dt):
            try:
                d, m, y = map(int, dt.split('-'))
                return y * 10000 + m * 100 + d
            except: return 0
            
        sorted_dates = sorted(list(set(fixed_dates)), key=parse_d)
        # Bill date is usually 10th or 15th, Due date is 30th etc.
        # But usually Bill Date is EARLIER than Due Date
        return sorted_dates[0], sorted_dates[-1]
    elif len(fixed_dates) == 1:
        return fixed_dates[0], ""
    return "", ""


def get_amounts_with_labels(text):
    # Pre-process: "3440 00" -> "3440.00", "3450 00" -> "3450.00"
    cleaned_text = re.sub(r'\b(\d{3,6})\s+(\d{2})\b', r'\1.\2', text)
    
    # Priority 1: Search for amounts near labels
    # Use re.findall to get all candidates for a label
    bill_matches = re.findall(r'(?:देयक|रक्कम|bill).*?(\d{3,6}\.\d{2})', cleaned_text, re.IGNORECASE | re.DOTALL)
    late_matches = re.findall(r'(?:देय|नंतर|after|late).*?(\d{3,6}\.\d{2})', cleaned_text, re.IGNORECASE | re.DOTALL)
    
    bill_amt = bill_matches[0] if bill_matches else ""
    late_amt = late_matches[0] if late_matches else ""
    
    # Priority 2: Look for common MSEDCL amount pairs (Late Amt is usually Bill Amt + 10 or 1.25% more)
    if not bill_amt or not late_amt:
        all_matches = re.findall(r'\b\d{3,6}\.\d{2}\b', cleaned_text)
        amounts = sorted([float(a) for a in all_matches], reverse=True)
        # Unique amounts only
        seen = set()
        unique_amounts = [x for x in amounts if not (x in seen or seen.add(x))]
        
        if len(unique_amounts) >= 2:
            # Try to find a pair that fits the late fee pattern
            for i in range(len(unique_amounts)):
                for j in range(len(unique_amounts)):
                    if i == j: continue
                    a1 = unique_amounts[i] # Potentially Late Amt (larger)
                    a2 = unique_amounts[j] # Potentially Bill Amt (smaller)
                    if a1 > a2:
                        diff = a1 - a2
                        if abs(diff - 10) < 2 or (a2 * 0.01 <= diff <= a2 * 0.05):
                            bill_amt = f"{a2:.2f}"
                            late_amt = f"{a1:.2f}"
                            return bill_amt, late_amt
                            
            # If no pair fits pattern, just pick the top two
            late_amt = f"{unique_amounts[0]:.2f}"
            bill_amt = f"{unique_amounts[1]:.2f}"
            return bill_amt, late_amt
        elif len(unique_amounts) == 1:
            return f"{unique_amounts[0]:.2f}", f"{unique_amounts[0]:.2f}"
            
    return "", ""





def get_load_kw(text):

    # Pattern: Digit(s) . Digit(s) KW
    match = re.search(r'(\d+\.?\d*)\s*KW', text, re.IGNORECASE)
    if match:
        val = match.group(1)
        if '.' not in val:
            # If it's something like "330", it's probably "3.30"
            if len(val) >= 2:
                return f"{val[0]}.{val[1:]}"
        return val
    return ""


def get_tariff(text):
    # This might need more complex logic as seen in extract_bill.py
    match = re.search(r'\bLT\b|\bHT\b', text, re.IGNORECASE)
    if match:
        return text.strip()
    return ""
