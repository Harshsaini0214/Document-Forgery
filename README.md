# 🔍  Document Forgery Detector

<div a="center">

![Python](https://img.shields.io/badge/Python-3.10%20%7C%203.11%20%7C%203.12%20%7C%203.14-4f8ef7?style=for-the-badge&logo=python&logoColor=white)
![Streamlit](https://img.shields.io/badge/Streamlit-1.45%2B-FF4B4B?style=for-the-badge&logo=streamlit&logoColor=white)
![License](https://img.shields.io/badge/License-MIT-22c55e?style=for-the-badge)
![OpenCV](https://img.shields.io/badge/OpenCV-5.0%2B-5C3EE8?style=for-the-badge&logo=opencv&logoColor=white)

**A forensic document analysis tool powered by multiple AI-assisted signals.**  
Detect potential tampering in scanned documents using ELA, Copy–Move detection, EXIF inspection, perceptual hashing, and optional OCR analysis.

</div>

---

## ✨ Features

| Signal | What it detects |
|---|---|
| ⚡ **Error Level Analysis (ELA)** | JPEG recompression artifacts from edited regions |
| 🔁 **Copy–Move Detection** | Cloned/duplicated regions via ORB keypoint matching |
| 🏷️ **EXIF / Metadata Inspection** | Suspicious software tags, conflicting timestamps, missing metadata |
| 📊 **pHash Similarity** | Near-duplicate comparison against an original/reference image |
| 📝 **OCR Text Analysis** | Extracts text and flags suspicious density changes (optional) |
| 📄 **PDF Report Export** | One-click forensic report with all findings and heatmaps |

**Risk assessment** is color-coded across four levels:

| Score | Level | Color |
|---|---|---|
| 0.00 – 0.24 | 🟢 Low Risk | Green |
| 0.25 – 0.49 | 🟡 Moderate | Yellow |
| 0.50 – 0.74 | 🟠 High Risk | Orange |
| 0.75 – 1.00 | 🔴 Critical | Red |

---

## 🗂️ Project Structure

```
Document-Forgery--main/
├── app.py                    # Main Streamlit application (Python 3.14 compatible)
├── requirements.txt          # Python dependencies
│
├── utils/
│   ├── __init__.py
│   ├── ela.py                # Error Level Analysis
│   ├── copy_move.py          # ORB-based Copy–Move detection
│   ├── metadata.py           # EXIF / piexif metadata inspection
│   ├── ocr_tools.py          # Tesseract OCR + text density scoring
│   ├── hashing.py            # Perceptual hash (pHash) comparison
│   └── report.py             # ReportLab PDF report generator
│
├── tests/
│   ├── conftest.py           # sys.path bootstrap for pytest
│   └── test_core.py          # Unit tests (no Streamlit needed)
│
├── assets/
│   └── logo.png              # App logo
│
├── samples/                  # Example document images
│   ├── sample_doc_1.jpg
│   ├── sample_doc_2.jpg
│   └── original_doc.jpg      # Reference for pHash testing
│
└── reports/                  # PDF reports saved here (auto-created)
```

---

## 🚀 Quick Start

### Option A — pip (recommended for Python 3.14)

```bash
# 1. Clone the repository
git clone https://github.com/your-username/Document-Forgery.git
cd Document-Forgery--main

# 2. Create a virtual environment
python -m venv .venv

# Windows (PowerShell)
.venv\Scripts\Activate.ps1

# macOS / Linux
source .venv/bin/activate

# 3. Install dependencies
pip install -r requirements.txt

# 4. Run the app
streamlit run app.py
```

Then open **http://localhost:8501** in your browser.

### Option B — uv (fastest, works great with Python 3.14)

```bash
# Install uv if you haven't already
pip install uv

# Create venv and install deps in one step
uv venv
uv pip install -r requirements.txt

# Run
streamlit run app.py
```

---

## 🧪 Running Tests

```bash
pytest -q
```

Tests in `tests/test_core.py` cover ELA, Copy–Move, pHash, and metadata utilities without requiring Streamlit.

---

## 📸 Using the App

1. **Upload** a JPG or PNG scan of a document using the file uploader
2. **Adjust** the ELA quality, scale, and Copy–Move sliders in the sidebar
3. **Explore** findings across the 5 tabs:
   - **Preview** — image info and optional reference comparison
   - **Forensics** — ELA heatmap, Copy–Move visualization, suspicion score
   - **Metadata** — EXIF anomalies and raw tag dump
   - **OCR** — extracted text and density analysis (enable in sidebar)
   - **Export** — generate and download a PDF report
4. Optionally upload a **reference/original image** in the sidebar for pHash comparison

---

## 🖊️ OCR Setup (Optional)

OCR requires **Tesseract** to be installed separately:

| Platform | Installation |
|---|---|
| **Windows** | Download installer from [UB-Mannheim/tesseract](https://github.com/UB-Mannheim/tesseract/wiki) |
| **macOS** | `brew install tesseract` |
| **Ubuntu/Debian** | `sudo apt-get install tesseract-ocr` |

The app **auto-detects** Tesseract on Windows in common install paths. If it's installed elsewhere, set the path in [`utils/ocr_tools.py`](utils/ocr_tools.py):

```python
pytesseract.pytesseract.tesseract_cmd = r"C:\Your\Path\tesseract.exe"
```

---

## 🐍 Python 3.14 Compatibility Notes

This version has been updated for full Python 3.14 compatibility:

- ✅ All deprecated `use_container_width` Streamlit calls replaced with `width='stretch'`
- ✅ `from __future__ import annotations` added to all utility modules
- ✅ `piexif` import guarded — gracefully disabled if unavailable on 3.14 builds
- ✅ `_ensure_dep()` bootstrap fixed to use correct importable module names
- ✅ `scipy` added as explicit dependency (required by `scikit-image` on 3.14)
- ✅ Pillow, NumPy, and OpenCV version pins updated to 3.14-compatible wheels

---

## 🛠️ Troubleshooting

| Problem | Solution |
|---|---|
| `ModuleNotFoundError: No module named 'streamlit'` | Run `pip install -r requirements.txt` |
| `ModuleNotFoundError: No module named 'utils.ela'` | Run from project root: `streamlit run app.py` |
| OpenCV install error on headless server | Switch to `opencv-python-headless` in `requirements.txt` |
| Tesseract not found | Install Tesseract and/or set path in `utils/ocr_tools.py` |
| `use_container_width` deprecation warning | Already fixed in this version |
| `piexif` not installing on Python 3.14 | Safe — the app gracefully disables it |

---
---
## Author 
# Harsh Saini
**Bachelor of Computer Applications (Artificial Intelligence & Machine Learning)**
<div a="center">
  <sub>Built with ❤️ using Python, Streamlit, OpenCV, ReportLab, and Tesseract</sub>
</div>

