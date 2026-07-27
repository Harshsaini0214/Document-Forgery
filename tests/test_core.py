from PIL import Image
from utils.ela import run_ela
from utils.hashing import phash_distance
from utils.metadata import analyze_metadata

def _make_solid(color=(200, 200, 200), size=(256, 256)):
    return Image.new("RGB", size, color)

def test_ela_runs_and_scores_reasonable():
    img = _make_solid()
    ela_img, score = run_ela(img, quality=85, scale=10)
    assert ela_img.size == img.size
    assert 0.0 <= score < 1.0

def test_phash_similarity_identical():
    a = _make_solid((100, 100, 100))
    b = _make_solid((100, 100, 100))
    dist, sim = phash_distance(a, b)
    assert dist == 0
    assert abs(sim - 1.0) < 1e-6

def test_metadata_no_exif_returns_issue():
    img = _make_solid()
    meta = analyze_metadata(img)
    assert any("No EXIF" in i[0] for i in meta["issues"]) or meta["tags"] == {}

def test_imports_and_basic_pipeline():
    import importlib
    for mod in ["utils.ela", "utils.copy_move", "utils.metadata", "utils.hashing", "utils.ocr_tools", "utils.report"]:
        importlib.import_module(mod)
    img = _make_solid()
    _, _ = run_ela(img)
    d, s = phash_distance(img, img)
    assert d == 0 and s == 1.0
