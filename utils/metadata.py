from __future__ import annotations

from PIL import Image
import exifread
from io import BytesIO

try:
    import piexif  # optional – not available on all Python 3.14 builds
    _HAS_PIEXIF = True
except Exception:
    piexif = None  # type: ignore
    _HAS_PIEXIF = False


def read_exif_pillow(pil_img: Image.Image) -> dict:
    try:
        exif = pil_img.getexif()
        return dict(exif)
    except Exception:
        return {}


def read_exif_bytes(img_bytes: bytes) -> dict:
    try:
        tags = exifread.process_file(BytesIO(img_bytes), details=False)
        return {str(k): str(v) for k, v in tags.items()}
    except Exception:
        return {}


def analyze_metadata(pil_img: Image.Image) -> dict:
    issues: list[tuple[str, float]] = []
    exif = read_exif_pillow(pil_img)
    if not exif:
        issues.append(("No EXIF data", 0.6))

    buf = BytesIO()
    try:
        pil_img.save(buf, format="JPEG")
    except Exception:
        pil_img.convert("RGB").save(buf, format="JPEG")
    raw = buf.getvalue()

    try:
        tags = exifread.process_file(BytesIO(raw), details=False)
    except Exception:
        tags = {}

    tag_names = set(map(str, tags.keys()))

    suspicious_software_tags = ["Software", "ProcessingSoftware"]
    for t in suspicious_software_tags:
        if any(t in name for name in tag_names):
            issues.append((f"Editing software tag present: {t}", 0.4))

    date_tags = ["EXIF DateTimeOriginal", "Image DateTime"]
    dt_values = []
    for t in date_tags:
        if t in tags:
            dt_values.append(str(tags[t]))
    if len(set(dt_values)) > 1:
        issues.append(("Conflicting timestamps in EXIF", 0.5))

    score = min(1.0, sum(w for _, w in issues))
    return {"issues": issues, "score": score, "tags": {str(k): str(v) for k, v in tags.items()}}
