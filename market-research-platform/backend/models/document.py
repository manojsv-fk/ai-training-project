# filepath: market-research-platform/backend/models/document.py
# ORM model for ingested documents (both uploaded PDFs and news articles).
# Application-level metadata only — LlamaIndex manages chunks/embeddings internally.

import enum
from datetime import datetime
from sqlalchemy import String, DateTime, Enum, JSON, Text
from sqlalchemy.orm import Mapped, mapped_column
from database import Base


class SourceType(str, enum.Enum):
    pdf_upload = "pdf_upload"
    news_article = "news_article"


class Document(Base):
    __tablename__ = "documents"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    title: Mapped[str] = mapped_column(String(512), nullable=False)
    source_type: Mapped[SourceType] = mapped_column(Enum(SourceType), nullable=False)
    source_name: Mapped[str] = mapped_column(String(256), nullable=True)
    original_url: Mapped[str] = mapped_column(Text, nullable=True)   # News articles
    file_path: Mapped[str] = mapped_column(Text, nullable=True)       # PDF uploads
    ingested_at: Mapped[datetime] = mapped_column(
        DateTime, default=datetime.utcnow, nullable=False
    )
    metadata_: Mapped[dict] = mapped_column(
        "metadata", JSON, default=dict, nullable=True
    )  # tags, topics, industry vertical
    llamaindex_doc_id: Mapped[str] = mapped_column(
        String(256), nullable=True
    )  # LlamaIndex internal document ID for retrieval linkback

    # TODO: Add indexing_status field (pending | indexing | indexed | failed)
    # TODO: Add relationship to Trend.supporting_document_ids (many-to-many)

    def __repr__(self) -> str:
        return f"<Document id={self.id} title={self.title!r} type={self.source_type}>"
