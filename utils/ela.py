from io import BytesIO
from PIL import Image, ImageChops, ImageEnhance
import numpy as np

def run_ela(pil_img: Image.Image, quality: int = 90, scale: float = 15.0):
    """Perform Error Level Analysis.
    Returns (ela_image, ela_score) where score is mean absolute ELA intensity.
    """
    if pil_img.mode != "RGB":
        pil_img = pil_img.convert("RGB")

    buf = BytesIO()
    pil_img.save(buf, format="JPEG", quality=quality)
    buf.seek(0)
    recompressed = Image.open(buf)

    diff = ImageChops.difference(pil_img, recompressed)
    enhancer = ImageEnhance.Brightness(diff)
    ela_vis = enhancer.enhance(scale)

    arr = np.asarray(diff).astype(np.float32)
    score = float(np.mean(np.abs(arr)))
    return ela_vis, score
