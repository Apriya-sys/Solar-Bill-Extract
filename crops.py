# Bill region coordinates (y1:y2, x1:x2)
# These may need adjustment based on the actual resolution of the bill images.

# Adjusted for ~1280x882 resolution (Height x Width)
BILL_REGIONS = {
    "consumer": {
        "y": (60, 220), 
        "x": (20, 650)
    },
    "bill_details": { # Top right: Dates and Amount
        "y": (60, 250), 
        "x": (650, 880)
    },
    "meter_info": { # Middle left/right: Meter No, Load, Tariff
        "y": (250, 450), 
        "x": (15, 880)
    },
    "readings": { # Reading table values
        "y": (450, 650), 
        "x": (15, 880)
    },
    "monthly_history": { # Monthly Graph
        "y": (650, 1100), 
        "x": (430, 880)
    }
}


def get_crop(image, region_name):
    """
    Returns the cropped image for a given region.
    """
    if region_name not in BILL_REGIONS:
        return None
        
    y_coords = BILL_REGIONS[region_name]["y"]
    x_coords = BILL_REGIONS[region_name]["x"]
    
    h, w = image.shape[:2]
    
    y1, y2 = y_coords
    x1, x2 = x_coords
    
    # Simple bounds check
    y2 = min(y2, h)
    x2 = min(x2, w)
    
    return image[y1:y2, x1:x2]
