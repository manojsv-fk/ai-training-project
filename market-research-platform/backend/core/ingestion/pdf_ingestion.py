# filepath: market-research-platform/backend/core/ingestion/pdf_ingestion.py
# PDF ingestion pipeline. Parses uploaded PDFs using LlamaParse (primary)
# or a simple fallback parser, chunks the text, and indexes into PGVectorStore.

import logging
from pathlib import Path

from llama_index.core import Document as LlamaDocument
from llama_index.core.node_parser import SentenceSplitter

from config import settings
from core.llamaindex_engine import LlamaIndexEngine

logger = logging.getLogger(__name__)


async def ingest_pdf(
    file_path: str,
    document_id: int,
    source_name: str,
    engine: LlamaIndexEngine,
) -> str:
    """
    Full PDF ingestion pipeline.

    Steps:
        1. Parse PDF with LlamaParse (falls back to simple text extraction)
        2. Chunk text with SentenceSplitter
        3. Attach source metadata to each node
        4. Add nodes to the LlamaIndex VectorStoreIndex
        5. Return the LlamaIndex document ID for storage in the DB record

    Args:
        file_path: Absolute path to the uploaded PDF on disk.
        document_id: DB Document.id (attached as node metadata for provenance).
        source_name: Human-readable source label (e.g. "Gartner").
        engine: Initialized LlamaIndexEngine instance.

    Returns:
        llamaindex_doc_id: The internal LlamaIndex document ID string.
    """
    path = Path(file_path)
    if not path.exists():
        raise FileNotFoundError(f"PDF file not found: {file_path}")

    logger.info(f"Starting PDF ingestion for: {path.name} (doc_id={document_id})")

    # Step 1 — Parse the PDF
    llama_docs = await _parse_pdf(file_path)

    if not llama_docs:
        raise ValueError(f"No content extracted from PDF: {file_path}")

    # Assign consistent doc_id across all extracted documents
    doc_id = f"doc_{document_id}_{path.stem}"
    for doc in llama_docs:
        doc.doc_id = doc_id
        doc.metadata.update({
            "document_id": document_id,
            "source_name": source_name or path.stem,
            "source_type": "pdf_upload",
            "file_name": path.name,
        })

    # Step 2 — Chunk the documents into nodes
    splitter = SentenceSplitter(
        chunk_size=settings.chunk_size,
        chunk_overlap=settings.chunk_overlap,
    )
    nodes = splitter.get_nodes_from_documents(llama_docs)

    # Step 3 — Enrich node metadata (already set on parent docs, inherited by nodes)
    for node in nodes:
        node.metadata["document_id"] = document_id
        node.metadata["source_name"] = source_name or path.stem
        node.metadata["source_type"] = "pdf_upload"

    logger.info(f"Parsed {len(llama_docs)} section(s) into {len(nodes)} chunk(s)")

    # Step 4 — Index nodes into the vector store
    engine.add_nodes(nodes)

    # Step 5 — Return the doc ID for linking back in the DB
    return doc_id


async def _parse_pdf(file_path: str) -> list[LlamaDocument]:
    """
    Try LlamaParse first (cloud API for high-quality PDF parsing),
    fall back to simple local text extraction if unavailable.
    """
    # Try LlamaParse if API key is configured
    if settings.llama_cloud_api_key:
        try:
            from llama_parse import LlamaParse

            parser = LlamaParse(
                api_key=settings.llama_cloud_api_key,
                result_type="markdown",
            )
            documents = await parser.aload_data(file_path)
            if documents:
                logger.info(f"LlamaParse extracted {len(documents)} section(s)")
                return documents
        except Exception as e:
            logger.warning(f"LlamaParse failed, falling back to local parser: {e}")

    # Fallback: simple local PDF text extraction
    return _fallback_parse_pdf(file_path)


def _fallback_parse_pdf(file_path: str) -> list[LlamaDocument]:
    """
    Fallback PDF parser using PyPDF2 or pdfplumber for basic text extraction.
    Returns a list of LlamaIndex Document objects (one per page or full doc).
    """
    try:
        # Try pdfplumber for better table handling
        import pdfplumber

        documents = []
        with pdfplumber.open(file_path) as pdf:
            full_text = []
            for i, page in enumerate(pdf.pages):
                text = page.extract_text() or ""
                if text.strip():
                    full_text.append(f"--- Page {i + 1} ---\n{text}")

            if full_text:
                combined = "\n\n".join(full_text)
                documents.append(LlamaDocument(
                    text=combined,
                    metadata={"parser": "pdfplumber", "page_count": len(pdf.pages)},
                ))

        if documents:
            logger.info(f"pdfplumber extracted text from {file_path}")
            return documents

    except ImportError:
        logger.debug("pdfplumber not available, trying PyPDF2")
    except Exception as e:
        logger.warning(f"pdfplumber failed: {e}")

    # Final fallback: PyPDF2
    try:
        from PyPDF2 import PdfReader

        reader = PdfReader(file_path)
        full_text = []
        for i, page in enumerate(reader.pages):
            text = page.extract_text() or ""
            if text.strip():
                full_text.append(f"--- Page {i + 1} ---\n{text}")

        if full_text:
            combined = "\n\n".join(full_text)
            return [LlamaDocument(
                text=combined,
                metadata={"parser": "PyPDF2", "page_count": len(reader.pages)},
            )]

    except ImportError:
        logger.error("No PDF parser available. Install pdfplumber or PyPDF2.")
    except Exception as e:
        logger.error(f"PyPDF2 fallback failed: {e}")

    return []
