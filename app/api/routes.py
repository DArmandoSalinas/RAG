"""
FastAPI routes: POST /upload, POST /query.
"""

from __future__ import annotations

from typing import Annotated

from fastapi import APIRouter, File, HTTPException, UploadFile

from app.api.schemas import QueryRequest
from app.core.document_processor import DocumentProcessor
from app.core.rag_manager import RAGManager

router = APIRouter()

# Lazy singletons — initialized on first use after env is loaded
_rag_manager: RAGManager | None = None
_document_processor: DocumentProcessor | None = None


def get_rag_manager() -> RAGManager:
    global _rag_manager
    if _rag_manager is None:
        _rag_manager = RAGManager()
    return _rag_manager


def get_document_processor() -> DocumentProcessor:
    global _document_processor
    if _document_processor is None:
        _document_processor = DocumentProcessor()
    return _document_processor


@router.post("/upload")
async def upload_pdf(file: Annotated[UploadFile, File(description="PDF to index")]):
    """
    Accept a PDF, chunk it, and persist chunks into ChromaDB.
    """
    if not file.filename or not file.filename.lower().endswith(".pdf"):
        raise HTTPException(status_code=400, detail="Only PDF files are accepted.")

    content = await file.read()
    if not content:
        raise HTTPException(status_code=400, detail="Empty file.")

    processor = get_document_processor()
    try:
        chunks = processor.process_uploaded_bytes(content, file.filename)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e)) from e

    if not chunks:
        raise HTTPException(status_code=422, detail="No text could be extracted from the PDF.")

    try:
        manager = get_rag_manager()
        ids = manager.add_documents(chunks)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e)) from e
    except Exception as e:
        # Chroma/OpenAI errors surface here — return message so UI is not opaque
        raise HTTPException(
            status_code=500,
            detail=f"Indexing failed: {type(e).__name__}: {e}",
        ) from e

    return {
        "filename": file.filename,
        "chunks_indexed": len(chunks),
        "ids_count": len(ids),
    }


@router.post("/query")
async def query_rag(payload: QueryRequest):
    """
    Body: {"query": "your question"}
    Returns answer and sources (snippet + metadata).
    """
    question = payload.query.strip()
    if not question:
        raise HTTPException(status_code=400, detail="Query must be non-empty.")

    manager = get_rag_manager()
    try:
        result = manager.query(question)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e)) from e
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e)) from e

    return result


@router.get("/health")
async def health():
    """Liveness and optional vector store stats."""
    try:
        manager = get_rag_manager()
        count = manager.document_count()
    except Exception:
        count = None
    return {"status": "ok", "vector_count": count}
