"""
FastAPI application entrypoint.
Run: uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
"""

from __future__ import annotations

from pathlib import Path

# Load .env FIRST — before any code that reads OPENAI_API_KEY.
# override=True so values in .env replace anything already in the shell
# (e.g. an old exported OPENAI_API_KEY=sk-your-key-here).
_PROJECT_ROOT = Path(__file__).resolve().parents[1]
_ENV_FILE = _PROJECT_ROOT / ".env"

from dotenv import load_dotenv

load_dotenv(_ENV_FILE, override=True)

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api.routes import router

app = FastAPI(
    title="RAG Research Assistant",
    description="PDF upload + MultiQuery RAG with ChromaDB and OpenAI.",
    version="1.0.0",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(router, prefix="", tags=["rag"])


@app.get("/")
async def root():
    return {
        "service": "RAG Research Assistant",
        "docs": "/docs",
        "upload": "POST /upload (multipart PDF)",
        "query": 'POST /query JSON {"query": "..."}',
    }
