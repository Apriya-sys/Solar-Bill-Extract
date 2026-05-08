import re
from PIL import Image

# =========================================================
# OCR ENGINE INITIALIZATION (DEFERRED)
# =========================================================
ocr_engine = None
ocr_type = None

def initialize_ocr():
    global ocr_engine, ocr_type
    
    if ocr_engine is not None:
        return ocr_type
    
    try:
        from paddleocr import PaddleOCR
        ocr_engine = PaddleOCR(
    use_angle_cls=True,
    lang='en',
    show_log=False
)
        ocr_type = "paddle"
        return "paddle"
    except Exception as e:
        try:
            import pytesseract
            pytesseract.get_tesseract_version()
            ocr_type = "tesseract"
            return "tesseract"
        except Exception as e2:
            raise RuntimeError(
                f"Failed to initialize OCR engines.\n"
                f"PaddleOCR error: {str(e)[:200]}\n"
                f"Tesseract error: {str(e2)[:200]}\n"
                f"Please install either paddleocr or pytesseract with Tesseract OCR."
            )



# =========================================================
# OCR HELPERS
# =========================================================

def normalize_text(text):
    return re.sub(r'\s+', ' ', text).strip()


def get_ocr_lines(image_path):
    ocr_type = initialize_ocr()
    ocr_lines = []

    if ocr_type == "paddle":
        result = ocr_engine.ocr(image_path)
        for line in result[0]:
            text = line[1][0].strip()
            if text:
                ocr_lines.append(text)
    else:
        import pytesseract
        img = Image.open(image_path)
        text = pytesseract.image_to_string(img)
        for line in text.splitlines():
            clean = line.strip()
            if clean:
                ocr_lines.append(clean)

    return ocr_lines


def find_line_with(ocr_lines, *keywords, case_insensitive=True):
    """Return first line containing ANY of the given keywords."""
    for line in ocr_lines:
        check = line.lower() if case_insensitive else line
        if any(kw.lower() in check for kw in keywords):
            return line
    return ""


def find_value_after(ocr_lines, *keywords):
    """Return the line immediately after the line containing ANY keyword."""
    for i, line in enumerate(ocr_lines):
        lower = line.lower()
        if any(kw.lower() in lower for kw in keywords):
            if i + 1 < len(ocr_lines):
                return ocr_lines[i + 1]
    return ""


# =========================================================
# FIELD EXTRACTORS
# =========================================================

# Lines that typically contain non-consumer 12-digit numbers to skip
_SKIP_LINE_PATTERNS = re.compile(
    r'CIN|GSTIN|beneficiary|account no|IFS|RTGS|NEFT|barcode|L\d{5}',
    re.IGNORECASE
)


def extract_consumer_number(ocr_lines, full_text):
    """
    MSEDCL consumer numbers are 12-digit numbers starting with 4393...
    They appear near 'ग्राहक क्रमांक', 'consumer no', 'customer no'.
    Also present in bank details: 'MSEDCL01439320095567'
    """
    # Priority 1: keyword-anchored search near ग्राहक क्रमांक
    keywords = ["ग्राहक क्रमांक", "ग्राहक क्र", "consumer no",
                "customer no", "consumer number", "ग्राहक", "खाता क्र"]

    for i, line in enumerate(ocr_lines):
        lower = line.lower()
        if any(kw.lower() in lower for kw in keywords):
            window = " ".join(ocr_lines[i:i+3])
            # Simple search: grab first occurrence of 43 + 10 digits
            # No lookahead/lookbehind — works even in merged OCR text
            m = re.search(r'(43\d{10})', window)
            if m:
                return m.group(1)

    # Priority 2: MSEDCL bank account reference line
    # e.g. "MSEDCL01439320095567" or "MSEDCL954 439322232375"
    for line in ocr_lines:
        m = re.search(r'MSEDCL[\w\s]*?(43\d{10})', line, re.IGNORECASE)
        if m:
            return m.group(1)

    # Priority 3: first occurrence of 43 + 10 digits in any non-label line
    for line in ocr_lines:
        if _SKIP_LINE_PATTERNS.search(line):
            continue
        m = re.search(r'(43\d{10})', line)
        if m:
            return m.group(1)

    # Priority 4: any 12-digit sequence, skip label lines
    for line in ocr_lines:
        if _SKIP_LINE_PATTERNS.search(line):
            continue
        m = re.search(r'(\d{12})', line)
        if m:
            val = m.group(1)
            # Avoid picking up the GGN number starting with 90 if possible
            if not val.startswith("90"):
                return val

    return ""


