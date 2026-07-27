from __future__ import annotations

import os
from datetime import datetime
from reportlab.lib.pagesizes import A4
from reportlab.lib import colors
from reportlab.pdfgen import canvas
from reportlab.lib.utils import ImageReader
from PIL import Image


def save_temp(image: Image.Image, path: str) -> None:
    image.save(path)


def export_report(
    output_dir: str,
    original_path: str | None,
    input_name: str,
    ela_path: str | None,
    cm_vis_path: str | None,
    meta_issues: list[tuple[str, float]] | None,
    overall_score: float,
) -> str:
    os.makedirs(output_dir, exist_ok=True)
    stamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    pdf_path = os.path.join(output_dir, f"forgery_report_{stamp}.pdf")

    c = canvas.Canvas(pdf_path, pagesize=A4)
    width, height = A4

    # ── Header bar ──────────────────────────────────────────────────────────
    c.setFillColor(colors.HexColor("#0f172a"))
    c.rect(0, height - 80, width, 80, fill=True, stroke=False)

    c.setFillColor(colors.HexColor("#4f8ef7"))
    c.rect(0, height - 83, width, 3, fill=True, stroke=False)

    c.setFillColor(colors.white)
    c.setFont("Helvetica-Bold", 18)
    c.drawString(40, height - 45, "AI Document Forgery Detector")
    c.setFont("Helvetica", 10)
    c.drawString(40, height - 62, "Forensic Analysis Report")

    # ── Meta info ────────────────────────────────────────────────────────────
    c.setFillColor(colors.HexColor("#1e293b"))
    c.rect(30, height - 145, width - 60, 52, fill=True, stroke=False)

    c.setFillColor(colors.HexColor("#94a3b8"))
    c.setFont("Helvetica", 9)
    c.drawString(42, height - 103, "DOCUMENT")
    c.drawString(250, height - 103, "ANALYSED ON")
    c.drawString(420, height - 103, "SUSPICION SCORE")

    c.setFillColor(colors.white)
    c.setFont("Helvetica-Bold", 10)
    c.drawString(42, height - 120, input_name[:36])
    c.drawString(250, height - 120, datetime.now().strftime("%d %b %Y  %H:%M"))

    # Color-coded score
    if overall_score >= 0.75:
        score_color = colors.HexColor("#ef4444")
    elif overall_score >= 0.5:
        score_color = colors.HexColor("#f97316")
    elif overall_score >= 0.25:
        score_color = colors.HexColor("#eab308")
    else:
        score_color = colors.HexColor("#22c55e")

    c.setFillColor(score_color)
    c.setFont("Helvetica-Bold", 14)
    c.drawString(420, height - 122, f"{overall_score:.2f} / 1.00")

    y = height - 175

    # ── Forensic images ──────────────────────────────────────────────────────
    img_w, img_h = 230, 190

    if ela_path and os.path.exists(ela_path):
        c.setFillColor(colors.HexColor("#0f172a"))
        c.rect(30, y - img_h - 20, img_w + 20, img_h + 32, fill=True, stroke=False)
        c.setFillColor(colors.HexColor("#94a3b8"))
        c.setFont("Helvetica-Bold", 9)
        c.drawString(40, y - 8, "ERROR LEVEL ANALYSIS (ELA)")
        try:
            c.drawImage(ImageReader(ela_path), 40, y - img_h - 16,
                        width=img_w, height=img_h, preserveAspectRatio=True, anchor="n")
        except Exception:
            pass

    if cm_vis_path and os.path.exists(cm_vis_path):
        cx = 30 + img_w + 40
        c.setFillColor(colors.HexColor("#0f172a"))
        c.rect(cx - 10, y - img_h - 20, img_w + 20, img_h + 32, fill=True, stroke=False)
        c.setFillColor(colors.HexColor("#94a3b8"))
        c.setFont("Helvetica-Bold", 9)
        c.drawString(cx, y - 8, "COPY–MOVE DETECTION")
        try:
            c.drawImage(ImageReader(cm_vis_path), cx, y - img_h - 16,
                        width=img_w, height=img_h, preserveAspectRatio=True, anchor="n")
        except Exception:
            pass

    y -= img_h + 40

    # ── Metadata findings ────────────────────────────────────────────────────
    if meta_issues:
        c.setFillColor(colors.HexColor("#0f172a"))
        c.rect(30, y - 14 * len(meta_issues[:10]) - 30, width - 60,
               14 * len(meta_issues[:10]) + 42, fill=True, stroke=False)

        c.setFillColor(colors.HexColor("#4f8ef7"))
        c.setFont("Helvetica-Bold", 10)
        c.drawString(42, y + 4, "METADATA FINDINGS")
        y -= 20
        c.setFont("Helvetica", 9)
        for issue, weight in meta_issues[:10]:
            if weight >= 0.5:
                c.setFillColor(colors.HexColor("#ef4444"))
            elif weight >= 0.3:
                c.setFillColor(colors.HexColor("#f97316"))
            else:
                c.setFillColor(colors.HexColor("#eab308"))
            c.drawString(50, y, f"▶  {issue}  (risk weight {weight:.2f})")
            y -= 14

    # ── Footer ───────────────────────────────────────────────────────────────
    c.setFillColor(colors.HexColor("#1e293b"))
    c.rect(0, 0, width, 28, fill=True, stroke=False)
    c.setFillColor(colors.HexColor("#64748b"))
    c.setFont("Helvetica", 8)
    c.drawString(40, 10, "AI Document Forgery Detector  •  Forensic Report  •  For investigative use only")

    c.showPage()
    c.save()
    return pdf_path
