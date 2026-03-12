"""
FastAPI application entrypoint.
Run: uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
"""

from __future__ import annotations

from pathlib import Path

from dotenv import load_dotenv
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api.routes import router

# Load .env from project root (parent of app/)
_env_path = Path(__file__).resolve().parents[1] / ".env"
load_dotenv(_env_path)

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
