import cv2
import numpy as np

def preprocess_for_ocr(image, upscale=True, apply_clahe=False):
    """
    Standard preprocessing for PaddleOCR.
    Upscale helps with small fonts, CLAHE helps with faded/low-contrast text.
    """
    if image is None:
        return None
        
    # Convert to grayscale
    gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
    
    if apply_clahe:
        # Adaptive histogram equalization for faded ink
        clahe = cv2.createCLAHE(clipLimit=2.0, tileGridSize=(8,8))
        gray = clahe.apply(gray)

    if upscale:
        # 2x Upscale for small text
        gray = cv2.resize(gray, None, fx=2, fy=2, interpolation=cv2.INTER_CUBIC)
    
    # Sharpness filter
    kernel = np.array([[-1,-1,-1], [-1,9,-1], [-1,-1,-1]])
    gray = cv2.filter2D(gray, -1, kernel)
    
    return gray

def resize_image(image, width=1200):
    """Resize image maintaining aspect ratio."""
    h, w = image.shape[:2]
    ratio = width / float(w)
    new_h = int(h * ratio)
    return cv2.resize(image, (width, new_h))
