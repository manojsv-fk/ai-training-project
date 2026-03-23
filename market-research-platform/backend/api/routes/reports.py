# filepath: market-research-platform/backend/api/routes/reports.py
# REST endpoints for report generation and retrieval.

import io
import logging

from fastapi import APIRouter, Depends, Query, HTTPException, Body
from fastapi.responses import StreamingResponse
from pydantic import BaseModel
from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession

from api.dependencies import get_session, get_llama_engine
from config import settings
from core.llamaindex_engine import LlamaIndexEngine
from core.query.summary_engine import SummaryEngine
from core.reports.export import to_pdf, to_docx
from models.report import Report, ReportType

logger = logging.getLogger(__name__)

router = APIRouter()


class ReportGenerateRequest(BaseModel):
    document_ids: list[int] = []
    report_type: str = "executive_summary"
    title: str = "Executive Summary"


@router.post("/generate")
async def generate_report(
    body: ReportGenerateRequest,
    db: AsyncSession = Depends(get_session),
    engine: LlamaIndexEngine = Depends(get_llama_engine),
):
    """
    Generate a new report from selected documents.
    """
    # Validate report type
    try:
        report_type = ReportType(body.report_type)
    except ValueError:
        raise HTTPException(
            status_code=400,
            detail=f"Invalid report_type. Must be one of: {[e.value for e in ReportType]}",
        )

    summary_engine = SummaryEngine(engine)

    # Generate content based on report type
    if report_type == ReportType.executive_summary:
        content = await summary_engine.generate_executive_summary(
            document_ids=body.document_ids or None,
            title=body.title,
        )
    elif report_type == ReportType.trend_report:
        trends = await summary_engine.identify_trends(
            document_ids=body.document_ids or None,
        )
        # Format trends into a markdown report
        content = _format_trend_report(trends, body.title)
    else:
        # Custom report — generate a general summary
        content = await summary_engine.generate_executive_summary(
            document_ids=body.document_ids or None,
            title=body.title,
        )

    # Save to DB
    report = Report(
        title=body.title,
        report_type=report_type,
        content=content,
        is_scheduled=False,
        source_document_ids=body.document_ids,
    )
    db.add(report)
    await db.commit()
    await db.refresh(report)

    return {
        "id": report.id,
        "title": report.title,
        "report_type": report.report_type.value,
        "content": report.content,
        "generated_at": report.generated_at.isoformat(),
        "source_document_ids": report.source_document_ids,
    }


@router.get("/")
async def list_reports(
    report_type: str | None = Query(default=None),
    sort: str = Query(default="newest"),
    page: int = Query(default=1, ge=1),
    limit: int = Query(default=20, ge=1, le=100),
    db: AsyncSession = Depends(get_session),
):
    """List all generated reports, optionally filtered by type."""
    query = select(Report)

    if report_type:
        query = query.where(Report.report_type == report_type)

    # Sort
    if sort == "oldest":
        query = query.order_by(Report.generated_at.asc())
    else:
        query = query.order_by(Report.generated_at.desc())

    # Count
    count_query = select(func.count()).select_from(query.subquery())
    total_result = await db.execute(count_query)
    total = total_result.scalar() or 0

    # Paginate
    offset = (page - 1) * limit
    query = query.offset(offset).limit(limit)
    result = await db.execute(query)
    reports = result.scalars().all()

    return {
        "reports": [
            {
                "id": r.id,
                "title": r.title,
                "report_type": r.report_type.value,
                "generated_at": r.generated_at.isoformat(),
                "is_scheduled": r.is_scheduled,
                "source_document_ids": r.source_document_ids,
                # Omit content in list view for performance
            }
            for r in reports
        ],
        "total": total,
        "page": page,
        "limit": limit,
    }


@router.get("/{report_id}")
async def get_report(report_id: int, db: AsyncSession = Depends(get_session)):
    """Retrieve a single report by ID, including full content."""
    result = await db.execute(select(Report).where(Report.id == report_id))
    report = result.scalar_one_or_none()

    if not report:
        raise HTTPException(status_code=404, detail="Report not found.")

    return {
        "id": report.id,
        "title": report.title,
        "report_type": report.report_type.value,
        "content": report.content,
        "generated_at": report.generated_at.isoformat(),
        "is_scheduled": report.is_scheduled,
        "schedule_config": report.schedule_config,
        "source_document_ids": report.source_document_ids,
    }


@router.get("/{report_id}/export")
async def export_report(
    report_id: int,
    format: str = Query(..., pattern="^(pdf|docx)$"),
    db: AsyncSession = Depends(get_session),
):
    """Export a report as PDF or Word (.docx). Returns a file download."""
    result = await db.execute(select(Report).where(Report.id == report_id))
    report = result.scalar_one_or_none()

    if not report:
        raise HTTPException(status_code=404, detail="Report not found.")

    if format == "pdf":
        content_bytes = to_pdf(report.title, report.content or "")
        media_type = "application/pdf"
        filename = f"{report.title}.pdf"
    else:
        content_bytes = to_docx(report.title, report.content or "")
        media_type = "application/vnd.openxmlformats-officedocument.wordprocessingml.document"
        filename = f"{report.title}.docx"

    return StreamingResponse(
        io.BytesIO(content_bytes),
        media_type=media_type,
        headers={
            "Content-Disposition": f'attachment; filename="{filename}"',
        },
    )


@router.delete("/{report_id}")
async def delete_report(report_id: int, db: AsyncSession = Depends(get_session)):
    """Delete a report record."""
    result = await db.execute(select(Report).where(Report.id == report_id))
    report = result.scalar_one_or_none()

    if not report:
        raise HTTPException(status_code=404, detail="Report not found.")

    await db.delete(report)
    await db.commit()

    return {"deleted": True, "id": report_id}


def _format_trend_report(trends: list[dict], title: str) -> str:
    """Format a list of trend dicts into a markdown report."""
    lines = [f"# {title}", "", "## Identified Market Trends", ""]

    if not trends:
        lines.append("No significant trends were identified from the available documents.")
        return "\n".join(lines)

    for i, trend in enumerate(trends, 1):
        score = trend.get("confidence_score", 0)
        confidence_label = "HIGH" if score >= 0.8 else "MEDIUM" if score >= 0.5 else "LOW"

        lines.append(f"### {i}. {trend.get('title', 'Untitled')}")
        lines.append("")
        lines.append(f"**Confidence:** {confidence_label} ({score:.0%})")
        lines.append("")
        lines.append(trend.get("description", ""))
        lines.append("")

        tags = trend.get("tags", [])
        if tags:
            lines.append(f"**Sources:** {', '.join(tags)}")
            lines.append("")

    lines.append("---")
    lines.append("*Report generated by Market Research Intelligence Platform*")
    return "\n".join(lines)
