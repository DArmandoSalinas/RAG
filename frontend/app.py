"""
Streamlit frontend — Personal Research Assistant (conversation-first UI).
Run from project root: streamlit run frontend/app.py
"""

from __future__ import annotations

import html
import os
from datetime import datetime
from typing import Any

import httpx
import streamlit as st

API_BASE = os.getenv("API_BASE_URL", "http://127.0.0.1:8000").rstrip("/")

PRODUCT_NAME = "Personal Research Assistant"
TAGLINE = "Your private researcher — reads your PDFs, cites sources, answers like a conversation."

st.set_page_config(
    page_title=f"{PRODUCT_NAME}",
    page_icon="📚",
    layout="wide",
    initial_sidebar_state="expanded",
    menu_items={"Get help": None, "Report a bug": None, "About": None},
)

CSS = """
<style>
    :root {
        --bg-deep: #0a0a0b;
        --bg-elevated: rgba(28, 28, 30, 0.85);
        --bg-glass: rgba(44, 44, 46, 0.5);
        --border-subtle: rgba(255, 255, 255, 0.06);
        --border-strong: rgba(255, 255, 255, 0.12);
        --text-primary: #f5f5f7;
        --text-secondary: #a1a1a6;
        --text-tertiary: #636366;
        --accent: #0a84ff;
        --accent-soft: rgba(10, 132, 255, 0.18);
        --success: #30d158;
        --danger: #ff453a;
        --radius-lg: 20px;
        --radius-pill: 980px;
        --shadow-soft: 0 8px 32px rgba(0, 0, 0, 0.45);
    }

    .stApp {
        background: var(--bg-deep) !important;
        background-image:
            radial-gradient(ellipse 90% 60% at 50% -15%, rgba(10, 132, 255, 0.14), transparent),
            radial-gradient(ellipse 50% 35% at 90% 80%, rgba(175, 82, 222, 0.08), transparent) !important;
        color: var(--text-primary);
    }
    [data-testid="stAppViewContainer"] > .main { padding-top: 1rem; }
    #MainMenu, footer { visibility: hidden; }
    header[data-testid="stHeader"] { background: transparent !important; }

    [data-testid="stSidebar"] {
        background: linear-gradient(195deg, rgba(24, 24, 26, 0.96) 0%, rgba(12, 12, 14, 0.99) 100%) !important;
        border-right: 1px solid var(--border-subtle) !important;
    }

    html, body, .stMarkdown, [class*="css"] {
        font-family: -apple-system, BlinkMacSystemFont, "SF Pro Text", "SF Pro Display", "Segoe UI", sans-serif !important;
        -webkit-font-smoothing: antialiased;
    }

    .stButton > button {
        background: var(--accent) !important;
        color: #fff !important;
        border: none !important;
        border-radius: var(--radius-pill) !important;
        font-weight: 600 !important;
        font-size: 0.88rem !important;
        padding: 0.5rem 1.2rem !important;
        transition: transform 0.15s ease, box-shadow 0.15s !important;
    }
    .stButton > button:hover { transform: scale(1.02); background: #409cff !important; }
    [data-testid="stSidebar"] .stButton > button { width: 100%; }

    /* Secondary outline button */
    div[data-testid="column"] .stButton > button[kind="secondary"],
    .btn-refresh button {
        background: transparent !important;
        border: 1px solid var(--border-strong) !important;
        color: var(--text-primary) !important;
        box-shadow: none !important;
    }

    [data-testid="stFileUploader"] section {
        background: var(--bg-glass) !important;
        border: 1px dashed var(--border-strong) !important;
        border-radius: var(--radius-lg) !important;
        padding: 1rem !important;
    }
    [data-testid="stFileUploader"] section:hover {
        border-color: rgba(10, 132, 255, 0.45) !important;
        background: var(--accent-soft) !important;
    }

    [data-testid="stChatInput"] textarea {
        background: var(--bg-elevated) !important;
        border: 1px solid var(--border-subtle) !important;
        color: var(--text-primary) !important;
        border-radius: 16px !important;
    }

    .streamlit-expanderHeader {
        background: var(--bg-glass) !important;
        border: 1px solid var(--border-subtle) !important;
        border-radius: 14px !important;
    }

    /* —— Brand hero —— */
    .brand-badge {
        display: inline-block;
        font-size: 0.65rem;
        font-weight: 700;
        letter-spacing: 0.14em;
        text-transform: uppercase;
        color: var(--accent);
        background: var(--accent-soft);
        padding: 5px 12px;
        border-radius: var(--radius-pill);
        margin-bottom: 10px;
        border: 1px solid rgba(10, 132, 255, 0.25);
    }
    .brand-title {
        font-size: 1.85rem;
        font-weight: 750;
        letter-spacing: -0.045em;
        line-height: 1.15;
        margin: 0 0 8px 0;
        background: linear-gradient(180deg, #ffffff 0%, #c7c7cc 100%);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        background-clip: text;
    }
    .brand-tagline {
        color: var(--text-secondary);
        font-size: 0.95rem;
        line-height: 1.5;
        max-width: 520px;
        margin-bottom: 0;
    }

    .thread-header {
        display: flex;
        align-items: center;
        justify-content: space-between;
        flex-wrap: wrap;
        gap: 10px;
        margin-bottom: 16px;
        padding-bottom: 12px;
        border-bottom: 1px solid var(--border-subtle);
    }
    .thread-title {
        font-size: 0.8rem;
        font-weight: 600;
        color: var(--text-secondary);
        letter-spacing: 0.04em;
    }
    .thread-meta {
        font-size: 0.75rem;
        color: var(--text-tertiary);
    }

    /* —— Messages —— */
    .msg-row {
        display: flex;
        margin-bottom: 16px;
        align-items: flex-start;
        gap: 12px;
        animation: fadeIn 0.28s ease;
    }
    .msg-row.user { flex-direction: row-reverse; }
    .avatar {
        width: 36px;
        height: 36px;
        border-radius: 50%;
        flex-shrink: 0;
        display: flex;
        align-items: center;
        justify-content: center;
        font-size: 1rem;
        font-weight: 700;
    }
    .avatar.user {
        background: linear-gradient(145deg, #48484a, #3a3a3c);
        border: 1px solid var(--border-subtle);
        color: #e8e8ed;
    }
    .avatar.assistant {
        background: linear-gradient(145deg, rgba(10,132,255,0.35), rgba(10,132,255,0.12));
        border: 1px solid rgba(10, 132, 255, 0.35);
        color: #fff;
    }
    .bubble-wrap { max-width: calc(100% - 48px); flex: 1; }
    .msg-row.user .bubble-wrap { display: flex; justify-content: flex-end; }
    .bubble {
        max-width: 85%;
        padding: 14px 18px;
        border-radius: 20px;
        line-height: 1.55;
        font-size: 0.94rem;
        white-space: pre-wrap;
        word-break: break-word;
    }
    .bubble.user {
        background: linear-gradient(160deg, #3a3a3c 0%, #2c2c2e 100%);
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
        font-size: 0.62rem;
        text-transform: uppercase;
        letter-spacing: 0.1em;
        color: var(--text-tertiary);
        margin-bottom: 8px;
        font-weight: 700;
    }

    .welcome-bubble {
        border-left: 3px solid var(--accent);
        padding-left: 14px;
        margin-bottom: 18px;
    }
    .welcome-bubble p {
        color: var(--text-secondary);
        font-size: 0.92rem;
        line-height: 1.55;
        margin: 0;
    }
    .welcome-bubble strong { color: var(--text-primary); }

    .empty-state {
        text-align: center;
        padding: 2.5rem 1.5rem;
        color: var(--text-secondary);
        border: 1px dashed var(--border-subtle);
        border-radius: var(--radius-lg);
        background: var(--bg-glass);
    }
    .empty-state h3 {
        color: var(--text-primary);
        font-size: 1.05rem;
        margin-bottom: 8px;
    }

    .source-card {
        background: var(--bg-elevated);
        border: 1px solid var(--border-subtle);
        border-radius: 14px;
        padding: 14px 16px;
        margin-bottom: 12px;
        border-left: 3px solid var(--accent);
    }
    .source-card-meta { font-size: 0.7rem; color: var(--text-tertiary); margin-bottom: 6px; }
    .source-card-body { font-size: 0.87rem; color: var(--text-secondary); line-height: 1.45; }

    .sidebar-brand {
        font-size: 0.68rem;
        font-weight: 700;
        letter-spacing: 0.14em;
        text-transform: uppercase;
        color: var(--text-tertiary);
        margin-bottom: 8px;
    }
    .status-pill {
        display: inline-flex;
        align-items: center;
        gap: 6px;
        padding: 5px 11px;
        border-radius: var(--radius-pill);
        font-size: 0.72rem;
        font-weight: 600;
        background: var(--bg-glass);
        border: 1px solid var(--border-subtle);
        color: var(--text-secondary);
    }
    .status-dot { width: 6px; height: 6px; border-radius: 50%; background: var(--text-tertiary); }
    .status-dot.ok { background: var(--success); box-shadow: 0 0 8px var(--success); }
    .status-dot.bad { background: var(--danger); }

    @keyframes fadeIn {
        from { opacity: 0; transform: translateY(8px); }
        to { opacity: 1; transform: translateY(0); }
    }
    hr, [data-testid="stSidebar"] hr { border-color: var(--border-subtle) !important; }
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


def _new_conversation() -> None:
    st.session_state.messages = []
    st.session_state.last_sources = []
    st.session_state.thread_id = (st.session_state.get("thread_id") or 0) + 1
    st.session_state.thread_started = datetime.now().strftime("%b %d, %Y · %H:%M")


def main() -> None:
    if "messages" not in st.session_state:
        st.session_state.messages = []
    if "last_sources" not in st.session_state:
        st.session_state.last_sources = []
    if "thread_id" not in st.session_state:
        st.session_state.thread_id = 1
        st.session_state.thread_started = datetime.now().strftime("%b %d, %Y · %H:%M")

    api_ok = _health()

    # —— Sidebar ——
    st.sidebar.markdown('<p class="sidebar-brand">Your library</p>', unsafe_allow_html=True)
    st.sidebar.markdown(
        f'<span class="status-pill"><span class="status-dot {"ok" if api_ok else "bad"}"></span>'
        f'{"Online" if api_ok else "Offline"} · {html.escape(API_BASE)}</span>',
        unsafe_allow_html=True,
    )
    st.sidebar.markdown("")

    if st.sidebar.button("New conversation", use_container_width=True, help="Clear this thread and start fresh"):
        _new_conversation()
        st.rerun()

    st.sidebar.divider()
    st.sidebar.markdown("**Teach your assistant**")
    st.sidebar.caption("Upload PDFs — it will answer only from what you’ve indexed.")
    uploaded = st.sidebar.file_uploader(
        "PDF",
        type=["pdf"],
        label_visibility="collapsed",
    )
    if uploaded is not None and st.sidebar.button("Index this PDF", use_container_width=True, type="primary"):
        with st.sidebar.status("Reading & embedding…", expanded=True) as status:
            try:
                data = upload_pdf(uploaded.getvalue(), uploaded.name)
                n = data.get("chunks_indexed", 0)
                status.update(label=f"Done — {n} chunks", state="complete")
                st.session_state["last_index_count"] = n
                st.session_state["last_index_name"] = uploaded.name
                st.sidebar.success(f"**{uploaded.name}** is now part of your research memory.")
            except httpx.HTTPStatusError as e:
                status.update(label="Failed", state="error")
                st.sidebar.error(e.response.text or str(e))
            except Exception as e:
                status.update(label="Failed", state="error")
                st.sidebar.error(str(e))

    if st.session_state.get("last_index_name"):
        st.sidebar.info(
            f"**In memory:** {st.session_state['last_index_name']} "
            f"· {st.session_state.get('last_index_count', '?')} segments"
        )

    st.sidebar.divider()
    st.sidebar.caption("RAG · ChromaDB · GPT-4o · Source-backed answers")

    # —— Main: brand ——
    st.markdown(
        f'<span class="brand-badge">Private · Source-grounded</span>',
        unsafe_allow_html=True,
    )
    st.markdown(f'<h1 class="brand-title">{html.escape(PRODUCT_NAME)}</h1>', unsafe_allow_html=True)
    st.markdown(f'<p class="brand-tagline">{html.escape(TAGLINE)}</p>', unsafe_allow_html=True)

    # Thread header + refresh (always visible when there are messages or after first load)
    col_a, col_b = st.columns([3, 1])
    with col_a:
        n_msgs = len(st.session_state.messages)
        st.markdown(
            f'<div class="thread-header" style="border:none;padding:0;margin:12px 0 8px 0;">'
            f'<span class="thread-title">Conversation</span>'
            f'<span class="thread-meta">Thread #{st.session_state.thread_id} · '
            f'{st.session_state.thread_started} · {n_msgs} messages</span></div>',
            unsafe_allow_html=True,
        )
    with col_b:
        if st.button("Refresh conversation", key="refresh_conv", use_container_width=True):
            _new_conversation()
            st.rerun()

    # Conversation area (Streamlit blocks don’t nest HTML — shell is visual only via spacing)
    has_indexed = bool(st.session_state.get("last_index_name"))
    if not st.session_state.messages:
        if has_indexed:
            st.markdown(
                """
                <div class="welcome-bubble">
                    <p><strong>Hi — I’m ready.</strong> I’ve read what you indexed. Ask me anything:
                    summaries, definitions, comparisons, or “where does it say…?” — I’ll answer from
                    your PDFs and you can open <strong>Sources</strong> below each reply to see the exact snippets.</p>
                </div>
                """,
                unsafe_allow_html=True,
            )
        else:
            st.markdown(
                """
                <div class="empty-state">
                    <h3>Start by feeding me a PDF</h3>
                    <p>Use the sidebar to upload and index a document.<br/>
                    Then chat here — every answer stays tied to <strong>your</strong> sources.</p>
                </div>
                """,
                unsafe_allow_html=True,
            )
    else:
        st.markdown(
            '<div style="height:1px;background:rgba(255,255,255,0.08);margin:8px 0 18px 0;"></div>',
            unsafe_allow_html=True,
        )
        for msg in st.session_state.messages:
            safe = html.escape(msg["content"])
            role = msg["role"]
            emoji = "●" if role == "user" else "◉"
            bubble_class = "user" if role == "user" else "assistant"
            label = "You" if role == "user" else PRODUCT_NAME.split()[0] + " Researcher"  # "Personal" -> use "Assistant"
            if role == "assistant":
                label = "Your researcher"
            st.markdown(
                f'<div class="msg-row {role}">'
                f'<div class="avatar {role}">{emoji}</div>'
                f'<div class="bubble-wrap"><div class="bubble {bubble_class}">'
                f'<div class="bubble-label">{label}</div>{safe}</div></div></div>',
                unsafe_allow_html=True,
            )

    prompt = st.chat_input("Ask your researcher…")
    if prompt:
        st.session_state.messages.append({"role": "user", "content": prompt})
        with st.spinner("Searching your documents and composing an answer…"):
            try:
                result = query_api(prompt)
                answer = result.get("answer", "")
                st.session_state.last_sources = result.get("sources") or []
            except httpx.ConnectError:
                answer = (
                    f"I can’t reach the API at `{API_BASE}`. Start the backend, then try again."
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

    if st.session_state.last_sources:
        with st.expander(
            f"Sources used in the last answer ({len(st.session_state.last_sources)} snippets)",
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
                    f'<div class="source-card-meta">Fragment {i}</div>'
                    f'<div class="source-card-meta">{html.escape(meta_str)}</div>'
                    f'<div class="source-card-body">{html.escape(preview)}</div></div>',
                    unsafe_allow_html=True,
                )


if __name__ == "__main__":
    main()
