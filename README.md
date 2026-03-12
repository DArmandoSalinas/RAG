# RAG Research Assistant

Production-style RAG app: **FastAPI** + **LangChain** (MultiQueryRetriever) + **ChromaDB** + **Streamlit** (dark UI). PDFs via **PyPDF**, embeddings **text-embedding-3-small**, chat **gpt-4o**.

## Layout

```
rag-research-assistant/
├── app/
│   ├── main.py              # FastAPI app
│   ├── core/
│   │   ├── document_processor.py   # PDF load + RecursiveCharacterTextSplitter (1000/100)
│   │   └── rag_manager.py         # Chroma + MultiQueryRetriever + RetrievalQA
│   └── api/
│       └── routes.py        # POST /upload, POST /query
├── frontend/
│   └── app.py               # Streamlit UI
├── data/                    # Chroma persistence (data/chroma)
├── requirements.txt
├── .env.example
└── README.md
```

## Setup

```bash
cd rag-research-assistant
python -m venv .venv
source .venv/bin/activate   # Windows: .venv\Scripts\activate
pip install -r requirements.txt
cp .env.example .env
# Edit .env — set OPENAI_API_KEY
```

## Run

**Terminal 1 — API**

```bash
cd rag-research-assistant
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

**Terminal 2 — UI**

```bash
cd rag-research-assistant
streamlit run frontend/app.py
```

Optional: `export API_BASE_URL=http://127.0.0.1:8000` if the API runs elsewhere.

## API

| Method | Path     | Description |
|--------|----------|-------------|
| POST   | `/upload` | Multipart `file` (PDF) → chunks indexed |
| POST   | `/query`  | JSON `{"query": "..."}` → `answer` + `sources[]` |
| GET    | `/health` | Basic health + vector count |

## Advanced RAG

`RAGManager` wraps **MultiQueryRetriever** so the LLM rewrites the user question into multiple queries before retrieval, improving recall on complex questions.

## Constraints

- API keys only via **`.env`** (see `.env.example`).
- Code is modular, **type-hinted**, and **PEP 8**-oriented.
