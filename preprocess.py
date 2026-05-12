# Overwriting with simpler, more reliable preprocessing
import cv2
import numpy as np

def preprocess_for_ocr(image):
    if image is None:
        return None
        
    # Convert to grayscale
    gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
    
    # Denoising
    denoised = cv2.fastNlMeansDenoising(gray)
    
    # Adaptive Thresholding
    thresh = cv2.adaptiveThreshold(
        denoised, 255, cv2.ADAPTIVE_THRESH_GAUSSIAN_C, 
        cv2.THRESH_BINARY, 11, 2
    )
    
    return thresh

def clean_ocr_text(text):
    if not text: return ""
    # Separate letters and numbers (Merged Words fix)
    text = re.sub(r'([A-Z])([0-9])', r'\1 \2', text)
    text = re.sub(r'([0-9])([A-Z])', r'\1 \2', text)
    return text





def resize_image(image, width=None, height=None, inter=cv2.INTER_AREA):
    """
    Resizes an image while maintaining aspect ratio.
    """
    dim = None
    (h, w) = image.shape[:2]

    if width is None and height is None:
        return image

    if width is None:
        r = height / float(h)
        dim = (int(w * r), height)
    else:
        r = width / float(w)
        dim = (width, int(h * r))

    return cv2.resize(image, dim, interpolation=inter)
