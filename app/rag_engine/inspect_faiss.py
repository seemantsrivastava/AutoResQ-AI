"""
AutoResQ RAG - inspect_faiss.py
-------------------------------
Validates and previews FAISS index contents.
"""

import os, logging
from dotenv import load_dotenv
from langchain_community.vectorstores import FAISS
from langchain_openai import OpenAIEmbeddings  # ✅ Use OpenAI instead of Bedrock

# -------------------------------------------------------------------
# Setup
# -------------------------------------------------------------------
load_dotenv()
logging.basicConfig(level=logging.INFO, format="[%(levelname)s] %(message)s")
log = logging.getLogger("AutoResQ-Inspect")

INDEX_PATH = os.getenv("INDEX_PATH")
EMBED_MODEL = os.getenv("EMBED_MODEL")

# -------------------------------------------------------------------
def inspect_faiss(limit=10):
    if not os.path.exists(INDEX_PATH):
        log.error(f"❌ Index path not found: {INDEX_PATH}")
        return

    index_file = os.path.join(INDEX_PATH, "index.faiss")
    if not os.path.exists(index_file):
        log.error(f"❌ No FAISS index file found at {index_file}")
        return

    embeddings = OpenAIEmbeddings(model=EMBED_MODEL)
    db = FAISS.load_local(INDEX_PATH, embeddings, allow_dangerous_deserialization=True)

    total = len(db.index_to_docstore_id)
    log.info(f"✅ Loaded FAISS index from {INDEX_PATH}")
    log.info(f"📦 Total documents: {total}\n")

    for i, (doc_id, doc) in enumerate(db.docstore._dict.items()):
        log.info(f"[{i+1}] ID={doc_id}")
        log.info(f"Metadata: {doc.metadata}")
        log.info(f"Snippet: {doc.page_content[:900].replace(chr(10), ' ')} ...\n")
        if i + 1 >= limit:
            break

# -------------------------------------------------------------------
if __name__ == "__main__":
    inspect_faiss(limit=20)
