import re

def extract_reading_info(ocr_text):
    """
    Extracts current and previous readings from OCR text.
    Works by finding pairs of numbers with reasonable monthly differences.
    """
    # Find all numbers with 4-5 digits
    numbers = [int(n) for n in re.findall(r'\b\d{4,5}\b', ocr_text)]
    if not numbers:
        return {"current_reading": "", "previous_reading": "", "units": ""}

    # Deduplicate and sort
    nums = sorted(list(set(numbers)), reverse=True)
    
    # Try to find a logical pair
    for i in range(len(nums)):
        for j in range(i + 1, len(nums)):
            curr = nums[i]
            prev = nums[j]
            diff = curr - prev
            # Units are usually 10-1500
            if 10 < diff < 1500:
                return {
                    "current_reading": curr,
                    "previous_reading": prev,
                    "units": diff
                }
    
    # Fallback
    return {
        "current_reading": nums[0] if nums else "",
        "previous_reading": nums[1] if len(nums) > 1 else "",
        "units": (nums[0] - nums[1]) if len(nums) > 1 else ""
    }
