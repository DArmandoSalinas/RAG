"""
Streamlit frontend — Apple-inspired RAG UI.
Run from project root: streamlit run frontend/app.py
"""

from __future__ import annotations

import html
import os
from typing import Any

import httpx
import streamlit as st

API_BASE = os.getenv("API_BASE_URL", "http://127.0.0.1:8000").rstrip("/")

st.set_page_config(
    page_title="RAG — Research",
    page_icon="◉",
    layout="wide",
    initial_sidebar_state="expanded",
    menu_items={"Get help": None, "Report a bug": None, "About": None},
)

# --- Design tokens (Apple dark palette + accent) ---
CSS = """
<style>
    :root {
        --bg-deep: #0a0a0b;
        --bg-elevated: rgba(28, 28, 30, 0.72);
        --bg-glass: rgba(44, 44, 46, 0.45);
        --border-subtle: rgba(255, 255, 255, 0.06);
        --border-strong: rgba(255, 255, 255, 0.10);
        --text-primary: #f5f5f7;
        --text-secondary: #a1a1a6;
        --text-tertiary: #636366;
        --accent: #0a84ff;
        --accent-soft: rgba(10, 132, 255, 0.15);
        --success: #30d158;
        --danger: #ff453a;
        --radius-lg: 20px;
        --radius-pill: 980px;
        --shadow-soft: 0 8px 32px rgba(0, 0, 0, 0.4);
    }

    /* App shell */
    .stApp {
        background: var(--bg-deep) !important;
        background-image:
            radial-gradient(ellipse 80% 50% at 50% -20%, rgba(10, 132, 255, 0.12), transparent),
            radial-gradient(ellipse 60% 40% at 100% 50%, rgba(88, 86, 214, 0.06), transparent) !important;
        color: var(--text-primary);
    }
    [data-testid="stAppViewContainer"] > .main {
        padding-top: 1.5rem;
    }
    #MainMenu {visibility: hidden;}
    footer {visibility: hidden;}
    header[data-testid="stHeader"] {
        background: transparent !important;
    }

    /* Sidebar — glass panel */
    [data-testid="stSidebar"] {
        background: linear-gradient(180deg, rgba(22, 22, 24, 0.95) 0%, rgba(14, 14, 15, 0.98) 100%) !important;
        border-right: 1px solid var(--border-subtle) !important;
    }
    [data-testid="stSidebar"] .block-container {
        padding-top: 1.25rem;
    }

    /* Typography */
    html, body, .stMarkdown, [class*="css"] {
        font-family: -apple-system, BlinkMacSystemFont, "SF Pro Text", "SF Pro Display", "Segoe UI", sans-serif !important;
        -webkit-font-smoothing: antialiased;
    }

    /* Headings */
    h1, h2, h3 {
        font-weight: 600;
        letter-spacing: -0.03em;
        color: var(--text-primary) !important;
    }

    /* Primary button — capsule */
    .stButton > button[kind="primary"],
    .stButton > button {
        background: var(--accent) !important;
        color: #fff !important;
        border: none !important;
        border-radius: var(--radius-pill) !important;
        font-weight: 590 !important;
        font-size: 0.9rem !important;
        padding: 0.55rem 1.35rem !important;
        transition: transform 0.15s ease, box-shadow 0.15s ease !important;
        box-shadow: 0 2px 12px rgba(10, 132, 255, 0.35);
    }
    .stButton > button:hover {
        background: #409cff !important;
        transform: scale(1.02);
    }

    /* Secondary / sidebar buttons */
    [data-testid="stSidebar"] .stButton > button {
        width: 100%;
        box-shadow: none;
    }

    /* File uploader — drop zone */
    [data-testid="stFileUploader"] section {
        background: var(--bg-glass) !important;
        border: 1px dashed var(--border-strong) !important;
        border-radius: var(--radius-lg) !important;
        padding: 1rem !important;
        transition: border-color 0.2s, background 0.2s;
    }
    [data-testid="stFileUploader"] section:hover {
        border-color: rgba(10, 132, 255, 0.4) !important;
        background: var(--accent-soft) !important;
    }

    /* Chat input area */
    [data-testid="stChatInput"] {
        border-radius: var(--radius-lg) !important;
    }
    [data-testid="stChatInput"] textarea {
        background: var(--bg-elevated) !important;
        border: 1px solid var(--border-subtle) !important;
        color: var(--text-primary) !important;
    }

    /* Alerts */
    .stSuccess, div[data-testid="stSuccess"] {
        background: rgba(48, 209, 88, 0.12) !important;
        border: 1px solid rgba(48, 209, 88, 0.25) !important;
        border-radius: 12px !important;
    }
    .stError {
        border-radius: 12px !important;
    }

    /* Expander — source drawer */
    .streamlit-expanderHeader {
        background: var(--bg-glass) !important;
        border: 1px solid var(--border-subtle) !important;
        border-radius: 14px !important;
        font-weight: 500 !important;
    }
    [data-testid="stExpander"] {
        border: none !important;
        background: transparent !important;
    }

    /* Custom blocks */
    .hero-title {
        font-size: 1.75rem;
        font-weight: 700;
        letter-spacing: -0.04em;
        margin-bottom: 0.25rem;
        background: linear-gradient(180deg, #fff 0%, #a1a1a6 100%);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        background-clip: text;
    }
    .hero-sub {
        color: var(--text-secondary);
        font-size: 0.9rem;
        margin-bottom: 1.5rem;
    }
    .status-pill {
        display: inline-flex;
        align-items: center;
        gap: 6px;
        padding: 4px 10px;
        border-radius: var(--radius-pill);
        font-size: 0.75rem;
        font-weight: 500;
        background: var(--bg-glass);
        border: 1px solid var(--border-subtle);
        color: var(--text-secondary);
    }
    .status-dot {
        width: 6px;
        height: 6px;
        border-radius: 50%;
        background: var(--text-tertiary);
    }
    .status-dot.ok { background: var(--success); box-shadow: 0 0 8px var(--success); }
    .status-dot.bad { background: var(--danger); }

    .msg-row {
        display: flex;
        margin-bottom: 14px;
        animation: fadeIn 0.25s ease;
    }
    .msg-row.user { justify-content: flex-end; }
    .msg-row.assistant { justify-content: flex-start; }
    .bubble {
        max-width: 78%;
        padding: 14px 18px;
        border-radius: 22px;
        line-height: 1.5;
        font-size: 0.95rem;
        white-space: pre-wrap;
        word-break: break-word;
    }
    .bubble.user {
        background: linear-gradient(145deg, #3a3a3c 0%, #2c2c2e 100%);
        border: 1px solid var(--border-subtle);
        color: var(--text-primary);
        border-bottom-right-radius: 6px;
    }
    .bubble.assistant {
        background: var(--bg-elevated);
        border: 1px solid var(--border-subtle);
        color: #e8e8ed;
        border-bottom-left-radius: 6px;
        box-shadow: var(--shadow-soft);
    }
    .bubble-label {
        font-size: 0.65rem;
        text-transform: uppercase;
        letter-spacing: 0.08em;
        color: var(--text-tertiary);
        margin-bottom: 6px;
        font-weight: 600;
    }

    .empty-state {
        text-align: center;
        padding: 3rem 2rem;
        color: var(--text-secondary);
        border: 1px dashed var(--border-subtle);
        border-radius: var(--radius-lg);
        margin: 2rem 0;
        background: var(--bg-glass);
    }
    .empty-state h3 {
        color: var(--text-primary);
        font-size: 1.1rem;
        margin-bottom: 0.5rem;
    }

    .source-card {
        background: var(--bg-elevated);
        border: 1px solid var(--border-subtle);
        border-radius: 14px;
        padding: 14px 16px;
        margin-bottom: 12px;
        border-left: 3px solid var(--accent);
    }
    .source-card-meta {
        font-size: 0.7rem;
        color: var(--text-tertiary);
        margin-bottom: 8px;
        font-weight: 500;
    }
    .source-card-body {
        font-size: 0.88rem;
        color: var(--text-secondary);
        line-height: 1.45;
    }

    .sidebar-brand {
        font-size: 0.7rem;
        font-weight: 600;
        letter-spacing: 0.12em;
        text-transform: uppercase;
        color: var(--text-tertiary);
        margin-bottom: 1rem;
    }

    @keyframes fadeIn {
        from { opacity: 0; transform: translateY(6px); }
        to { opacity: 1; transform: translateY(0); }
    }

    /* Divider subtle */
    hr, [data-testid="stSidebar"] hr {
        border-color: var(--border-subtle) !important;
        margin: 1.25rem 0;
    }
</style>
"""
st.markdown(CSS, unsafe_allow_html=True)


