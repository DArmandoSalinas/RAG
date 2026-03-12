"""
Streamlit frontend — dark, minimalist Apple-style UI.
Calls FastAPI POST /upload and POST /query.
Run: streamlit run frontend/app.py
"""

from __future__ import annotations

import html
import os
from typing import Any

import httpx
import streamlit as st

API_BASE = os.getenv("API_BASE_URL", "http://127.0.0.1:8000").rstrip("/")

# --- Apple-style dark theme CSS ---
st.set_page_config(
    page_title="RAG Research Assistant",
    page_icon="",
    layout="wide",
    initial_sidebar_state="expanded",
)

APPLE_DARK_CSS = """
<style>
    /* Base */
    .stApp {
        background: #000000;
        color: #f5f5f7;
    }
    [data-testid="stSidebar"] {
        background: #1c1c1e;
        border-right: 1px solid #2c2c2e;
    }
    /* Typography */
    html, body, [class*="css"] {
        font-family: -apple-system, BlinkMacSystemFont, "SF Pro Text", "Segoe UI", sans-serif;
    }
    h1, h2, h3 {
        font-weight: 600;
        letter-spacing: -0.02em;
        color: #f5f5f7;
    }
    /* Inputs */
    .stTextInput input, .stTextArea textarea {
        background: #1c1c1e !important;
        border: 1px solid #3a3a3c !important;
        border-radius: 12px !important;
        color: #f5f5f7 !important;
    }
    /* Buttons */
    .stButton > button {
        background: #0a84ff !important;
        color: #fff !important;
        border: none !important;
        border-radius: 980px !important;
        font-weight: 500 !important;
        padding: 0.5rem 1.25rem !important;
    }
    .stButton > button:hover {
        background: #409cff !important;
    }
    /* File uploader */
    [data-testid="stFileUploader"] section {
        background: #1c1c1e;
        border: 1px dashed #3a3a3c;
        border-radius: 12px;
    }
    /* Chat bubbles */
    .chat-user {
        background: #2c2c2e;
        border-radius: 18px 18px 4px 18px;
        padding: 12px 16px;
        margin: 8px 0 8px 20%;
        color: #f5f5f7;
    }
    .chat-assistant {
        background: #1c1c1e;
        border: 1px solid #2c2c2e;
        border-radius: 18px 18px 18px 4px;
        padding: 12px 16px;
        margin: 8px 20% 8px 0;
        color: #e8e8ed;
    }
    /* Source viewer */
    .source-snippet {
        background: #1c1c1e;
        border-left: 3px solid #0a84ff;
        padding: 10px 14px;
        margin: 8px 0;
        border-radius: 0 8px 8px 0;
        font-size: 0.9rem;
        color: #aeaeb2;
    }
    .source-meta {
        font-size: 0.75rem;
        color: #636366;
        margin-bottom: 6px;
    }
    /* Expander */
    .streamlit-expanderHeader {
        background: #1c1c1e !important;
        border-radius: 10px !important;
    }
</style>
"""
st.markdown(APPLE_DARK_CSS, unsafe_allow_html=True)


def upload_pdf(file_bytes: bytes, filename: str) -> dict[str, Any]:
    with httpx.Client(timeout=120.0) as client:
        r = client.post(
            f"{API_BASE}/upload",
            files={"file": (filename, file_bytes, "application/pdf")},
        )
    r.raise_for_status()
    return r.json()


def query_api(question: str) -> dict[str, Any]:
    with httpx.Client(timeout=120.0) as client:
        r = client.post(
            f"{API_BASE}/query",
            json={"query": question},
        )
    r.raise_for_status()
    return r.json()


def main() -> None:
    st.sidebar.title("Documents")
    st.sidebar.caption("Upload PDFs to index. Chunks use 1000 / 100 overlap.")
    uploaded = st.sidebar.file_uploader(
        "PDF upload",
        type=["pdf"],
        label_visibility="collapsed",
    )
    if uploaded is not None:
        if st.sidebar.button("Index this PDF", use_container_width=True):
            with st.sidebar.status("Indexing…", expanded=True) as status:
                try:
                    data = upload_pdf(uploaded.getvalue(), uploaded.name)
                    status.update(
                        label=f"Indexed {data.get('chunks_indexed', 0)} chunks",
                        state="complete",
                    )
                    st.sidebar.success(f"{uploaded.name} ready.")
                except httpx.HTTPStatusError as e:
                    status.update(label="Failed", state="error")
                    st.sidebar.error(e.response.text or str(e))
                except Exception as e:
                    status.update(label="Failed", state="error")
                    st.sidebar.error(str(e))

    st.sidebar.divider()
    st.sidebar.markdown(f"**API** `{API_BASE}`")

    st.title("RAG Research Assistant")
    st.caption("Retrieval uses MultiQueryRetriever over ChromaDB · GPT-4o")

    if "messages" not in st.session_state:
        st.session_state.messages = []
    if "last_sources" not in st.session_state:
        st.session_state.last_sources = []

    # Render history (escape HTML in content)
    for msg in st.session_state.messages:
        safe = html.escape(msg["content"])
        if msg["role"] == "user":
            st.markdown(f'<div class="chat-user">{safe}</div>', unsafe_allow_html=True)
        else:
            st.markdown(f'<div class="chat-assistant">{safe}</div>', unsafe_allow_html=True)

    prompt = st.chat_input("Ask about your documents…")
    if prompt:
        st.session_state.messages.append({"role": "user", "content": prompt})

        with st.spinner("Retrieving context…"):
            try:
                result = query_api(prompt)
                answer = result.get("answer", "")
                sources = result.get("sources") or []
                st.session_state.last_sources = sources
            except httpx.ConnectError:
                answer = f"Cannot reach API at `{API_BASE}`. Start the backend: `uvicorn app.main:app --reload`"
                sources = []
                st.session_state.last_sources = []
            except httpx.HTTPStatusError as e:
                answer = e.response.text or str(e)
                sources = []
                st.session_state.last_sources = []
            except Exception as e:
                answer = str(e)
                sources = []
                st.session_state.last_sources = []

        st.session_state.messages.append({"role": "assistant", "content": answer})
        st.rerun()

    # Source viewer (last answer)
    if st.session_state.last_sources:
        with st.expander("Source viewer — snippets used for the last answer", expanded=False):
            for i, src in enumerate(st.session_state.last_sources, 1):
                meta = src.get("metadata") or {}
                meta_str = ", ".join(f"{k}: {v}" for k, v in meta.items() if v is not None)
                content = (src.get("content") or "").strip()
                preview = content[:1200] + ("…" if len(content) > 1200 else "")
                safe_preview = html.escape(preview)
                safe_meta = html.escape(meta_str)
                st.markdown(
                    f'<div class="source-meta">Source {i} · {safe_meta}</div>'
                    f'<div class="source-snippet">{safe_preview}</div>',
                    unsafe_allow_html=True,
                )


if __name__ == "__main__":
    main()
