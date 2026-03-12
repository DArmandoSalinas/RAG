# Personal Research Assistant (RAG)

A **source-grounded** research assistant: upload **PDFs**, index them locally, then **chat** with answers tied to **your documents** — with **visible snippets** for every reply.

**Stack:** FastAPI · LangChain (MultiQueryRetriever) · ChromaDB · OpenAI (GPT-4o + `text-embedding-3-small`) · Streamlit · PyPDF.

**Repository:** [github.com/DArmandoSalinas/RAG](https://github.com/DArmandoSalinas/RAG)

---

## What you can do

| Action | How |
|--------|-----|
| **Index a PDF** | Sidebar → upload PDF → **Index this PDF** |
| **Ask questions** | Type in the chat — answers use only indexed content |
| **Verify answers** | Open **Sources** under each reply to see the exact PDF fragments used |
| **Start over** | **New conversation** or **Refresh conversation** clears the thread (not the index) |

---

## Prerequisites

- **Python 3.11 or 3.12** (recommended; 3.14 may show LangChain warnings)
- **OpenAI API key** with [billing enabled](https://platform.openai.com/settings/organization/billing)
- **Git** (to clone)

---

## Quick start

### 1. Clone and enter the project

```bash
git clone https://github.com/DArmandoSalinas/RAG.git
cd RAG
```

### 2. Create a virtual environment

```bash
python3 -m venv .venv
source .venv/bin/activate          # Windows: .venv\Scripts\activate
pip install --upgrade pip
pip install -r requirements.txt
```

### 3. Configure environment variables

```bash
cp .env.example .env
```

Edit **`.env`** in the project root (same folder as `app/`):

```env
OPENAI_API_KEY=sk-your-real-key-here
```

- Use your **real** key from [OpenAI API keys](https://platform.openai.com/api-keys).
- Do **not** commit `.env` — it is listed in `.gitignore`.
- If you previously ran `export OPENAI_API_KEY=sk-your-key-here` in the terminal, run `unset OPENAI_API_KEY` or open a new terminal so `.env` wins (the app loads `.env` with `override=True` on startup).

Optional overrides in `.env`:

```env
OPENAI_CHAT_MODEL=gpt-4o
OPENAI_EMBEDDING_MODEL=text-embedding-3-small
```

### 4. Run the API (Terminal 1)

From the **project root** (where `app/` lives):

```bash
cd RAG
source .venv/bin/activate
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

- API docs: **http://127.0.0.1:8000/docs**
- Health check: **http://127.0.0.1:8000/health**

If **port 8000 is already in use**:

```bash
uvicorn app.main:app --reload --host 0.0.0.0 --port 8050
```

### 5. Run the UI (Terminal 2)

```bash
cd RAG
source .venv/bin/activate
streamlit run frontend/app.py
```

Streamlit must be run from the **project root** so `frontend/app.py` resolves correctly.

If the API is **not** on port 8000, set the base URL before starting Streamlit:

```bash
export API_BASE_URL=http://127.0.0.1:8050
streamlit run frontend/app.py
```

Open the URL Streamlit prints (usually **http://localhost:8501**).

### 6. Use the app

1. Wait until the sidebar shows **Online** (API reachable).
2. **Upload a PDF** → click **Index this PDF** and wait until indexing succeeds.
3. **Ask anything** about the document in the chat input.
4. Expand **Sources used in the last answer** to inspect snippets.

---

## Project layout

```
RAG/
├── app/
│   ├── main.py                 # FastAPI entry; loads .env first
│   ├── core/
│   │   ├── document_processor.py   # PyPDF + chunking (1000 / 100 overlap)
│   │   └── rag_manager.py          # Chroma + MultiQueryRetriever + QA
│   └── api/
│       ├── routes.py           # POST /upload, POST /query
│       └── schemas.py
├── frontend/
│   └── app.py                  # Streamlit UI (Personal Research Assistant)
├── data/                       # Chroma persistence (data/chroma)
├── requirements.txt
├── .env.example
└── README.md
```

---

## API reference

| Method | Path | Description |
|--------|------|-------------|
| `POST` | `/upload` | Multipart form field `file` (PDF). Indexes chunks into Chroma. |
| `POST` | `/query` | JSON body `{"query": "your question"}`. Returns `answer` + `sources[]`. |
| `GET` | `/health` | Liveness and optional vector count. |

Example query:

```bash
curl -s -X POST http://127.0.0.1:8000/query \
  -H "Content-Type: application/json" \
  -d '{"query": "What is this document about?"}'
```

---

## Troubleshooting

| Problem | What to try |
|--------|-------------|
| **401 Incorrect API key** | Put the real key in `.env`; restart uvicorn; `unset OPENAI_API_KEY` if the shell still has a placeholder. |
| **ModuleNotFoundError: langchain.retrievers** | `pip install langchain-classic` — retrievers live there in LangChain 1.x. |
| **Address already in use** | Use another port (e.g. 8050) and set `API_BASE_URL` for Streamlit. |
| **Streamlit: File does not exist: frontend/app.py** | `cd` into the project root before `streamlit run frontend/app.py`. |
| **No text extracted from PDF** | PDF may be image-only; use OCR’d PDFs or text-based PDFs. |
| **Indexing failed (metadata)** | Metadata is sanitized for Chroma; if it still fails, check the `detail` JSON in the UI or uvicorn logs. |

---

## Advanced behavior

- **MultiQueryRetriever** rewrites the user question into several retrieval queries to improve recall.
- **Chunks** default to size **1000** with overlap **100** (see `DocumentProcessor`).
- **Vector store** persists under **`data/chroma/`** (ignored by git by default).

---

## License / contributing

This repo is intended as a portfolio / learning project. Forks and PRs welcome.

---

## Summary

1. Clone → venv → `pip install -r requirements.txt`
2. Copy `.env.example` → `.env` → set **OPENAI_API_KEY**
3. **Terminal 1:** `uvicorn app.main:app --reload --port 8000` (or 8050)
4. **Terminal 2:** `streamlit run frontend/app.py` (set `API_BASE_URL` if not 8000)
5. Index PDFs in the sidebar, then chat — answers include **Sources** you can verify.
