# Overwriting with simpler, more reliable preprocessing
import cv2
import numpy as np

def preprocess_for_ocr(image):
    """
    Applies minimal preprocessing to an image/crop to improve OCR accuracy.
    """
    if image is None:
        return None
        
    # Convert to grayscale
    gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
    
    # Increase contrast
    alpha = 1.3 # Contrast control
    beta = 0    # Brightness control
    adjusted = cv2.convertScaleAbs(gray, alpha=alpha, beta=beta)
    
    # Sharpening kernel (mild)
    kernel = np.array([[0,-1,0], [-1,5,-1], [0,-1,0]])
    sharpened = cv2.filter2D(adjusted, -1, kernel)
    
    return sharpened




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
