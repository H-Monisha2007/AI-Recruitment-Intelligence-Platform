"""
Reports endpoint — generate PDF report from analysis data.
"""
from __future__ import annotations
from fastapi import APIRouter, Depends
from fastapi.responses import Response

from app.auth.dependencies import get_current_active_user
from app.database.models import User
from app.schemas import PDFReportRequest
from app.services.report_service import create_pdf_report

router = APIRouter()


@router.post("/", summary="Generate a PDF talent report", tags=["reports"])
async def generate_pdf(
    request: PDFReportRequest,
    current_user: User = Depends(get_current_active_user),
):
    results = request.model_dump()
    pdf_bytes = create_pdf_report(results)
    return Response(
        content=pdf_bytes,
        media_type="application/pdf",
        headers={"Content-Disposition": "attachment; filename=AI_Talent_Scout_Report.pdf"},
    )