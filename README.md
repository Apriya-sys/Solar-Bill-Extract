# MSEDCL Electricity Bill Extractor

## Project Overview
This project provides a fully automated pipeline for extracting complex, unstructured data from Maharashtra State Electricity Distribution Company Limited (MSEDCL / Mahavitaran) electricity bill images. Using advanced Optical Character Recognition (OCR) combined with robust regex heuristics and mathematical data validations, the engine pulls consumer details, meter numbers, current/previous readings, consumption units, tariff plans, and bill amounts, outputting the results into a unified, cleanly formatted Excel (`.xlsx`) report.

---

## Folders & Project Structure
The project is structurally divided into key components:

```text
c:\solar-load-calculator\
│
├── assets/                  # Directory containing input electricity bill images (.jpeg, .png)
├── outputs/                 # Directory where the combined batch Excel files are generated
├── venv/                    # Python virtual environment containing isolated dependencies
│
├── app.py                   # A web-based Graphical User Interface (GUI) powered by Streamlit
├── main.py                  # The batch processing command-line engine for folder-wide extraction
├── extract_bill.py          # The core OCR mathematical & linguistic logic engine (PaddleOCR)
├── fill_excel.py            # Utility for persisting structured python dictionaries to formatted Excel
└── README.md                # Project documentation
```

---

## Installation & Setup
To run this project perfectly on a Windows system, the following installations are required:

**1. Python Environment Setup:**
Ensure Python 3.9+ is installed. Create and activate a Virtual Environment in the project directory.
```powershell
python -m venv venv
.\venv\Scripts\activate
```

**2. Core OCR & Mathematical Dependencies:**
Install the foundational OCR models and dependencies required for data extraction and Excel processing:
```powershell
pip install paddlepaddle          # Core machine learning framework
pip install "paddleocr>=2.0.1"    # The OCR optical model that parses Indian bills accurately
pip install pandas openpyxl       # For parsing and writing to .xlsx Excel spreadsheets
pip install streamlit             # The frontend framework for the Web Application GUI
```
*(Note: Tesseract represents a fallback architecture but PaddleOCR's model is strongly required for MSEDCL standard operation.)*

---

## Implementation Code Overview

### `extract_bill.py` (The Extraction Brain)
This script is the core driver behind the extraction and is mathematically fine-tuned for MSEDCL architectures.
- **Engine Initialization**: Configures `PaddleOCR` deliberately with a loosened bounding-box threshold (`det_db_box_thresh=0.2, det_db_thresh=0.2`) and disables `use_angle_cls` to detect faded or softly-printed consumer names cleanly instead of letting the engine skip them.
- **Mathematical Validation (`extract_readings`)**: Because generic OCR extracts raw grids of numbers which can be unreliable, the reading parser mathematically analyzes all integers in the document to detect a perfect numerical triplet explicitly matching `Current - Previous = Units`, heavily prioritizing high consumer consumption block limits over arbitrary billing amounts.
- **Linguistic Cleanup (`extract_name_and_address`)**: Scans lines logically via semantic checks, explicitly rejecting noisy text (like PAN, masked phone numbers `XXXX`, or file numbers `400D`) and applies linguistic spacing (e.g., automatically expanding `SHIWAJINAGAR` back properly to `SHIWAJI NAGAR`).

### `fill_excel.py` (The Formatter)
Once data is rendered into structured python dictionaries from the engine, it invokes `pandas` to translate them into a `DataFrame`.
- Manages dynamic file-naming based on timestamps (`outputs/all_bills_TIMESTAMP.xlsx`).
- Automates backend Excel column width adjustment loops iteratively, ensuring exported column headers fit neatly around their extracted rows without manual spreadsheet dragging for users processing heavy batches.

### `main.py` (The CLI Pipeline)
A quick automation script that looks into your local `assets/` folder, detects all bill images automatically, loops linearly through them feeding `extract_bill_data` on each image array, dynamically strings the dictionaries together, and saves them iteratively into a single comprehensive Excel spreadsheet via `fill_excel.py`. It provides CLI print outputs to allow operators to actively gaze at validations before opening Microsoft Excel.

### `app.py` (The Streamlit Web GUI)
Instead of forcing non-technical users to use terminal scripting:
- Enables users to visually interact and batch-upload `N` multiple files directly safely via a modern web interface.
- Concurrently triggers `extract_bill.py` on uploaded stream buffers securely, rendering side-by-side verification metrics on the UI pane dynamically.
- Deploys a final integrated binary download button natively feeding the constructed `Excel` memory payload securely back.

---

## Usage Guide
There are two ways to operate the completed extraction mechanism:

**Option 1: Using the Terminal (Batch Folder Mode)**
Place your electricity bill images cleanly into the strict `assets/` folder and trigger the python command. Terminal logs will vividly narrate runtime validations out sequentially to you natively.
```powershell
python main.py
```

**Option 2: Using the Web GUI (Interactive Mode)**
Start the standard UI layer locally natively on your `127.0.0.1:8501` socket server and securely interact by uploading physical files dynamically.
```powershell
streamlit run app.py
```