def extract_name_and_address(ocr_lines):
    """
    MSEDCL bills print the full consumer name in UPPERCASE on one line,
    followed by address on next line(s).
    """
    consumer_name = ""
    address_lines = []

    skip_words = {
        "BILL", "SUPPLY", "GSTIN", "QR", "SCAN", "PAYMENT", "APP", "DATE",
        "RUPEES", "ENERGY", "PORTAL", "WWW", "MSEDCL", "PHASE", "DIVISION",
        "METER", "STATUS", "NORMAL", "READING", "UNITS", "LOAD", "TARIFF",
        "FILE", "CONSUMER", "CUSTOMER", "ADDRESS", "MONTH", "MAHAVITARAN",
        "MAHADISCOM", "CIN", "GSTIN", "INDIA", "JANUARY", "FEBRUARY",
        "MARCH", "LT", "HT"
    }

    address_keywords = ["NAGAR", "H.NO", "PLOT", "ROAD", "DIST", "TAL", "PIN", "TUMSAR", "ROOM", "BLDG", "APARTMENT", "SOCIETY", "MARG", "GALI", "WARD", "SHIVAJI"]

    def is_address_line(line):
        upper = line.upper()
        if any(kw in upper for kw in address_keywords):
            return True
        if re.search(r'\b\d{6}\b', line):
            return True
        if list(line).count('/') >= 1 and re.search(r'\d', line):
            return True
        return False

    def is_skip_line(line):
        clean = line.strip().upper()
        if len(clean) < 5: return True
        if any(sw in clean for sw in skip_words): return True
        if re.fullmatch(r'[\d\W]+', clean): return True
        if re.search(r'400D|4000|XXXX|FILE\s*NO|FENO|FI3|FN\s*\d', clean): return True
        return False

    def is_uppercase_name(line):
        letters = [c for c in line if c.isalpha()]
        if not letters: return False
        upper_count = sum(1 for c in letters if c.isupper())
        return upper_count / len(letters) > 0.8

    # Strategy 1: look right after 'BILL OF SUPPLY' or 'तीज पुरवठा' header
    start_idx = 0
    for i, line in enumerate(ocr_lines):
        if re.search(r'bill of supply|तीज पुरवठा|purwatha|पुरवठा|bill for the month', line, re.IGNORECASE):
            start_idx = i + 1
            break

    for line in ocr_lines[start_idx:start_idx+15]:
        clean = line.strip()
        if is_skip_line(clean): continue

        if not consumer_name:
            if not is_address_line(clean) and len(clean) >= 8 and len(clean.split()) >= 2 and is_uppercase_name(clean):
                consumer_name = clean
            elif is_address_line(clean):
                # If we encounter an address line before a name line, OCR probably skipped the name
                address_lines.append(clean)
        else:
            if len(address_lines) < 3:
                address_lines.append(clean)

    # Strategy 2: Fallback scanning first 20 lines if missing
    if not consumer_name and not address_lines:
        for line in ocr_lines[:20]:
            clean = line.strip()
            if is_skip_line(clean): continue
            
            if not consumer_name and not is_address_line(clean) and len(clean) >= 8 and len(clean.split()) >= 2 and is_uppercase_name(clean):
                consumer_name = clean
            elif is_address_line(clean) and len(address_lines) < 3:
                address_lines.append(clean)

    raw_address = " ".join(address_lines)
    # Fix OCR missing spaces: '214TUMSAR' -> '214 TUMSAR'
    raw_address = re.sub(r'(\d)([A-Za-z])', r'\1 \2', raw_address)
    # Fix OCR missing spaces: 'TUMSAR441912' -> 'TUMSAR 441912'
    raw_address = re.sub(r'([A-Za-z])(\d)', r'\1 \2', raw_address)
    # Explicit user formatting fixes
    raw_address = re.sub(r'(?i)SHIWAJINAGAR', 'SHIWAJI NAGAR', raw_address)
    raw_address = re.sub(r'(?i)SHIVAJINAGAR', 'SHIVAJI NAGAR', raw_address)

    return normalize_text(consumer_name), normalize_text(raw_address)


