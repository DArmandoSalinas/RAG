"""
RAGManager: ChromaDB persistence, MultiQueryRetriever, and QA with sources.
Uses LCEL (no langchain.chains.RetrievalQA — removed in LangChain 0.3).
"""

from __future__ import annotations

import os
from pathlib import Path
from typing import Any

from langchain_core.documents import Document
from langchain_core.prompts import ChatPromptTemplate
from langchain_openai import ChatOpenAI, OpenAIEmbeddings
from langchain_chroma import Chroma

# LangChain 1.x: retrievers live in langchain-classic, not langchain.retrievers
try:
    from langchain_classic.retrievers.multi_query import MultiQueryRetriever
except ImportError:
    from langchain.retrievers.multi_query import MultiQueryRetriever  # type: ignore

from app.core.document_processor import DocumentProcessor


def _default_persist_dir() -> str:
    base = Path(__file__).resolve().parents[2]
    return str(base / "data" / "chroma")


def _format_docs(docs: list[Document]) -> str:
    return "\n\n".join(doc.page_content for doc in docs if doc.page_content)


def _chroma_safe_metadata(meta: dict[str, Any]) -> dict[str, Any]:
    """
    Chroma only accepts str, int, float, bool as metadata values.
    Coerce or drop everything else to avoid add_documents failures.
    """
    out: dict[str, Any] = {}
    for k, v in meta.items():
        if v is None:
            continue
        if isinstance(v, (str, int, float, bool)):
            out[k] = v
        else:
            out[k] = str(v)
    return out


def _sanitize_documents_for_chroma(documents: list[Document]) -> list[Document]:
    sanitized: list[Document] = []
    for doc in documents:
        safe_meta = _chroma_safe_metadata(dict(doc.metadata))
        sanitized.append(
            Document(page_content=doc.page_content, metadata=safe_meta)
        )
    return sanitized


class RAGManager:
    """
    Manages Chroma collection, MultiQueryRetriever, and prompt-based QA.
    """

    COLLECTION_NAME: str = "rag_research_assistant"

    _PROMPT = ChatPromptTemplate.from_messages(
        [
            (
                "system",
                "You are a precise assistant. Answer only using the context below. "
                "If the context is insufficient, say you don't know.",
            ),
            (
                "human",
                "Context:\n{context}\n\nQuestion: {question}",
            ),
        ]
    )

    def __init__(
        self,
        persist_directory: str | None = None,
        openai_api_key: str | None = None,
        chat_model: str | None = None,
        embedding_model: str | None = None,
    ) -> None:
        self._persist_directory = persist_directory or _default_persist_dir()
        self._api_key = (openai_api_key or os.getenv("OPENAI_API_KEY") or "").strip()
        if not self._api_key:
            raise ValueError("OPENAI_API_KEY is required (env or constructor).")
        if "your-key-here" in self._api_key or self._api_key == "sk-your-key-here":
            raise ValueError(
                "OPENAI_API_KEY is still the placeholder. Edit rag-research-assistant/.env "
                "and set OPENAI_API_KEY to your real key from "
                "https://platform.openai.com/api-keys — then restart uvicorn."
            )

        self._chat_model = chat_model or os.getenv(
            "OPENAI_CHAT_MODEL", "gpt-4o"
        )
        self._embedding_model = embedding_model or os.getenv(
            "OPENAI_EMBEDDING_MODEL", "text-embedding-3-small"
        )

        Path(self._persist_directory).mkdir(parents=True, exist_ok=True)

        self._embeddings = OpenAIEmbeddings(
            api_key=self._api_key,
            model=self._embedding_model,
        )
        self._llm = ChatOpenAI(
            api_key=self._api_key,
            model=self._chat_model,
            temperature=0,
        )

        self._vectorstore = Chroma(
            collection_name=self.COLLECTION_NAME,
            embedding_function=self._embeddings,
            persist_directory=self._persist_directory,
        )

        base_retriever = self._vectorstore.as_retriever(
            search_kwargs={"k": 6},
        )
        self._retriever = MultiQueryRetriever.from_llm(
            retriever=base_retriever,
            llm=self._llm,
        )

    @property
    def persist_directory(self) -> str:
        return self._persist_directory

    def add_documents(self, documents: list[Document]) -> list[str]:
        """Add chunked documents to the vector store; returns inserted IDs."""
        if not documents:
            return []
        documents = _sanitize_documents_for_chroma(documents)
        # Chroma/embeddings can fail on empty chunks
        documents = [d for d in documents if d.page_content and d.page_content.strip()]
        if not documents:
            raise ValueError(
                "All chunks were empty after sanitization; PDF may be image-only or unreadable."
            )
        ids = self._vectorstore.add_documents(documents)
        if hasattr(self._vectorstore, "persist"):
            try:
                self._vectorstore.persist()
            except Exception:
                pass
        if ids is None:
            return []
        return ids if isinstance(ids, list) else [str(ids)]

    def query(self, question: str) -> dict[str, Any]:
        """
        Run retrieval + generation. Returns answer and serializable source list.
        """
        if not question or not question.strip():
            raise ValueError("Question must be non-empty.")

        q = question.strip()
        # MultiQueryRetriever returns merged docs from multiple sub-queries
        try:
            source_docs = self._retriever.invoke(q)
        except TypeError:
            source_docs = self._retriever.get_relevant_documents(q)
        if not isinstance(source_docs, list):
            source_docs = list(source_docs) if source_docs else []

        context = _format_docs(source_docs)
        if not context.strip():
            return {
                "answer": "No relevant context was retrieved. Upload and index a PDF first.",
                "sources": [],
            }

        messages = self._PROMPT.format_messages(context=context, question=q)
        response = self._llm.invoke(messages)
        answer = getattr(response, "content", None) or str(response)

        sources: list[dict[str, Any]] = []
        for doc in source_docs:
            sources.append(
                {
                    "content": doc.page_content,
                    "metadata": dict(doc.metadata),
                }
            )

        return {
            "answer": answer,
            "sources": sources,
        }

    def document_count(self) -> int:
        """Approximate count of vectors in collection (if supported)."""
        try:
            coll = self._vectorstore._collection
            if coll is not None:
                return coll.count()
        except Exception:
            pass
        return 0