def _health() -> bool:
    try:
        with httpx.Client(timeout=3.0) as c:
            r = c.get(f"{API_BASE}/health")
            return r.status_code == 200
    except Exception:
        return False


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
    # --- Sidebar ---
    api_ok = _health()
    st.sidebar.markdown('<p class="sidebar-brand">Library</p>', unsafe_allow_html=True)
    st.sidebar.markdown(
        f'<span class="status-pill"><span class="status-dot {"ok" if api_ok else "bad"}"></span>'
        f'{"Connected" if api_ok else "Offline"} · {html.escape(API_BASE)}</span>',
        unsafe_allow_html=True,
    )
    st.sidebar.markdown("")  # spacer

    st.sidebar.markdown("**Add knowledge**")
    st.sidebar.caption("PDF only · chunks 1000 / overlap 100")
    uploaded = st.sidebar.file_uploader(
        "Drop PDF",
        type=["pdf"],
        label_visibility="collapsed",
        help="Upload a PDF to embed and query with RAG.",
    )

    if uploaded is not None:
        col1, col2 = st.sidebar.columns(2)
        with col1:
            if st.button("Index", use_container_width=True, type="primary"):
                with st.sidebar.status("Embedding…", expanded=True) as status:
                    try:
                        data = upload_pdf(uploaded.getvalue(), uploaded.name)
                        n = data.get("chunks_indexed", 0)
                        status.update(label=f"Indexed · {n} chunks", state="complete")
                        st.session_state["last_index_count"] = n
                        st.session_state["last_index_name"] = uploaded.name
                        st.sidebar.success(f"**{uploaded.name}** is ready to query.")
                    except httpx.HTTPStatusError as e:
                        status.update(label="Failed", state="error")
                        st.sidebar.error(e.response.text or str(e))
                    except Exception as e:
                        status.update(label="Failed", state="error")
                        st.sidebar.error(str(e))
        with col2:
            if st.button("Clear chat", use_container_width=True):
                st.session_state.messages = []
                st.session_state.last_sources = []
                st.rerun()

    if st.session_state.get("last_index_name"):
        st.sidebar.info(
            f"Last indexed: **{st.session_state['last_index_name']}** "
            f"({st.session_state.get('last_index_count', '?')} chunks)"
        )

    st.sidebar.divider()
    st.sidebar.caption("MultiQueryRetriever · ChromaDB · GPT-4o")

    # --- Main ---
    st.markdown('<p class="hero-title">Research Assistant</p>', unsafe_allow_html=True)
    st.markdown(
        '<p class="hero-sub">Ask in natural language — answers are grounded in your PDFs.</p>',
        unsafe_allow_html=True,
    )

    if "messages" not in st.session_state:
        st.session_state.messages = []
    if "last_sources" not in st.session_state:
        st.session_state.last_sources = []

    if not st.session_state.messages and not uploaded:
        st.markdown(
            """
            <div class="empty-state">
                <h3>No conversation yet</h3>
                <p>Index a PDF in the sidebar, then ask anything about it.<br/>
                Answers include retrievable source snippets.</p>
            </div>
            """,
            unsafe_allow_html=True,
        )

    for msg in st.session_state.messages:
        safe = html.escape(msg["content"])
        role = msg["role"]
        label = "You" if role == "user" else "Assistant"
        bubble_class = "user" if role == "user" else "assistant"
        st.markdown(
            f'<div class="msg-row {role}">'
            f'<div class="bubble {bubble_class}">'
            f'<div class="bubble-label">{label}</div>{safe}'
            f"</div></div>",
            unsafe_allow_html=True,
        )

    prompt = st.chat_input("Message…")
    if prompt:
        st.session_state.messages.append({"role": "user", "content": prompt})
        with st.spinner("Retrieving & reasoning…"):
            try:
                result = query_api(prompt)
                answer = result.get("answer", "")
                st.session_state.last_sources = result.get("sources") or []
            except httpx.ConnectError:
                answer = (
                    f"Can't reach **{API_BASE}**. Start the API:\n\n"
                    "`uvicorn app.main:app --reload --port 8050`"
                )
                st.session_state.last_sources = []
            except httpx.HTTPStatusError as e:
                answer = e.response.text or str(e)
                st.session_state.last_sources = []
            except Exception as e:
                answer = str(e)
                st.session_state.last_sources = []

        st.session_state.messages.append({"role": "assistant", "content": answer})
        st.rerun()

    # Sources — collapsible stack
    if st.session_state.last_sources:
        with st.expander(
            f"Sources · {len(st.session_state.last_sources)} snippets used",
            expanded=False,
        ):
            for i, src in enumerate(st.session_state.last_sources, 1):
                meta = src.get("metadata") or {}
                meta_str = " · ".join(
                    f"{k}: {v}" for k, v in list(meta.items())[:4] if v is not None
                )
                content = (src.get("content") or "").strip()
                preview = content[:1000] + ("…" if len(content) > 1000 else "")
                st.markdown(
                    f'<div class="source-card">'
                    f'<div class="source-card-meta">Source {i}</div>'
                    f'<div class="source-card-meta">{html.escape(meta_str)}</div>'
                    f'<div class="source-card-body">{html.escape(preview)}</div>'
                    f"</div>",
                    unsafe_allow_html=True,
                )


if __name__ == "__main__":
    main()
