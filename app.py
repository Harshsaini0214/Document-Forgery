from __future__ import annotations

import os
import sys
import subprocess
from io import BytesIO
from pathlib import Path

# ── Path bootstrap ─────────────────────────────────────────────────────────────
ROOT = Path(__file__).resolve().parent
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))


def _ensure_dep(import_name: str, pip_name: str | None = None) -> bool:
    """Try to import `import_name`; if missing, install `pip_name` via pip."""
    pkg = pip_name or import_name
    try:
        __import__(import_name)
        return True
    except Exception:
        print(f"[bootstrap] Installing missing package: {pkg}…")
        try:
            subprocess.check_call([sys.executable, "-m", "pip", "install", pkg])
            __import__(import_name)
            return True
        except Exception as e:
            print(f"[bootstrap] Failed to install {pkg}: {e}")
            return False


if not _ensure_dep("streamlit"):
    print("\nERROR: Streamlit is required. Please run: pip install -r requirements.txt\n")
    sys.exit(1)

import numpy as np
import streamlit as st
from PIL import Image

# Ensure optional deps
_ensure_dep("PIL", "Pillow")
_ensure_dep("cv2", "opencv-python")
_ensure_dep("imagehash")
_ensure_dep("reportlab")
_ensure_dep("exifread")
_ensure_dep("piexif")
_ensure_dep("pytesseract")

from utils.ela import run_ela
from utils.copy_move import copy_move_map
from utils.metadata import analyze_metadata
from utils.ocr_tools import ocr_text, text_density_score
from utils.hashing import phash_distance
from utils.report import export_report

# ── Page config ────────────────────────────────────────────────────────────────
st.set_page_config(
    page_title="Document Forgery Detector",
    page_icon="🔍",
    layout="wide",
    initial_sidebar_state="expanded",
)

# ── Global CSS ─────────────────────────────────────────────────────────────────
st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700&display=swap');

/* ── Root & Base ─────────────────────────────────────── */
html, body, [class*="css"] {
    font-family: 'Inter', sans-serif !important;
}
.stApp {
    background: #0a0b0f;
    color: #e2e8f0;
}

