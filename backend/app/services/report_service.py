"""
PDF Report generation service.
"""
from __future__ import annotations

import io
from datetime import datetime

from app.core.logging_config import get_logger
from app.core.utils import remove_emojis

logger = get_logger(__name__)




def create_pdf_report(results: dict, _role_data=None) -> bytes:
    try:
        from fpdf import FPDF
    except ImportError as exc:
        raise RuntimeError("fpdf library is required for PDF generation") from exc

    class PDF(FPDF):
        def header(self):
            self.set_font("Arial", "B", 18)
            self.set_fill_color(30, 30, 46)
            self.set_text_color(255, 255, 255)
            self.cell(0, 14, "AI Talent Scout Pro  —  Analysis Report", 0, 1, "C", fill=True)
            self.ln(6)
            self.set_text_color(0, 0, 0)

        def footer(self):
            self.set_y(-15)
            self.set_font("Arial", "I", 9)
            self.set_text_color(150, 150, 150)
            self.cell(0, 10, f"Generated: {datetime.now().strftime('%Y-%m-%d %H:%M')}  |  AI Talent Scout Pro", 0, 0, "C")

    pdf = PDF()
    pdf.add_page()

    # ── Role header ──────────────────────────────────────────────────────
    pdf.set_font("Arial", "B", 14)
    clean_role = remove_emojis(results.get("role", "Unknown"))
    pdf.cell(0, 10, f"Target Role: {clean_role}", 0, 1, "C")
    pdf.ln(4)

    # ── Score table ──────────────────────────────────────────────────────
    pdf.set_font("Arial", "B", 12)
    pdf.set_fill_color(241, 245, 249)
    pdf.cell(0, 10, "Analysis Scores", 0, 1, "L", fill=True)
    pdf.set_font("Arial", "", 11)
    scores = [
        ("Overall Role Fit", f"{int(results.get('role_fit', 0))}%"),
        ("ML Proficiency Score", f"{int(results.get('ml_score', 0))}/100"),
        ("Semantic Similarity", f"{int(results.get('semantic_score', 0))}%"),
        ("TF-IDF Skill Match", f"{int(results.get('skill_similarity', 0))}%"),
        ("ATS Compliance", f"{int(results.get('ats_score', 0))}/100"),
        ("Experience", f"{results.get('experience', 0)} years"),
        ("Hire Probability", f"{int(results.get('hire_prob', 0))}%"),
        ("Confidence", f"{int(results.get('confidence', 0) * 100)}%"),
    ]
    for label, value in scores:
        pdf.cell(90, 9, f"  {label}:", 0, 0)
        pdf.cell(0, 9, value, 0, 1)
    pdf.ln(4)

    # ── Decision banner ───────────────────────────────────────────────────
    decision = results.get("decision", "UNKNOWN")
    pdf.set_font("Arial", "B", 14)
    pdf.set_fill_color(16, 185, 129)
    pdf.set_text_color(255, 255, 255)
    pdf.cell(0, 12, f"HIRING RECOMMENDATION: {decision}", 0, 1, "C", fill=True)
    pdf.set_text_color(0, 0, 0)
    pdf.ln(6)

    # ── Top roles ─────────────────────────────────────────────────────────
    pdf.set_font("Arial", "B", 12)
    pdf.set_fill_color(241, 245, 249)
    pdf.cell(0, 10, "Top 5 Role Matches", 0, 1, "L", fill=True)
    pdf.set_font("Arial", "", 10)
    for i, (role, score) in enumerate(results.get("top_roles", [])[:5], 1):
        pdf.cell(0, 8, f"  {i}. {remove_emojis(str(role))} — {int(score)}%", 0, 1)
    pdf.ln(4)

    # ── Skills ────────────────────────────────────────────────────────────
    found   = results.get("found_skills", [])
    missing = results.get("missing_skills", [])
    if found or missing:
        pdf.set_font("Arial", "B", 12)
        pdf.set_fill_color(241, 245, 249)
        pdf.cell(0, 10, "Skill Gap Analysis", 0, 1, "L", fill=True)
        pdf.set_font("Arial", "", 10)
        pdf.set_text_color(16, 185, 129)
        pdf.cell(0, 8, f"  Found ({len(found)}): {', '.join(found) or 'None'}", 0, 1)
        pdf.set_text_color(239, 68, 68)
        pdf.cell(0, 8, f"  Missing ({len(missing)}): {', '.join(missing) or 'None'}", 0, 1)
        pdf.set_text_color(0, 0, 0)

    buf = io.BytesIO()
    pdf.output(buf)
    buf.seek(0)
    return buf.getvalue()
