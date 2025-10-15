"""
===============================================================================
AutoResQ - embeddings_faiss.py
===============================================================================
Description:
------------
This script builds and updates the FAISS index for AutoResQ RAG engine.

It performs the following steps:
1. Loads documents from the data directory (supports txt, pdf, csv, xlsx, zip).
2. Splits documents into chunks.
3. Creates embeddings using OpenAI's embedding model.
4. Builds or appends to a FAISS index and saves it locally.

Logging Levels:
---------------
- INFO  → Flow tracking and summary-level events.
- DEBUG → Detailed diagnostic trace (counts, filenames, intermediate states).

Note:
-----
No logic, structure, or variable naming has been modified — only descriptive
comments and loggers are added for clarity and traceability.
===============================================================================
"""

# -------------------------------------------------------------------
# Imports
# -------------------------------------------------------------------
import os, logging, tempfile, zipfile, pandas as pd
from dotenv import load_dotenv
from langchain_community.vectorstores import FAISS
from langchain_openai import OpenAIEmbeddings
from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain.schema import Document
from langchain_community.document_loaders import (
    TextLoader, CSVLoader, PyPDFLoader, UnstructuredExcelLoader
)

# -------------------------------------------------------------------
# Setup logging and environment
# -------------------------------------------------------------------
load_dotenv()
logging.basicConfig(
    level=logging.INFO,
    format="[%(levelname)s] [embeddings_faiss.py] %(message)s"
)
log = logging.getLogger("AutoResQ-RAG")

# -------------------------------------------------------------------
# Environment & Configuration
# -------------------------------------------------------------------
INDEX_PATH = "faiss_index_openai"
RAG_DATA_DIR = os.getenv("RAG_DATA_DIR1", os.path.join(os.path.dirname(__file__), "data"))
EMBED_MODEL = os.getenv("EMBED_MODEL")
CHUNK_SIZE = int(os.getenv("RAG_CHUNK_SIZE", 2000))
CHUNK_OVERLAP = int(os.getenv("RAG_CHUNK_OVERLAP", 80))
SUPPORTED_TEXT = tuple(
    os.getenv("RAG_SUPPORTED_TEXT", ".txt,.md,.xml,.yaml,.yml,.json,.properties,.java").split(",")
)

log.info(f"📝 EMBED_MODEL {EMBED_MODEL}")
log.debug(f"Config: INDEX_PATH={INDEX_PATH}, DATA_DIR={RAG_DATA_DIR}, "
          f"CHUNK_SIZE={CHUNK_SIZE}, CHUNK_OVERLAP={CHUNK_OVERLAP}, "
          f"SUPPORTED_TEXT={SUPPORTED_TEXT}")

# -------------------------------------------------------------------
# Initialize OpenAI Embeddings
# -------------------------------------------------------------------
embeddings = OpenAIEmbeddings(model=EMBED_MODEL)
splitter = RecursiveCharacterTextSplitter(chunk_size=CHUNK_SIZE, chunk_overlap=CHUNK_OVERLAP)

# -------------------------------------------------------------------
# Core functions
# -------------------------------------------------------------------
def dataframe_to_docs(df: pd.DataFrame, source_path: str):
    """Convert a DataFrame (e.g. Sumo CSV) into LangChain Documents."""
    docs = []
    for i, row in df.iterrows():
        content = " | ".join(f"{k}={v}" for k, v in row.items() if pd.notna(v) and str(v).strip())
        docs.append(Document(page_content=content, metadata={"source": source_path, "row": i}))
    log.info(f"📝 Converted {len(docs)} DataFrame rows into Documents")
    log.debug(f"DataFrame {source_path} → {len(docs)} docs")
    return docs


def load_from_path(path):
    """Load supported file types as LangChain Documents."""
    try:
        if path.endswith(SUPPORTED_TEXT):
            loaded = TextLoader(path).load()
        elif path.endswith(".csv"):
            loaded = CSVLoader(path).load()
        elif path.endswith(".pdf"):
            loaded = PyPDFLoader(path).load()
        elif path.endswith(".xlsx"):
            loaded = UnstructuredExcelLoader(path, mode="elements").load()
        else:
            return []
        log.info(f"📄 Loaded {len(loaded)} docs from {os.path.basename(path)}")
        log.debug(f"File loaded successfully: {path}")
        return loaded
    except Exception as e:
        log.warning(f"⚠️ Skipped {path} due to error: {e}")
        return []


def load_docs_from_dir(data_dir):
    """Scan directory (and ZIPs) and return chunked documents."""
    docs = []
    log.info(f"📂 Scanning directory: {data_dir}")
    for root, _, files in os.walk(data_dir):
        for fname in files:
            fpath = os.path.join(root, fname)
            if fname.endswith(".zip"):
                log.info(f"📦 Extracting ZIP: {fname}")
                try:
                    with zipfile.ZipFile(fpath, "r") as zf:
                        extract_dir = tempfile.mkdtemp()
                        zf.extractall(extract_dir)
                        for subroot, _, subfiles in os.walk(extract_dir):
                            for subfile in subfiles:
                                subpath = os.path.join(subroot, subfile)
                                docs.extend(load_from_path(subpath))
                        log.debug(f"Extracted and loaded contents from ZIP: {fname}")
                except Exception as e:
                    log.warning(f"⚠️ Failed to extract ZIP {fname}: {e}")
            else:
                docs.extend(load_from_path(fpath))

    if docs:
        chunks = splitter.split_documents(docs)
        log.info(f"✂️ Split {len(docs)} raw docs into {len(chunks)} chunks")
        log.debug(f"Chunk details: chunk_size={CHUNK_SIZE}, overlap={CHUNK_OVERLAP}")
        return chunks
    else:
        log.warning("⚠️ No documents found in directory")
        return []


def build_faiss_from_docs(docs):
    """Create or append to FAISS index from docs."""
    if not docs:
        log.warning("⚠️ No documents to index.")
        return None

    log.info("📦 Building FAISS index...")
    seen, unique_docs = set(), []
    for d in docs:
        text = d.page_content.strip()
        if text and text not in seen:
            seen.add(text)
            unique_docs.append(d)
    log.debug(f"Unique documents count: {len(unique_docs)}")

    try:
        if os.path.exists(INDEX_PATH):
            log.info("📦 Appending to existing FAISS index...")
            db = FAISS.load_local(INDEX_PATH, embeddings, allow_dangerous_deserialization=True)
            before = len(db.index_to_docstore_id)
            db.add_documents(unique_docs)
            after = len(db.index_to_docstore_id)
            log.info(f"➕ Added {after - before} docs (total={after})")
            log.debug(f"Before={before}, After={after}")
        else:
            log.info(f"📦 Creating new FAISS index at {INDEX_PATH}...")
            db = FAISS.from_documents(unique_docs, embeddings)
            log.info(f"✅ New FAISS index created with {len(unique_docs)} docs")

        db.save_local(INDEX_PATH)
        log.info(f"💾 FAISS index saved to {INDEX_PATH}")
        return db

    except Exception as e:
        log.error(f"❌ Error building FAISS index: {e}")
        return None


# -------------------------------------------------------------------
# Script Entry Point
# -------------------------------------------------------------------
if __name__ == "__main__":
    log.info("🚀 Starting FAISS index build for AutoResQ...")
    docs = load_docs_from_dir(RAG_DATA_DIR)
    build_faiss_from_docs(docs)
    log.info("✅ FAISS index build complete.")
