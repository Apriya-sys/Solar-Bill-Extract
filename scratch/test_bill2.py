import sys
import os
sys.path.append(os.getcwd())
from extract_bill import extract_bill_data

import json

data = extract_bill_data("assets/bill2.jpeg")
with open("scratch_output.json", "w") as f:
    json.dump(data, f, indent=4)