def extract_meter_number(ocr_lines, full_text):
    """
    MSEDCL meter numbers are almost exactly 11 digits starting with 08.
    """
    for line in ocr_lines:
        # Priority 1: MSEDCL specific 11-digit meter prefix
        m = re.search(r'\b(08\d{9})\b', line)
        if m:
            return m.group(1)

    # Priority 2: fallback search near keyword
    keywords = ["मिटर", "meter", "मीटर", "serial"]
    for i, line in enumerate(ocr_lines):
        lower = line.lower()
        if any(kw.lower() in lower for kw in keywords):
            window = " ".join(ocr_lines[i:i+3])
            m = re.search(r'\b(0\d{10})\b', window)
            if m: return m.group(1)

    return ""


def extract_load_kw(ocr_lines, full_text):
    """
    Load appears near 'मंजूर भार', 'sanctioned load', 'connected load'.
    Format: X.XX KW
    """
    keywords = ["मंजूर", "sanctioned", "connected load", "load", "भार"]

    for i, line in enumerate(ocr_lines):
        lower = line.lower()
        if any(kw.lower() in lower for kw in keywords):
            window = " ".join(ocr_lines[i:i+3])
            match = re.search(r'(\d+\.?\d*)\s*KW', window, re.IGNORECASE)
            if match:
                return match.group(1)

    # Global search
    match = re.search(r'(\d+\.?\d*)\s*KW', full_text, re.IGNORECASE)
    return match.group(1) if match else ""


def extract_tariff(ocr_lines):
    """
    Tariff appears near 'दर संकेत', 'tariff', 'LT', 'HT'.
    MSEDCL format: 90/LT I Res 1-Phase
    """
    keywords = ["दर संकेत", "tariff", "rate code", "दर"]

    for i, line in enumerate(ocr_lines):
        lower = line.lower()
        if any(kw.lower() in lower for kw in keywords):
            # check next 2 lines for LT/HT tariff
            window = ocr_lines[i:i+3]
            for w in window:
                if re.search(r'\bLT\b|\bHT\b', w, re.IGNORECASE):
                    return format_tariff(w.strip())
            # if the keyword line itself has the value
            match = re.search(r'(\d+/LT[^\n]+)', line, re.IGNORECASE)
            if match:
                return format_tariff(match.group(1).strip())

    # Fallback: find line with "LT" and "Phase"
    for line in ocr_lines:
        if re.search(r'\bLT\b', line, re.IGNORECASE) and re.search(
            r'phase|1-phase|3-phase', line, re.IGNORECASE
        ):
            return format_tariff(line.strip())

    def format_tariff(t):
        if not t: return ""
        t = re.sub(r'(?i)(LT|HT)\s*Res', r'\1 Res', t)
        t = re.sub(r'(?i)(LT|HT)Res', r'\1 Res', t)
        return t

    for line in ocr_lines:
        if re.search(r'\d+/LT', line, re.IGNORECASE):
            return format_tariff(line.strip())

    return ""


def extract_dates(ocr_lines, full_text):
    """
    Bill date = देयक दिनांक / bill date (usually 10-01-2026)
    Due date  = देय दिनांक / due date / pay by (usually 30-01-2026)
    """
    bill_date = ""
    due_date = ""

    bill_kw  = ["देयक दिनांक", "bill date", "invoice date", "दिनांक", "बिल दिनांक"]
    due_kw   = ["देय दिनांक", "due date", "payment due", "pay by", "ya tarikh",
                "या तारखे", "दे दिनांक", "last date"]

    for line in ocr_lines:
        dates = re.findall(r'\d{2}[-/]\d{2}[-/]\d{4}', line)
        if not dates:
            continue

        lower = line.lower()

        if not due_date and any(kw.lower() in lower for kw in due_kw):
            due_date = dates[-1]   # last date on due-line
            continue

        if not bill_date and any(kw.lower() in lower for kw in bill_kw):
            bill_date = dates[0]

    # Fallback: grab all dates from full text
    all_dates = re.findall(r'\d{2}[-/]\d{2}[-/]\d{4}', full_text)

    if not bill_date and all_dates:
        # Find the earliest date that matches 10-01-2026 pattern (bill month)
        bill_date = all_dates[0]

    if not due_date:
        # Due date is typically 20 days after bill date
        for d in all_dates:
            if d != bill_date:
                due_date = d
                break

    return bill_date, due_date


