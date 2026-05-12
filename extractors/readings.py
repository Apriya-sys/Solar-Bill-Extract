import re

def extract_reading_info(ocr_text):
    """
    Extracts current, previous readings and units.
    """
    # Pre-process: Join numbers split by a single space (e.g. "1842 9" -> "18429")
    # Only if it forms a 4-6 digit number
    ocr_text = re.sub(r'\b(\d{1,4})\s+(\d{1,3})\b', lambda m: m.group(1)+m.group(2) if 4 <= len(m.group(1)+m.group(2)) <= 6 else m.group(0), ocr_text)
    
    lines = [line.strip() for line in ocr_text.split('\n') if line.strip()]

    
    current = ""
    previous = ""
    units = ""
    
    # MSEDCL reading table labels
    # Strategy: find lines with many numbers or specific keywords
    # Pre-process: Join numbers split by a single space (e.g. "1842 9" -> "18429")
    # Only if it forms a 4-6 digit number or 2-3 digit units
    processed_text = re.sub(r'\b(\d{1,4})\s+(\d{1,3})\b', lambda m: m.group(1)+m.group(2) if 2 <= len(m.group(1)+m.group(2)) <= 6 else m.group(0), ocr_text)
    
    all_nums = re.findall(r'\b\d{1,6}\b', processed_text)
    
    candidates = []
    # Keywords to search for proximity
    reading_keywords = ["चालू", "मागील", "Current", "Previous", "Units", "युनिट", "वापर"]
    
    for i in range(len(all_nums)):
        for j in range(len(all_nums)):
            if i == j: continue
            try:
                n1 = int(all_nums[i]) # Potential Current
                n2 = int(all_nums[j]) # Potential Previous
                
                if n1 > n2 and n1 > 1000:
                    diff = n1 - n2
                    if 5 < diff < 2000: # Realistic monthly units
                        score = 0
                        # Check if diff exists in the text
                        if str(diff) in all_nums: score += 20
                        
                        # Check proximity to keywords
                        for kw in reading_keywords:
                            if kw.lower() in ocr_text.lower():
                                # Very basic proximity: is it in the same text block?
                                score += 5
                        
                        # Penalize years
                        if n1 in [2024, 2025, 2026] or n2 in [2024, 2025, 2026]:
                            score -= 50
                            
                        # Favor larger readings (cumulative meters)
                        if n1 > 5000: score += 10
                        
                        candidates.append((n1, n2, diff, score))
            except: continue
            
    if candidates:
        # Sort by score descending, then by current reading descending
        candidates.sort(key=lambda x: (x[3], x[0]), reverse=True)
        best = candidates[0]
        # Only return if score is decent
        if best[3] > 0:
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

