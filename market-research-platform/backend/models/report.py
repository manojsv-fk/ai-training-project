# filepath: market-research-platform/backend/models/report.py
# ORM model for AI-generated reports (executive summaries, trend reports).
# Stores the full generated content (markdown) alongside scheduling metadata.

import enum
from datetime import datetime
from sqlalchemy import String, DateTime, Enum, JSON, Text, Boolean
from sqlalchemy.orm import Mapped, mapped_column
from database import Base


class ReportType(str, enum.Enum):
    executive_summary = "executive_summary"
    trend_report = "trend_report"
    custom = "custom"


class Report(Base):
    __tablename__ = "reports"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    title: Mapped[str] = mapped_column(String(512), nullable=False)
    report_type: Mapped[ReportType] = mapped_column(Enum(ReportType), nullable=False)
    content: Mapped[str] = mapped_column(Text, nullable=True)  # Markdown/HTML
    generated_at: Mapped[datetime] = mapped_column(
        DateTime, default=datetime.utcnow, nullable=False
    )
    is_scheduled: Mapped[bool] = mapped_column(Boolean, default=False)
    schedule_config: Mapped[dict] = mapped_column(
        JSON, nullable=True
    )  # e.g. {"cron": "0 8 * * 1", "topics": ["AI"]}
    source_document_ids: Mapped[list] = mapped_column(
        JSON, default=list
    )  # Array of Document.id values used as input

    # TODO: Add status field (generating | complete | failed)
    # TODO: Add generated_by field (manual | scheduled)

    def __repr__(self) -> str:
        return f"<Report id={self.id} title={self.title!r} type={self.report_type}>"
