# filepath: market-research-platform/backend/api/routes/documents.py
# REST endpoints for document management.

import os
import uuid
import logging
from pathlib import Path

from fastapi import APIRouter, UploadFile, File, Depends, HTTPException, Query, BackgroundTasks
from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession

from api.dependencies import get_session, get_llama_engine
from config import settings
from core.llamaindex_engine import LlamaIndexEngine
from core.ingestion.pdf_ingestion import ingest_pdf
from models.document import Document, SourceType

logger = logging.getLogger(__name__)

router = APIRouter()


@router.post("/upload")
async def upload_document(
    background_tasks: BackgroundTasks,
    file: UploadFile = File(...),
    source_name: str = Query(default=""),
    db: AsyncSession = Depends(get_session),
    engine: LlamaIndexEngine = Depends(get_llama_engine),
):
    """
    Accept a PDF upload, save to disk, and trigger LlamaIndex ingestion.
    Returns the created Document record.
    """
    # Validate file type
    if file.content_type != "application/pdf" and not file.filename.endswith(".pdf"):
        raise HTTPException(status_code=400, detail="Only PDF files are accepted.")

    # Validate file size
    content = await file.read()
    max_bytes = settings.max_upload_size_mb * 1024 * 1024
    if len(content) > max_bytes:
        raise HTTPException(
            status_code=400,
            detail=f"File size exceeds {settings.max_upload_size_mb}MB limit.",
        )

    # Save file to disk with a unique name
    upload_dir = Path(settings.upload_dir)
    upload_dir.mkdir(parents=True, exist_ok=True)
    unique_name = f"{uuid.uuid4().hex}_{file.filename}"
    file_path = upload_dir / unique_name

    with open(file_path, "wb") as f:
        f.write(content)

    # Create Document record in DB
    doc = Document(
        title=file.filename.replace(".pdf", ""),
        source_type=SourceType.pdf_upload,
        source_name=source_name or "Manual Upload",
        file_path=str(file_path),
        metadata_={"original_filename": file.filename, "size_bytes": len(content)},
    )
    db.add(doc)
    await db.commit()
    await db.refresh(doc)

    # Trigger ingestion in background
    background_tasks.add_task(
        _run_ingestion, doc.id, str(file_path), source_name or "Manual Upload", engine
    )

    return {
        "id": doc.id,
        "title": doc.title,
        "source_type": doc.source_type.value,
        "source_name": doc.source_name,
        "ingested_at": doc.ingested_at.isoformat(),
        "status": "processing",
    }


async def _run_ingestion(doc_id: int, file_path: str, source_name: str, engine: LlamaIndexEngine):
    """Background task to ingest a PDF into the vector store and update the DB."""
    from database import AsyncSessionLocal

    try:
        llamaindex_doc_id = await ingest_pdf(file_path, doc_id, source_name, engine)

        async with AsyncSessionLocal() as db:
            result = await db.execute(select(Document).where(Document.id == doc_id))
            doc = result.scalar_one_or_none()
            if doc:
                doc.llamaindex_doc_id = llamaindex_doc_id
                await db.commit()

        logger.info(f"Document {doc_id} ingested successfully: {llamaindex_doc_id}")
    except Exception as e:
        logger.error(f"Ingestion failed for document {doc_id}: {e}")


@router.get("/")
async def list_documents(
    source_type: str | None = Query(default=None),
    search: str | None = Query(default=None),
    page: int = Query(default=1, ge=1),
    limit: int = Query(default=20, ge=1, le=100),
    db: AsyncSession = Depends(get_session),
):
    """List all ingested documents with optional type filter and search."""
    query = select(Document).order_by(Document.ingested_at.desc())

    # Filter by source type
    if source_type:
        query = query.where(Document.source_type == source_type)

    # Search by title or source_name
    if search:
        search_term = f"%{search}%"
        query = query.where(
            Document.title.ilike(search_term) | Document.source_name.ilike(search_term)
        )

    # Get total count
    count_query = select(func.count()).select_from(query.subquery())
    total_result = await db.execute(count_query)
    total = total_result.scalar() or 0

    # Apply pagination
    offset = (page - 1) * limit
    query = query.offset(offset).limit(limit)
    result = await db.execute(query)
    documents = result.scalars().all()

    return {
        "documents": [
            {
                "id": doc.id,
                "title": doc.title,
                "source_type": doc.source_type.value,
                "source_name": doc.source_name,
                "original_url": doc.original_url,
                "ingested_at": doc.ingested_at.isoformat(),
                "metadata": doc.metadata_,
                "has_embeddings": doc.llamaindex_doc_id is not None,
            }
            for doc in documents
        ],
        "total": total,
        "page": page,
        "limit": limit,
    }


@router.get("/{document_id}")
async def get_document(document_id: int, db: AsyncSession = Depends(get_session)):
    """Get a single document's metadata by ID."""
    result = await db.execute(select(Document).where(Document.id == document_id))
    doc = result.scalar_one_or_none()

    if not doc:
        raise HTTPException(status_code=404, detail="Document not found.")

    return {
        "id": doc.id,
        "title": doc.title,
        "source_type": doc.source_type.value,
        "source_name": doc.source_name,
        "original_url": doc.original_url,
        "file_path": doc.file_path,
        "ingested_at": doc.ingested_at.isoformat(),
        "metadata": doc.metadata_,
        "llamaindex_doc_id": doc.llamaindex_doc_id,
        "has_embeddings": doc.llamaindex_doc_id is not None,
    }


@router.delete("/{document_id}")
async def delete_document(
    document_id: int,
    db: AsyncSession = Depends(get_session),
    engine: LlamaIndexEngine = Depends(get_llama_engine),
):
    """Delete a document from the DB and remove its nodes from the vector store."""
    result = await db.execute(select(Document).where(Document.id == document_id))
    doc = result.scalar_one_or_none()

    if not doc:
        raise HTTPException(status_code=404, detail="Document not found.")

    # Remove from LlamaIndex vector store
    if doc.llamaindex_doc_id:
        engine.delete_document(doc.llamaindex_doc_id)

    # Delete physical file if it's a PDF upload
    if doc.file_path and os.path.exists(doc.file_path):
        try:
            os.remove(doc.file_path)
        except OSError as e:
            logger.warning(f"Failed to delete file {doc.file_path}: {e}")

    # Delete from DB
    await db.delete(doc)
    await db.commit()

    return {"deleted": True, "id": document_id}
