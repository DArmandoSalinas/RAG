"""
RAGManager: ChromaDB persistence, MultiQueryRetriever, and QA chain with sources.
"""

from __future__ import annotations

import os
from pathlib import Path
from typing import Any

from langchain.chains.retrieval_qa.base import RetrievalQA
from langchain_core.documents import Document
from langchain_openai import ChatOpenAI, OpenAIEmbeddings
from langchain_chroma import Chroma
from langchain.retrievers.multi_query import MultiQueryRetriever

from app.core.document_processor import DocumentProcessor


def _default_persist_dir() -> str:
    base = Path(__file__).resolve().parents[2]
    return str(base / "data" / "chroma")


class RAGManager:
    """
    Manages Chroma collection, MultiQueryRetriever, and RetrievalQA chain.
    """

    COLLECTION_NAME: str = "rag_research_assistant"

    def __init__(
        self,
        persist_directory: str | None = None,
        openai_api_key: str | None = None,
        chat_model: str | None = None,
        embedding_model: str | None = None,
    ) -> None:
        self._persist_directory = persist_directory or _default_persist_dir()
        self._api_key = openai_api_key or os.getenv("OPENAI_API_KEY")
        if not self._api_key:
            raise ValueError("OPENAI_API_KEY is required (env or constructor).")

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

        self._qa_chain = RetrievalQA.from_chain_type(
            llm=self._llm,
            chain_type="stuff",
            retriever=self._retriever,
            return_source_documents=True,
        )

    @property
    def persist_directory(self) -> str:
        return self._persist_directory

    def add_documents(self, documents: list[Document]) -> list[str]:
        """Add chunked documents to the vector store; returns inserted IDs."""
        if not documents:
            return []
        ids = self._vectorstore.add_documents(documents)
        # Chroma persists automatically when persist_directory is set
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

        result = self._qa_chain.invoke({"query": question.strip()})
        answer = result.get("result", "")
        source_docs: list[Document] = result.get("source_documents") or []

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