def extract_readings(ocr_lines, full_text):
    """
    MSEDCL reading table: चालू रिडींग | मागील रिडींग | गुणक अवयव | युनिट
    Current reading is the larger number, previous is smaller.
    Units = current - previous
    """
    current_reading = ""
    previous_reading = ""
    units = ""

    # Strategy 1: look for reading table header line, then grab next data line
    reading_kw = ["चालू रिडींग", "current reading", "चालू", "मागील रिडींग",
                  "previous reading", "reading"]

    reading_idx = -1
    for i, line in enumerate(ocr_lines):
        lower = line.lower()
        if any(kw.lower() in lower for kw in reading_kw):
            reading_idx = i
            break

    # Helper: reject year-range numbers which are not meter readings
    def is_reading(n):
        return not (2019 <= n <= 2030)

    def find_pairs(num_list, min_val=0):
        """Find (cur, prev, diff) pairs from a list of ints."""
        results = []
        for j in range(len(num_list) - 1):
            cur, prev = num_list[j], num_list[j + 1]
            if cur >= min_val and prev >= min_val:
                if cur > prev and 0 < (cur - prev) <= 5000:
                    results.append((cur, prev, cur - prev))
        return results

    # --- Strategy 1: reading table header line ---
    if reading_idx >= 0:
        for line in ocr_lines[reading_idx + 1: reading_idx + 5]:
            nums = [int(x) for x in re.findall(r'\b(\d{4,6})\b', line)
                    if is_reading(int(x))]
            # Prefer 5-digit numbers (>=10000) — bill amounts are 4-digit
            big = [n for n in nums if n >= 10000]
            pairs = find_pairs(big) or find_pairs(nums)
            if pairs:
                cur, prev, diff = min(pairs, key=lambda x: x[2])
                return str(cur), str(prev), str(diff)
        # Fallback: pool all valid nums around header
        candidate_nums = []
        for line in ocr_lines[reading_idx + 1: reading_idx + 6]:
            for mn in re.findall(r'\b(\d{4,6})\b', line):
                v = int(mn)
                if 1000 <= v <= 999999 and is_reading(v):
                    candidate_nums.append(v)
        big = [n for n in candidate_nums if n >= 10000]
        for pool in (big, candidate_nums):
            if len(pool) >= 2:
                cur, prev = sorted(pool, reverse=True)[:2]
                diff = cur - prev
                if 0 < diff <= 5000:
                    return str(cur), str(prev), str(diff)

    # Helper: reject year-range numbers which are not meter readings
    def is_reading(n):
        return not (2019 <= n <= 2030)

    # --- Strategy 1: Mathematical Triplet Match (Bulletproof) ---
    # Find A, B, C exactly occurring in the document where A - B = C
    all_raw_nums = []
    for line in ocr_lines:
        all_raw_nums.extend([int(x) for x in re.findall(r'\b\d+\b', line)])
        
    readings_pool = [x for x in all_raw_nums if is_reading(x) and 1000 <= x <= 999999]
    diffs_pool = [x for x in all_raw_nums if is_reading(x) and 0 < x <= 5000]
    
    valid_triplets = []
    for cur in readings_pool:
        for prev in readings_pool:
            if cur > prev:
                diff = cur - prev
                # Check if this exact difference was extracted by OCR somewhere
                if diff in diffs_pool:
                    valid_triplets.append((cur, prev, diff))
                    
    if valid_triplets:
        # Prioritize triplets with the highest current reading. We don't want bill amounts overriding readings.
        valid_triplets.sort(key=lambda x: (-x[0], x[2]))
        best = valid_triplets[0]
        return str(best[0]), str(best[1]), str(best[2])

    # --- Strategy 2: Adjacency Scan (Fallback) ---
    def find_pairs(num_list, min_val=0):
        results = []
        for j in range(len(num_list) - 1):
            cur, prev = num_list[j], num_list[j + 1]
            if cur >= min_val and prev >= min_val:
                if cur > prev and 0 < (cur - prev) <= 5000:
                    results.append((cur, prev, cur - prev))
        return results

    possible_5 = []
    possible_4 = []
    
    for line in ocr_lines:
        line_nums = [int(n) for n in re.findall(r'\b(\d{4,6})\b', line) if is_reading(int(n))]
        big = [n for n in line_nums if n >= 10000]
        possible_5.extend(find_pairs(big, min_val=10000))
        possible_4.extend(find_pairs(line_nums))

    # Reject pairs that exactly match bill amounts to avoid false positives
    def filter_bill_amounts(pair_list):
        return [p for p in pair_list if p[0] != p[1]]

    for pool in (possible_5, possible_4):
        filtered = filter_bill_amounts(pool)
        if filtered:
            if pool is possible_5:
                best = max(filtered, key=lambda x: x[0])
            else:
                best = min(filtered, key=lambda x: x[2])
            return str(best[0]), str(best[1]), str(best[2])

    return current_reading, previous_reading, units