/* ── Hero Header ─────────────────────────────────────── */
.hero-wrap {
    background: linear-gradient(135deg, #0f172a 0%, #1a1f35 50%, #0f172a 100%);
    border: 1px solid #1e293b;
    border-radius: 16px;
    padding: 28px 32px;
    margin-bottom: 24px;
    position: relative;
    overflow: hidden;
}
.hero-wrap::before {
    content: '';
    position: absolute;
    top: 0; left: 0; right: 0; height: 2px;
    background: linear-gradient(90deg, #4f8ef7, #818cf8, #4f8ef7);
    animation: shimmer 3s linear infinite;
    background-size: 200% 100%;
}
@keyframes shimmer {
    0% { background-position: -200% 0; }
    100% { background-position: 200% 0; }
}
.hero-title {
    font-size: 2rem;
    font-weight: 700;
    background: linear-gradient(135deg, #e2e8f0, #4f8ef7);
    -webkit-background-clip: text;
    -webkit-text-fill-color: transparent;
    background-clip: text;
    margin: 0 0 6px 0;
}
.hero-sub {
    color: #64748b;
    font-size: 0.875rem;
    font-weight: 400;
    margin: 0;
    letter-spacing: 0.05em;
}
.hero-badge {
    display: inline-block;
    background: rgba(79,142,247,0.15);
    border: 1px solid rgba(79,142,247,0.3);
    color: #4f8ef7;
    border-radius: 20px;
    padding: 3px 10px;
    font-size: 0.7rem;
    font-weight: 600;
    letter-spacing: 0.08em;
    margin-top: 10px;
    margin-right: 6px;
}

/* ── Sidebar ─────────────────────────────────────────── */
[data-testid="stSidebar"] {
    background: #0d1117 !important;
    border-right: 1px solid #1e293b;
}
[data-testid="stSidebar"] .stMarkdown h2,
[data-testid="stSidebar"] .stMarkdown h3 {
    color: #4f8ef7;
    font-size: 0.85rem;
    letter-spacing: 0.1em;
    text-transform: uppercase;
    font-weight: 600;
}

/* ── Upload zone ─────────────────────────────────────── */
[data-testid="stFileUploader"] {
    border: 2px dashed #1e293b;
    border-radius: 12px;
    background: #0d1117;
    transition: border-color 0.3s;
}
[data-testid="stFileUploader"]:hover {
    border-color: #4f8ef7;
}

/* ── Cards ───────────────────────────────────────────── */
.glass-card {
    background: rgba(15, 23, 42, 0.8);
    backdrop-filter: blur(12px);
    border: 1px solid #1e293b;
    border-radius: 12px;
    padding: 20px;
    margin-bottom: 16px;
}

/* ── Risk Badge ──────────────────────────────────────── */
.risk-badge {
    display: inline-flex;
    align-items: center;
    gap: 8px;
    padding: 10px 20px;
    border-radius: 8px;
    font-weight: 700;
    font-size: 1.1rem;
    margin-top: 8px;
}
.risk-low    { background: rgba(34,197,94,0.15);  border: 1px solid #22c55e; color: #22c55e; }
.risk-medium { background: rgba(234,179,8,0.15);  border: 1px solid #eab308; color: #eab308; }
.risk-high   { background: rgba(249,115,22,0.15); border: 1px solid #f97316; color: #f97316; }
.risk-critical { background: rgba(239,68,68,0.15); border: 1px solid #ef4444; color: #ef4444; }

/* ── Metric override ─────────────────────────────────── */
[data-testid="stMetric"] {
    background: #0f172a;
    border: 1px solid #1e293b;
    border-radius: 10px;
    padding: 14px 18px;
}
[data-testid="stMetricValue"] {
    color: #4f8ef7 !important;
    font-weight: 700 !important;
}

/* ── Tabs ────────────────────────────────────────────── */
.stTabs [data-baseweb="tab-list"] {
    background: #0d1117;
    border-bottom: 1px solid #1e293b;
    gap: 4px;
}
.stTabs [data-baseweb="tab"] {
    color: #64748b;
    font-weight: 500;
    border-radius: 6px 6px 0 0;
    padding: 8px 20px;
}
.stTabs [aria-selected="true"] {
    background: #0f172a;
    color: #4f8ef7 !important;
    border-bottom: 2px solid #4f8ef7;
}

/* ── Buttons ─────────────────────────────────────────── */
.stButton > button[kind="primary"] {
    background: linear-gradient(135deg, #4f8ef7, #818cf8);
    border: none;
    border-radius: 8px;
    color: white;
    font-weight: 600;
    padding: 10px 24px;
    transition: all 0.2s;
}
.stButton > button[kind="primary"]:hover {
    transform: translateY(-1px);
    box-shadow: 0 4px 20px rgba(79,142,247,0.4);
}

/* ── Info / warning / success ───────────────────────── */
.stAlert {
    border-radius: 8px !important;
    border-left-width: 3px !important;
}

/* ── Text areas ──────────────────────────────────────── */
.stTextArea textarea {
    background: #0d1117 !important;
    border: 1px solid #1e293b !important;
    color: #e2e8f0 !important;
    font-family: 'JetBrains Mono', 'Courier New', monospace !important;
    border-radius: 8px !important;
}

/* ── Expander ────────────────────────────────────────── */
details {
    background: #0d1117 !important;
    border: 1px solid #1e293b !important;
    border-radius: 8px !important;
}
summary {
    color: #94a3b8 !important;
    font-weight: 500 !important;
}

/* ── Divider ─────────────────────────────────────────── */
hr {
    border-color: #1e293b !important;
}

/* ── Scrollbar ───────────────────────────────────────── */
::-webkit-scrollbar { width: 6px; }
::-webkit-scrollbar-track { background: #0a0b0f; }
::-webkit-scrollbar-thumb { background: #1e293b; border-radius: 3px; }
::-webkit-scrollbar-thumb:hover { background: #334155; }
</style>
""", unsafe_allow_html=True)


# ── Helper ─────────────────────────────────────────────────────────────────────
def _risk_level(score: float) -> tuple[str, str, str]:
    """Return (label, css_class, emoji) based on suspicion score."""
    if score >= 0.75:
        return "CRITICAL", "risk-critical", "🔴"
    if score >= 0.50:
        return "HIGH RISK", "risk-high", "🟠"
    if score >= 0.25:
        return "MODERATE", "risk-medium", "🟡"
    return "LOW RISK", "risk-low", "🟢"


# ── Hero header ────────────────────────────────────────────────────────────────
logo_path = os.path.join("assets", "logo.png")
h_col1, h_col2 = st.columns([1, 11])
with h_col1:
    if os.path.exists(logo_path):
        st.image(logo_path, width=72)
with h_col2:
    st.markdown("""
    <div class="hero-wrap">
        <p class="hero-title">Document Forgery Detector</p>
        <p class="hero-sub">FORENSIC ANALYSIS ENGINE &nbsp;·&nbsp; Python 3.14 Compatible</p>
        <span class="hero-badge">ELA</span>
        <span class="hero-badge">Copy–Move</span>
        <span class="hero-badge">EXIF Metadata</span>
        <span class="hero-badge">pHash</span>
        <span class="hero-badge">OCR</span>
    </div>
    """, unsafe_allow_html=True)


# ── Sidebar ─────────────────────────────────────────────────────────────────────
with st.sidebar:
    st.markdown("## ⚙️ Controls")

    st.markdown("### Error Level Analysis")
    ela_quality = st.slider("JPEG recompression quality", 60, 98, 90, 1,
                            help="Lower = more aggressive recompression, amplifies differences")
    ela_scale = st.slider("ELA visual scale factor", 5.0, 40.0, 15.0, 0.5,
                          help="Higher = brighter ELA heatmap")

    st.markdown("### Copy–Move Detection")
    cm_features = st.slider("ORB feature count", 500, 5000, 2000, 100,
                            help="More features = more thorough but slower")
    cm_good_pct = st.slider("Good match threshold %", 0.05, 0.5, 0.15, 0.01,
                             help="Fraction of best matches considered 'good'")

    st.markdown("### Optional Modules")
    use_ocr = st.toggle("Run OCR checks", value=False,
                        help="Requires Tesseract OCR installed on your system (slower)")

    st.divider()
    st.markdown("### 🖼️ Reference Image")
    st.caption("Upload the original document to enable pHash comparison")
    ref_file = st.file_uploader("Reference / original image", type=["jpg", "jpeg", "png"], key="ref")

    st.divider()
    st.markdown(
        "<div style='color:#334155;font-size:0.72rem;text-align:center'>"
        "AI Document Forgery Detector<br>Python 3.14 · Streamlit"
        "</div>",
        unsafe_allow_html=True,
    )


# ── Main upload ────────────────────────────────────────────────────────────────
st.markdown("---")
uploaded = st.file_uploader(
    "📂  Upload a document image (JPG / PNG)",
    type=["jpg", "jpeg", "png"],
    accept_multiple_files=False,
    help="Supports JPEG and PNG scans or photos of documents",
)

if uploaded is not None:
    img_bytes = uploaded.read()
    pil = Image.open(BytesIO(img_bytes))

    tabs = st.tabs(["🖼️  Preview", "🔬  Forensics", "🏷️  Metadata", "📝  OCR", "📄  Export"])

    # ── Tab 0: Preview ─────────────────────────────────────────────────────────
    with tabs[0]:
        st.markdown("#### Document Preview")
        c1, c2 = st.columns(2)
        with c1:
            st.image(pil, caption=f"📄 {uploaded.name}", width="stretch")
            w, h = pil.size
            mode = pil.mode
            st.markdown(
                f'<div class="glass-card">'
                f'<b style="color:#4f8ef7">Image Info</b><br>'
                f'<span style="color:#94a3b8">Filename:</span> {uploaded.name}<br>'
                f'<span style="color:#94a3b8">Dimensions:</span> {w} × {h} px<br>'
                f'<span style="color:#94a3b8">Color mode:</span> {mode}<br>'
                f'<span style="color:#94a3b8">File size:</span> {len(img_bytes)/1024:.1f} KB'
                f'</div>',
                unsafe_allow_html=True,
            )
        with c2:
            if ref_file is not None:
                ref_img = Image.open(ref_file)
                st.image(ref_img, caption=f"📋 Reference: {ref_file.name}", width="stretch")
            else:
                st.markdown(
                    '<div class="glass-card" style="text-align:center;padding:40px 20px;">'
                    '<p style="font-size:2rem">📋</p>'
                    '<p style="color:#4f8ef7;font-weight:600">No Reference Image</p>'
                    '<p style="color:#64748b;font-size:0.85rem">'
                    'Upload an original document in the sidebar to enable pHash similarity comparison.</p>'
                    '</div>',
                    unsafe_allow_html=True,
                )
            st.info("💡 **Tip:** Increase the ELA scale slider to accentuate manipulation artifacts.")

    # ── Tab 1: Forensics ───────────────────────────────────────────────────────
    with tabs[1]:
        st.markdown("#### Forensic Signal Analysis")

        with st.spinner("Running forensic analysis…"):
            ela_vis, ela_score = run_ela(pil, quality=ela_quality, scale=ela_scale)
            cm_vis, cm_ratio = copy_move_map(pil, max_features=cm_features, good_match_percent=cm_good_pct)

        fcol1, fcol2 = st.columns(2)

        with fcol1:
            st.markdown(
                '<div style="color:#4f8ef7;font-weight:600;margin-bottom:8px">'
                '⚡ Error Level Analysis (ELA)</div>',
                unsafe_allow_html=True,
            )
            st.image(ela_vis, caption=f"ELA Heatmap — mean diff: {ela_score:.4f}", width="stretch")
            ela_level = "🔴 Elevated" if ela_score > 5 else ("🟡 Moderate" if ela_score > 2 else "🟢 Normal")
            st.metric("ELA Mean Intensity", f"{ela_score:.4f}", delta=ela_level, delta_color="off")

        with fcol2:
            st.markdown(
                '<div style="color:#4f8ef7;font-weight:600;margin-bottom:8px">'
                '🔁 Copy–Move Detection (ORB)</div>',
                unsafe_allow_html=True,
            )
            try:
                st.image(cm_vis[:, :, ::-1], caption=f"Match ratio: {cm_ratio:.3f}", width="stretch")
            except Exception:
                st.image(cm_vis, caption=f"Match ratio: {cm_ratio:.3f}", width="stretch")
                st.caption("⚠️ OpenCV not available — showing original image.")
            cm_level = "🔴 Suspicious" if cm_ratio > 0.3 else ("🟡 Possible" if cm_ratio > 0.1 else "🟢 Normal")
            st.metric("Good/All Match Ratio", f"{cm_ratio:.3f}", delta=cm_level, delta_color="off")

        st.divider()

        # pHash comparison
        phash_sim = None
        if ref_file is not None:
            ref_img_ph = Image.open(ref_file)
            dist, sim = phash_distance(pil, ref_img_ph)
            phash_sim = sim
            ph_col1, ph_col2 = st.columns(2)
            with ph_col1:
                st.metric("pHash Distance", dist, help="0 = identical, 64 = completely different")
            with ph_col2:
                st.metric("pHash Similarity", f"{sim:.3f}", help="1.0 = identical images")
        else:
            st.info("📋 Upload a reference image in the sidebar to enable pHash similarity comparison.")

        st.divider()

        # ── Suspicion Score ────────────────────────────────────────────────────
        ela_norm = min(1.0, ela_score / 10.0)
        cm_norm  = min(1.0, cm_ratio * 3.0)
        ph_norm  = (1.0 - phash_sim) if phash_sim is not None else 0.0
        suspicion = float(np.clip(0.5 * ela_norm + 0.4 * cm_norm + 0.1 * ph_norm, 0.0, 1.0))

        label, css_cls, emoji = _risk_level(suspicion)

        score_col1, score_col2 = st.columns([1, 2])
        with score_col1:
            st.metric(
                "Overall Suspicion Score",
                f"{suspicion:.2f} / 1.00",
                help="Weighted heuristic: 50% ELA · 40% Copy-Move · 10% pHash",
            )
        with score_col2:
            st.markdown(
                f'<div class="risk-badge {css_cls}">{emoji} {label}</div>',
                unsafe_allow_html=True,
            )
            st.markdown(
                '<div style="color:#64748b;font-size:0.78rem;margin-top:6px">'
                'Weighted: 50% ELA · 40% Copy–Move · 10% pHash</div>',
                unsafe_allow_html=True,
            )

    # ── Tab 2: Metadata ────────────────────────────────────────────────────────
    with tabs[2]:
        st.markdown("#### EXIF & Metadata Inspection")

        with st.spinner("Reading metadata…"):
            meta = analyze_metadata(pil)

        if meta["issues"]:
            st.markdown(
                f'<div class="glass-card">'
                f'<b style="color:#ef4444">⚠️ {len(meta["issues"])} issue(s) detected</b>'
                f'</div>',
                unsafe_allow_html=True,
            )
            for issue, weight in meta["issues"]:
                if weight >= 0.5:
                    st.error(f"🔴 {issue}  *(risk weight: {weight:.2f})*")
                elif weight >= 0.3:
                    st.warning(f"🟠 {issue}  *(risk weight: {weight:.2f})*")
                else:
                    st.warning(f"🟡 {issue}  *(risk weight: {weight:.2f})*")
        else:
            st.success("✅ No obvious metadata issues detected.")

        with st.expander("📋 Raw EXIF Tags", expanded=False):
            if meta["tags"]:
                st.json(meta["tags"])
            else:
                st.caption("No EXIF tags found in this image.")

    # ── Tab 3: OCR ─────────────────────────────────────────────────────────────
    with tabs[3]:
        st.markdown("#### OCR & Text Density Analysis")

        if use_ocr:
            with st.spinner("Running Tesseract OCR…"):
                text = ocr_text(pil)
                density = text_density_score(text)

            if text.strip():
                char_count = len(text.strip())
                word_count = len(text.split())
                line_count = len([l for l in text.splitlines() if l.strip()])

                m1, m2, m3, m4 = st.columns(4)
                m1.metric("Characters", char_count)
                m2.metric("Words", word_count)
                m3.metric("Lines", line_count)
                m4.metric("Density Score", f"{density:.2f}")

                st.text_area("📄 Extracted Text", text, height=220)

                # Update suspicion with OCR contribution
                ela_norm = min(1.0, ela_score / 10.0)
                cm_norm  = min(1.0, cm_ratio * 3.0)
                ph_norm  = (1.0 - phash_sim) if phash_sim is not None else 0.0
                suspicion_base = float(np.clip(0.5 * ela_norm + 0.4 * cm_norm + 0.1 * ph_norm, 0.0, 1.0))
                suspicion_ocr  = float(np.clip(suspicion_base * 0.9 + 0.1 * density, 0.0, 1.0))

                label_ocr, css_ocr, emoji_ocr = _risk_level(suspicion_ocr)
                st.divider()
                st.metric("Updated Suspicion (with OCR)", f"{suspicion_ocr:.2f}")
                st.markdown(
                    f'<div class="risk-badge {css_ocr}">{emoji_ocr} {label_ocr}</div>',
                    unsafe_allow_html=True,
                )
            else:
                st.warning("⚠️ No text could be extracted. Tesseract may not be installed or the image has no text.")
                st.info("Install Tesseract: https://github.com/UB-Mannheim/tesseract/wiki")
        else:
            st.markdown(
                '<div class="glass-card" style="text-align:center;padding:40px 20px;">'
                '<p style="font-size:2rem">📝</p>'
                '<p style="color:#4f8ef7;font-weight:600">OCR Disabled</p>'
                '<p style="color:#64748b;font-size:0.85rem">'
                'Enable <b>Run OCR checks</b> in the sidebar to extract and analyse text content.</p>'
                '</div>',
                unsafe_allow_html=True,
            )

    # ── Tab 4: Export ──────────────────────────────────────────────────────────
    with tabs[4]:
        st.markdown("#### PDF Report Export")

        # Re-compute scores for export (in case tabs[1] wasn't visited first)
        ela_vis_exp, ela_score_exp = run_ela(pil, quality=ela_quality, scale=ela_scale)
        cm_vis_exp, cm_ratio_exp   = copy_move_map(pil, max_features=cm_features, good_match_percent=cm_good_pct)
        phash_sim_exp = None
        if ref_file is not None:
            ref_img_exp = Image.open(ref_file)
            _, phash_sim_exp = phash_distance(pil, ref_img_exp)
        ela_norm_exp = min(1.0, ela_score_exp / 10.0)
        cm_norm_exp  = min(1.0, cm_ratio_exp * 3.0)
        ph_norm_exp  = (1.0 - phash_sim_exp) if phash_sim_exp is not None else 0.0
        suspicion_exp = float(np.clip(0.5 * ela_norm_exp + 0.4 * cm_norm_exp + 0.1 * ph_norm_exp, 0.0, 1.0))
        meta_exp = analyze_metadata(pil)

        label_exp, css_exp, emoji_exp = _risk_level(suspicion_exp)

        exp_col1, exp_col2 = st.columns([2, 1])
        with exp_col1:
            st.markdown(
                '<div class="glass-card">'
                '<b style="color:#4f8ef7">📄 Report will include:</b><br><br>'
                '• Error Level Analysis heatmap<br>'
                '• Copy–Move detection visualization<br>'
                '• Metadata findings & EXIF anomalies<br>'
                '• Overall suspicion score with risk label<br>'
                '• Timestamped forensic summary'
                '</div>',
                unsafe_allow_html=True,
            )
            out_dir = st.text_input("📁 Output folder", value="reports")
        with exp_col2:
            st.markdown(
                f'<div class="glass-card" style="text-align:center">'
                f'<p style="color:#94a3b8;font-size:0.8rem;margin-bottom:6px">RISK ASSESSMENT</p>'
                f'<div class="risk-badge {css_exp}">{emoji_exp} {label_exp}</div>'
                f'<p style="color:#4f8ef7;font-weight:700;font-size:1.4rem;margin-top:12px">'
                f'{suspicion_exp:.2f}</p>'
                f'<p style="color:#64748b;font-size:0.75rem">Suspicion Score</p>'
                f'</div>',
                unsafe_allow_html=True,
            )

        st.markdown("<br>", unsafe_allow_html=True)

        # Save temp forensic images
        tmp_dir = "_tmp"
        os.makedirs(tmp_dir, exist_ok=True)
        ela_path = os.path.join(tmp_dir, "ela.png")
        cm_path  = os.path.join(tmp_dir, "copy_move.png")
        ela_vis_exp.save(ela_path)
        from PIL import Image as PILImage
        try:
            PILImage.fromarray(cm_vis_exp[:, :, ::-1]).save(cm_path)
        except Exception:
            PILImage.fromarray(cm_vis_exp).save(cm_path)

        if st.button("🚀 Generate PDF Report", type="primary"):
            with st.spinner("Building PDF report…"):
                pdf = export_report(
                    output_dir=out_dir,
                    original_path=None,
                    input_name=uploaded.name,
                    ela_path=ela_path,
                    cm_vis_path=cm_path,
                    meta_issues=meta_exp["issues"],
                    overall_score=suspicion_exp,
                )
            st.success(f"✅ Report saved to: `{pdf}`")
            with open(pdf, "rb") as fh:
                st.download_button(
                    "⬇️ Download PDF Report",
                    data=fh.read(),
                    file_name=os.path.basename(pdf),
                    mime="application/pdf",
                )

else:
    # ── Landing / empty state ──────────────────────────────────────────────────
    st.markdown("<br>", unsafe_allow_html=True)
    st.markdown(
        '<div class="glass-card" style="text-align:center;padding:60px 40px;">'
        '<p style="font-size:3rem;margin-bottom:8px">🔍</p>'
        '<p style="font-size:1.4rem;font-weight:700;color:#e2e8f0;margin-bottom:8px">'
        'Upload a Document to Begin</p>'
        '<p style="color:#64748b;max-width:480px;margin:0 auto;line-height:1.6">'
        'Drop a JPG or PNG scan of any document above. The engine will run '
        'ELA, Copy–Move, Metadata, and optional OCR checks to detect potential forgery.'
        '</p>'
        '<br>'
        '<div style="display:flex;gap:16px;justify-content:center;flex-wrap:wrap;margin-top:8px">'
        '<span class="hero-badge">🔬 ELA Analysis</span>'
        '<span class="hero-badge">🔁 Copy–Move</span>'
        '<span class="hero-badge">🏷️ EXIF Metadata</span>'
        '<span class="hero-badge">📊 pHash Compare</span>'
        '<span class="hero-badge">📝 OCR Text</span>'
        '</div>'
        '</div>',
        unsafe_allow_html=True,
    )
