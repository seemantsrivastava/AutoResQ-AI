import os, sqlite3, datetime
import streamlit as st
from dotenv import load_dotenv
import pandas as pd

# Optional import for FAISS
try:
    from app.rag_engine.embeddings_faiss import build_faiss_from_docs
except Exception:
    build_faiss_from_docs = None

# ----------------------------
# Setup
# ----------------------------
load_dotenv()
DB_PATH = os.getenv("DATABASE_PATH", "../data/autoresq.db")
DATA_DIR = os.getenv("DATA_DIR", "rag_engine/data")

st.set_page_config(page_title="AutoResQ Dashboard", layout="wide")

# ----------------------------
# ✨ Custom CSS (Glassy Look)
# ----------------------------
st.markdown("""
<style>
/* ======= GLOBAL LAYOUT ======= */
.stApp {
    background: radial-gradient(circle at 25% 20%, #05080D, #010304 80%);
    color: #EAEAEA;
    font-family: 'Segoe UI', 'Roboto', sans-serif;
}

/* ======= GLASS PANELS ======= */
.main-container {
    background: rgba(10, 15, 25, 0.6);
    border: 1px solid rgba(0, 255, 255, 0.15);
    border-radius: 20px;
    padding: 25px 30px;
    box-shadow: 0 0 25px rgba(0, 255, 255, 0.1);
    backdrop-filter: blur(16px);
    transition: 0.3s ease-in-out;
}
.main-container:hover {
    box-shadow: 0 0 30px rgba(0,255,255,0.25);
}

/* ======= HEADINGS ======= */
h1, h2, h3, h4 {
    color: #00FFFF !important;
    text-shadow: 0 0 10px rgba(0,255,255,0.4);
    font-weight: 600;
    letter-spacing: 0.5px;
}

/* ======= SUBTEXT ======= */
p, label, span, div {
    color: #C8D4D4 !important;
}

/* ======= INCIDENT DATA ======= */
.dataframe {
    color: #D0E7E7 !important;
    font-weight: 500;
}
[data-testid="stDataFrame"] {
    background: rgba(20,25,35,0.85) !important;
    border-radius: 12px !important;
    box-shadow: 0 0 25px rgba(0,255,255,0.08);
    color: #E5F2F2 !important;
}

/* Make text darker and bolder for incident details */
div[data-testid="stMarkdownContainer"] p,
div[data-testid="stMarkdownContainer"] code,
div[data-testid="stMarkdownContainer"] span {
    color: #D8E0E3 !important;
    font-weight: 600;
}

/* ======= BUTTONS ======= */
.stButton>button {
    background: linear-gradient(90deg, #00E6FF, #007BFF);
    border: none;
    border-radius: 10px;
    color: white;
    font-weight: 500;
    box-shadow: 0 0 10px rgba(0,255,255,0.3);
    transition: 0.25s;
}
.stButton>button:hover {
    transform: scale(1.05);
    box-shadow: 0 0 20px rgba(0,255,255,0.6);
}

/* ======= TAB BAR ======= */
div[data-baseweb="tab-list"] {
    justify-content: center;
    border-radius: 12px;
    background: rgba(255,255,255,0.05);
    box-shadow: 0 0 15px rgba(0,255,255,0.08);
}
div[data-baseweb="tab"] {
    color: #00FFFF !important;
    font-weight: 600;
}
div[data-baseweb="tab"]:hover {
    background: rgba(0,255,255,0.05);
}

/* ======= CODE BLOCKS ======= */
code {
    color: #00E6FF !important;
    background: rgba(255,255,255,0.03);
    border-left: 3px solid #00FFFF;
    padding-left: 6px;
    border-radius: 4px;
}

/* ======= DIVIDERS ======= */
hr, .stDivider {
    border: none;
    height: 1px;
    background: linear-gradient(90deg, transparent, rgba(0,255,255,0.4), transparent);
}

/* ======= SCROLLBAR ======= */
::-webkit-scrollbar {
    width: 8px;
}
::-webkit-scrollbar-thumb {
    background: rgba(0,255,255,0.3);
    border-radius: 10px;
}
</style>
""", unsafe_allow_html=True)

# ----------------------------
# Header
# ----------------------------
st.markdown("""
<div class="main-container" style="text-align:center;">
    <h1>🚨 AutoResQ</h1>
    <h3>The AI-Powered Incident Copilot</h3>
    <p style="color:#CCCCCC;">Smart Triage · Root Cause Insights · Automated Recovery</p>
</div>
""", unsafe_allow_html=True)

