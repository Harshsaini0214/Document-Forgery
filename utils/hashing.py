from PIL import Image
import imagehash

def phash_distance(img_a: Image.Image, img_b: Image.Image):
    """Return pHash distance between two PIL images and similarity in [0,1]."""
    if img_a.mode != "RGB":
        img_a = img_a.convert("RGB")
    if img_b.mode != "RGB":
        img_b = img_b.convert("RGB")
    h1 = imagehash.phash(img_a)
    h2 = imagehash.phash(img_b)
    dist = h1 - h2
    similarity = 1.0 - (dist / 64.0)
    return int(dist), max(0.0, min(1.0, float(similarity)))
