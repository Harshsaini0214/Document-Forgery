try:
    import cv2  # type: ignore
    _HAS_CV2 = True
except Exception:
    cv2 = None  # type: ignore
    _HAS_CV2 = False

import numpy as np
from PIL import Image

def _to_cv(img: Image.Image):
    if img.mode != "RGB":
        img = img.convert("RGB")
    import numpy as _np
    if not _HAS_CV2:
        arr = _np.array(img)
        return arr[:, :, ::-1]
    return cv2.cvtColor(_np.array(img), cv2.COLOR_RGB2BGR)

def copy_move_map(pil_img: Image.Image, max_features: int = 2000, good_match_percent: float = 0.15):
    """Detect potential copy–move via ORB matches in the same image.
    Returns (vis_bgr, match_ratio). If OpenCV missing, returns original image and 0.0.
    """
    bgr = _to_cv(pil_img)
    if not _HAS_CV2:
        return bgr, 0.0

    gray = cv2.cvtColor(bgr, cv2.COLOR_BGR2GRAY)
    orb = cv2.ORB_create(nfeatures=max_features, scaleFactor=1.2, edgeThreshold=15)
    kps, des = orb.detectAndCompute(gray, None)
    if des is None or len(kps) < 2:
        return bgr, 0.0

    bf = cv2.BFMatcher(cv2.NORM_HAMMING, crossCheck=True)
    matches = bf.match(des, des)
    matches = [m for m in matches if m.queryIdx != m.trainIdx]
    if not matches:
        return bgr, 0.0

    matches = sorted(matches, key=lambda m: m.distance)
    good_n = max(10, int(len(matches) * good_match_percent))
    good = matches[:good_n]

    vis = cv2.drawMatches(bgr, kps, bgr, kps, good, None,
                          matchColor=(0, 255, 0), singlePointColor=(255, 0, 0),
                          flags=cv2.DrawMatchesFlags_NOT_DRAW_SINGLE_POINTS)

    ratio = float(len(good)) / float(len(matches)) if matches else 0.0
    return vis, ratio
