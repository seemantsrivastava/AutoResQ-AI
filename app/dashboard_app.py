import os, sqlite3, datetime
import streamlit as st
from dotenv import load_dotenv
import pandas as pd

try:
    from app.rag_engine.embeddings_faiss import build_faiss_from_docs
except Exception:
    build_faiss_from_docs = None

load_dotenv()
DB_PATH = os.getenv("DATABASE_PATH")
DATA_DIR = os.getenv("DATA_DIR", "rag_engine/data")
st.set_page_config(page_title="AutoResQ Dashboard", layout="wide")

st.markdown("""
<style>
/* ======= APP BACKGROUND ======= */
.stApp {
    background: linear-gradient(135deg, #eef2f7 0%, #dae2ed 100%);
    color: #1b2a3d;
    font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
}

/* ======= HEADER ======= */
.main-header {
    background: linear-gradient(120deg, rgba(47,85,151,0.15), rgba(47,85,151,0.05));
    border-radius: 22px;
    padding: 32px;
    margin-top: 20px;
    text-align: center;
    box-shadow: 0 6px 24px rgba(47,85,151,0.15);
    backdrop-filter: blur(10px);
}
h1 {
    color: #2f5597;
    font-weight: 800;
    font-size: 2.8rem;
    text-shadow: 0 0 8px rgba(47,85,151,0.3);
    margin-bottom: 0.3rem;
}
h3 {
    color: #3b4b61;
    font-weight: 600;
    font-size: 1.2rem;
    margin-top: 0;
}
p {
    color: #4c5968;
    font-size: 1rem;
    margin-top: 4px;
}

/* ======= MAIN CONTAINER ======= */
.main-container {
    background: rgba(255, 255, 255, 0.65);
    border: 1px solid rgba(255, 255, 255, 0.4);
    border-radius: 22px;
    padding: 28px 32px;
    margin-top: 28px;
    box-shadow: 0 8px 32px rgba(31, 38, 135, 0.18);
    backdrop-filter: blur(14px);
    transition: transform 0.3s ease, box-shadow 0.3s ease;
}
.main-container:hover {
    transform: translateY(-2px);
    box-shadow: 0 12px 48px rgba(31, 38, 135, 0.25);
}

/* ======= SUBHEADERS ======= */
.subheader {
    color: #2f5597;
    font-weight: 700;
    font-size: 1.4rem;
    text-shadow: 0 0 8px rgba(47,85,151,0.25);
    margin-bottom: 16px;
}

/* ======= TABS ======= */
div[data-baseweb="tab-list"] {
    background: rgba(255,255,255,0.6);
    border-radius: 16px;
    box-shadow: inset 0 0 20px rgba(47,85,151,0.12);
    padding: 8px 14px;
    margin-bottom: 24px;
}
div[data-baseweb="tab"] {
    color: #214c7c !important;
    font-weight: 700;
    font-size: 1rem;
    padding: 10px 24px;
    border-radius: 10px;
    transition: all 0.25s ease;
}
div[data-baseweb="tab"]:hover {
    background: rgba(47,85,151,0.12) !important;
    transform: translateY(-1px);
}
div[data-baseweb="tab"][aria-selected="true"] {
    background: linear-gradient(120deg, #3a6dd6 0%, #2f5597 100%) !important;
    color: #ffffff !important;
    box-shadow: 0 4px 15px rgba(47,85,151,0.4);
}

/* ======= DATAFRAME ======= */
[data-testid="stDataFrame"] {
    background: rgba(255,255,255,0.8) !important;
    border-radius: 16px !important;
    box-shadow: 0 6px 26px rgba(47,85,151,0.08);
    font-weight: 500;
    font-size: 1rem !important;
}
thead tr th {
    background: rgba(47,85,151,0.15) !important;
    color: #1d3e6b !important;
    font-weight: 700 !important;
    border-bottom: 2px solid rgba(47,85,151,0.4) !important;
}
tbody tr:hover {
    background: rgba(47,85,151,0.08) !important;
    transition: all 0.3s ease-in-out;
}

/* ======= BUTTONS ======= */
.stButton>button {
    background: linear-gradient(90deg, #4a90e2, #357ABD);
    color: #fff;
    border-radius: 12px;
    padding: 10px 22px;
    font-weight: 700;
    border: none;
    box-shadow: 0 6px 18px rgba(47,85,151,0.25);
    transition: all 0.25s ease;
}
.stButton>button:hover {
    background: linear-gradient(90deg, #357ABD, #4a90e2);
    transform: translateY(-1px);
}

/* ======= SCROLLBAR ======= */
::-webkit-scrollbar {
    width: 9px;
}
::-webkit-scrollbar-thumb {
    background: rgba(47,85,151,0.25);
    border-radius: 8px;
}
</style>
""", unsafe_allow_html=True)

# ---------- Header ----------
st.markdown("""
<div class="main-header">
    <h1>🚨 AutoResQ</h1>
    <h3>The AI-Powered Incident Copilot</h3>
    <p>Smart Triage · Root Cause Insights · Automated Recovery</p>
</div>
""", unsafe_allow_html=True)

# ---------- Database Helpers ----------
@st.cache_resource
def get_conn():
    conn = sqlite3.connect(DB_PATH, check_same_thread=False)
    conn.row_factory = sqlite3.Row
    return conn

def load_events():
    conn = get_conn()
    cur = conn.execute("""
        SELECT id, incident_id, received_at, event_type, summary, service, status 
        FROM events ORDER BY id DESC
    """)
    return [dict(row) for row in cur.fetchall()]

# ---------- Tabs ----------
tab1, tab2 = st.tabs(["📟 Incidents", "📚 RAG Upload"])

# ---------- TAB 1: Incidents ----------
with tab1:
    st.markdown("<div class='main-container'>", unsafe_allow_html=True)
    st.markdown("<div class='subheader'>Recent Incidents</div>", unsafe_allow_html=True)

    events = load_events()
    if events:
        df = pd.DataFrame(events)
        st.dataframe(df, use_container_width=True, height=340)
    else:
        st.info("No incidents yet. Trigger via webhook or manual insert.")

    st.markdown("</div>", unsafe_allow_html=True)

# ---------- TAB 2: RAG Upload ----------
with tab2:
    st.markdown("<div class='main-container'>", unsafe_allow_html=True)
    st.markdown("<div class='subheader'>Upload Knowledge Docs (RAG)</div>", unsafe_allow_html=True)

    uploaded_files = st.file_uploader(
        "Choose files (PDF or TXT)",
        type=["pdf", "txt"],
        accept_multiple_files=True
    )

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