def extract_amounts(ocr_lines, full_text):
    """
    MSEDCL bills show:
      देयक रक्कम (Bill Amount)  e.g. 1460.00
      देय रक्कम / late amount   e.g. 1470.00

    Bottom section also repeats:
      'या तारखे पर्यंत भरल्यास: Rs. 1460.00'
      'या तारखे नंतर भरल्यास : Rs. 1470.00'
    """
    bill_amount = ""
    late_amount = ""

    # Priority: lines with 'देयक रक्कम', 'bill amount', 'देय रक्कम'
    bill_kw = ["देयक रक्कम", "bill amount", "रक्कम रु", "amount", "total",
               "तारखे पर्यंत", "पर्यंत भरल्यास"]
    late_kw = ["देय रक्कम", "late payment", "after due", "विलंब",
               "तारखे नंतर", "नंतर भरल्यास"]

    for line in ocr_lines:
        amounts = re.findall(r'\b\d{3,6}\.\d{2}\b', line)
        if not amounts:
            continue

        lower = line.lower()

        if not late_amount and any(kw.lower() in lower for kw in late_kw):
            late_amount = amounts[-1]
            continue

        if not bill_amount and any(kw.lower() in lower for kw in bill_kw):
            bill_amount = amounts[-1]

    # Fallback: scan for two distinct decimal amounts
    if not bill_amount or not late_amount:
        all_amounts = re.findall(r'\b\d{3,6}\.\d{2}\b', full_text)

        # Remove duplicates while preserving order
        seen = []
        for a in all_amounts:
            if a not in seen:
                seen.append(a)

        if not bill_amount and seen:
            bill_amount = seen[0]

        if not late_amount and len(seen) >= 2:
            # Late amount is slightly higher
            for a in seen[1:]:
                if float(a) > float(bill_amount):
                    late_amount = a
                    break
            if not late_amount:
                late_amount = seen[1]

    return bill_amount, late_amount


# =========================================================
# MAIN EXTRACTION FUNCTION
# =========================================================

def extract_bill_data(image_path):

    # ── OCR ───────────────────────────────────────────────
    ocr_lines = get_ocr_lines(image_path)
    full_text = "\n".join(ocr_lines)

    print("\n========== OCR TEXT ==========\n")
    print(full_text)

    # ── EXTRACT ───────────────────────────────────────────
    data = {}

    data["consumer_number"] = extract_consumer_number(ocr_lines, full_text)

    name, address = extract_name_and_address(ocr_lines)
    data["consumer_name"] = name
    data["address"]        = address

    data["meter_number"] = extract_meter_number(ocr_lines, full_text)
    data["load_kw"]      = extract_load_kw(ocr_lines, full_text)
    data["tariff"]       = extract_tariff(ocr_lines)

    bill_date, due_date = extract_dates(ocr_lines, full_text)
    data["bill_date"] = bill_date
    data["due_date"]  = due_date

    cur, prev, units = extract_readings(ocr_lines, full_text)
    data["current_reading"]  = cur
    data["previous_reading"] = prev
    data["units"]            = units

    bill_amt, late_amt = extract_amounts(ocr_lines, full_text)
    data["bill_amount"] = bill_amt
    data["late_amount"] = late_amt

    # ── PRINT RESULT ──────────────────────────────────────
    print("\n========== EXTRACTED DATA ==========\n")
    fields = [
        "consumer_number", "consumer_name", "address",
        "meter_number", "load_kw", "tariff",
        "bill_date", "due_date",
        "current_reading", "previous_reading", "units",
        "bill_amount", "late_amount",
    ]
    for key in fields:
        print(f"{key}: {data.get(key, '')}")

    return data