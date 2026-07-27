from __future__ import annotations

import os
import sys
import pytesseract
from PIL import Image
import numpy as np

# ── Auto-detect Tesseract on Windows ──────────────────────────────────────────
_WINDOWS_PATHS = [
    r"C:\Program Files\Tesseract-OCR\tesseract.exe",
    r"C:\Program Files (x86)\Tesseract-OCR\tesseract.exe",
    r"C:\Users\Public\Tesseract-OCR\tesseract.exe",
]

def _find_tesseract() -> str | None:
    """Return tesseract executable path if found, else None."""
    if sys.platform == "win32":
        for path in _WINDOWS_PATHS:
            if os.path.isfile(path):
                return path
    return None

_tess_path = _find_tesseract()
if _tess_path:
    pytesseract.pytesseract.tesseract_cmd = _tess_path


def ocr_text(pil_img: Image.Image) -> str:
    """Extract text from image using Tesseract OCR.
    Returns empty string if Tesseract is unavailable or fails.
    """
    try:
        if pil_img.mode != "RGB":
            pil_img = pil_img.convert("RGB")
        text = pytesseract.image_to_string(pil_img)
        return text
    except Exception:
        return ""


def text_density_score(text: str) -> float:
    """Compute coefficient-of-variation of line lengths.
    High CV → suspicious density changes in the text block.
    """
    lines = [len(l.strip()) for l in text.splitlines() if l.strip()]
    if not lines:
        return 0.0
    arr = np.array(lines, dtype=float)
    cv = arr.std() / (arr.mean() + 1e-6)
    return float(min(1.0, cv))