# ----------------------------
# Database Helpers
# ----------------------------
@st.cache_resource
def get_conn():
    conn = sqlite3.connect(DB_PATH, check_same_thread=False)
    conn.row_factory = sqlite3.Row
    return conn

def load_events():
    conn = get_conn()
    cur = conn.execute("SELECT id, received_at, event_type, summary, service, status FROM events ORDER BY id DESC")
    return [dict(r) for r in cur.fetchall()]

def get_event(event_id: int):
    conn = get_conn()
    cur = conn.execute("SELECT * FROM events WHERE id=?", (event_id,))
    r = cur.fetchone()
    return dict(r) if r else None

def update_status(event_id: int, status: str):
    conn = get_conn()
    with conn:
        conn.execute("UPDATE events SET status=? WHERE id=?", (status, event_id))

def add_action(event_id: int, action: str):
    conn = get_conn()
    with conn:
        conn.execute(
            "INSERT INTO actions(event_id, action, created_at) VALUES(?,?,?)",
            (event_id, action, datetime.datetime.utcnow().isoformat())
        )

# ----------------------------
# Tabs for Incidents and RAG Upload
# ----------------------------
tab1, tab2 = st.tabs(["📟 Incidents", "📚 RAG Upload"])

# ==========================
# TAB 1: INCIDENTS
# ==========================
with tab1:
    st.markdown("<div class='main-container'>", unsafe_allow_html=True)
    st.subheader("Recent Incidents")

    events = load_events()
    if events:
        df = pd.DataFrame(events)
        st.dataframe(df, use_container_width=True, height=280)
    else:
        st.info("No incidents yet. Trigger via webhook or manual insert.")

    st.divider()

    if events:
        default_id = events[0]["id"]
        selected_id = st.selectbox("Select Event ID", [e["id"] for e in events], index=0)
        event = get_event(selected_id)
        if event:
            st.markdown(f"<h4>Event #{event['id']} – {event['summary']}</h4>", unsafe_allow_html=True)
            col1, col2 = st.columns(2)
            with col1:
                st.write("**Received At:**", event["received_at"])
                st.write("**Event Type:**", event["event_type"])
                st.write("**Service:**", event["service"])
                st.write("**Status:**", event["status"])
            with col2:
                st.write("**Details:**")
                st.code(event["details"] or "(none)")

            st.write("**AI Suggested Plan:**")
            st.code(event["ai_plan"] or "(none)")

            st.write("**Raw JSON:**")
            st.code(event["raw_json"] or "{}", language="json")

            c1, c2, c3 = st.columns(3)
            if c1.button("✅ Approve & Run Fix (mock)"):
                add_action(event["id"], "RUN_FIX_MOCK")
                update_status(event["id"], "ACTIONED")
                st.success("Mock fix executed.")
                st.experimental_rerun()
            if c2.button("🟩 Mark Resolved"):
                add_action(event["id"], "RESOLVED")
                update_status(event["id"], "RESOLVED")
                st.success("Marked as resolved.")
                st.experimental_rerun()
            if c3.button("🔁 Reopen"):
                add_action(event["id"], "REOPEN")
                update_status(event["id"], "NEW")
                st.info("Reopened.")
                st.experimental_rerun()
    st.markdown("</div>", unsafe_allow_html=True)

# ==========================
# TAB 2: RAG UPLOAD
# ==========================
with tab2:
    st.markdown("<div class='main-container'>", unsafe_allow_html=True)
    st.subheader("Upload Knowledge Docs (RAG)")

    uploaded_files = st.file_uploader("Upload files (PDF/TXT)", type=["pdf", "txt"], accept_multiple_files=True)

    if uploaded_files:
        os.makedirs(DATA_DIR, exist_ok=True)
        saved_files = []
        for f in uploaded_files:
            save_path = os.path.join(DATA_DIR, f.name)
            with open(save_path, "wb") as out:
                out.write(f.read())
            saved_files.append(save_path)
        st.success(f"✅ Uploaded: {', '.join(os.path.basename(f) for f in saved_files)}")

        if st.button("🚀 Build / Update FAISS Index"):
            if build_faiss_from_docs:
                try:
                    build_faiss_from_docs(saved_files)
                    st.success("🎯 RAG index updated successfully.")
                except Exception as e:
                    st.error(f"❌ Failed to rebuild FAISS index: {e}")
            else:
                st.warning("⚠️ RAG builder not available.")
    else:
        st.info("Upload PDFs or text SOPs to enhance AI knowledge.")
    st.markdown("</div>", unsafe_allow_html=True)
