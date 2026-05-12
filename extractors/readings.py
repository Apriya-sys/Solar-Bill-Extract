import re

def extract_reading_info(ocr_text, is_global=False):
    """
    Finds (Current, Previous, Units) triplet where Current - Previous = Units.
    """
    if not ocr_text:
        return {}
    
    # Pre-process: Join numbers split by spaces (e.g. "18 42 9" -> "18429")
    last_text = ""
    processed_text = ocr_text
    while last_text != processed_text:
        last_text = processed_text
        # Only join if it doesn't look like a year joining another number
        processed_text = re.sub(r'\b(?!2024|2025|2026)(\d{1,4})\s+(\d{1,3})\b', r'\1\2', processed_text)

    
    all_nums = re.findall(r'\b\d{1,7}\b', processed_text)
    
    candidates = []



    for i in range(len(all_nums)):
        for j in range(len(all_nums)):
            if i == j: continue
            try:
                n1 = int(all_nums[i]) # Potential Current
                n2 = int(all_nums[j]) # Potential Previous
                
                if n1 > n2 and n1 > 100: # Readings can be low for new meters
                    diff = n1 - n2
                    if 5 < diff < 5000:
                        score = 0
                        if is_global: score -= 20 # Penalty for global scan
                        
                        # Penalize year patterns
                        if any(y in str(n1) for y in ["2024", "2025", "2026"]): score -= 100
                        if any(y in str(n2) for y in ["2024", "2025", "2026"]): score -= 100
                            
                        # Favor results where diff is found in text
                        if str(diff) in all_nums: score += 50
                        
                        # Favor larger cumulative readings
                        if n1 > 5000: score += 20
                        
                        candidates.append((n1, n2, diff, score))
            except: continue
            
    if candidates:
        candidates.sort(key=lambda x: (x[3], x[0]), reverse=True)
        best = candidates[0]
        return {
            "current_reading": str(best[0]),
            "previous_reading": str(best[1]),
            "units": str(best[2])
        }
            
    return {
        "current_reading": "",
        "previous_reading": "",
        "units": ""
    }
