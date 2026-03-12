"""
PDF loading and chunking using RecursiveCharacterTextSplitter.
"""

from __future__ import annotations

import os
import tempfile
from pathlib import Path
from typing import Any

from langchain_community.document_loaders import PyPDFLoader
from langchain_core.documents import Document
from langchain_text_splitters import RecursiveCharacterTextSplitter


class DocumentProcessor:
    """
    Handles PDF loading via PyPDF and chunking with fixed size/overlap.
    """

    DEFAULT_CHUNK_SIZE: int = 1000
    DEFAULT_CHUNK_OVERLAP: int = 100

    def __init__(
        self,
        chunk_size: int = DEFAULT_CHUNK_SIZE,
        chunk_overlap: int = DEFAULT_CHUNK_OVERLAP,
    ) -> None:
        self._chunk_size = chunk_size
        self._chunk_overlap = chunk_overlap
        self._splitter = RecursiveCharacterTextSplitter(
            chunk_size=chunk_size,
            chunk_overlap=chunk_overlap,
            length_function=len,
            separators=["\n\n", "\n", " ", ""],
        )

    @property
    def chunk_size(self) -> int:
        return self._chunk_size

    @property
    def chunk_overlap(self) -> int:
        return self._chunk_overlap

    def load_pdf(self, file_path: str | Path) -> list[Document]:
        """
        Load a PDF file and return LangChain Document objects (per page).
        """
        path = Path(file_path)
        if not path.exists():
            raise FileNotFoundError(f"PDF not found: {path}")
        if path.suffix.lower() != ".pdf":
            raise ValueError(f"Expected PDF file, got: {path.suffix}")

        loader = PyPDFLoader(str(path))
        return loader.load()

    def chunk_documents(
        self,
        documents: list[Document],
        extra_metadata: dict[str, Any] | None = None,
    ) -> list[Document]:
        """
        Split documents into chunks. Optionally merge extra_metadata into each chunk.
        """
        if extra_metadata:
            for doc in documents:
                doc.metadata = {**doc.metadata, **extra_metadata}
        return self._splitter.split_documents(documents)

    def process_pdf_file(
        self,
        file_path: str | Path,
        source_label: str | None = None,
    ) -> list[Document]:
        """
        Load PDF and return chunked documents with source metadata.
        """
        path = Path(file_path)
        label = source_label or path.name
        docs = self.load_pdf(path)
        return self.chunk_documents(
            docs,
            extra_metadata={"source": label, "source_path": str(path.resolve())},
        )

    def process_uploaded_bytes(
        self,
        content: bytes,
        filename: str,
    ) -> list[Document]:
        """
        Write uploaded bytes to a temp PDF, process, then remove temp file.
        """
        suffix = Path(filename).suffix.lower() or ".pdf"
        if suffix != ".pdf":
            raise ValueError("Only PDF uploads are supported.")

        with tempfile.NamedTemporaryFile(delete=False, suffix=".pdf") as tmp:
            tmp.write(content)
            tmp_path = tmp.name
        try:
            return self.process_pdf_file(tmp_path, source_label=filename)
        finally:
            if os.path.exists(tmp_path):
                os.unlink(tmp_path)
