"""
AutoResQ - rag_ai_engine.py (OpenAI Version)
----------------------------------------
RAG + LLM hybrid:
- If FAISS match score is strong → return SOP snippet (no hallucination)
- Else → call LLM for reasoning-based suggestion
"""

import os, logging
from dotenv import load_dotenv
from typing import List, Tuple
from langchain_openai import ChatOpenAI, OpenAIEmbeddings  # ✅ OpenAI imports
from langchain_community.vectorstores import FAISS
from langchain.schema import Document

# -------------------------------------------------------------------
# Setup
# -------------------------------------------------------------------
load_dotenv()
logging.basicConfig(level=logging.INFO, format="[%(levelname)s] %(message)s")
log = logging.getLogger("AutoResQ-AI")

# New: use similarity logic for OpenAI
SCORE_KIND = os.getenv("RAG_SCORE_KIND").lower()
SIM_THR = float(os.getenv("RAG_SIMILARITY_THRESHOLD"))  # ✅ higher=better
DIST_THR = float(os.getenv("RAG_DISTANCE_THRESHOLD"))

# ✅ Updated for OpenAI
INDEX_PATH = os.getenv("INDEX_PATH")
EMBED_MODEL = os.getenv("EMBED_MODEL")
LLM_MODEL = os.getenv("LLM_MODEL")

log.info(f"INDEX_PATH {INDEX_PATH}")
log.info(f"EMBED_MODEL {EMBED_MODEL}")
log.info(f"LLM_MODEL {LLM_MODEL}")

# ------------------------------
def is_high_confidence(score: float) -> bool:
    if SCORE_KIND == "similarity":
        return score >= SIM_THR  # ✅ higher is better
    else:
        return score <= DIST_THR

# -------------------------------------------------------------------
# Load FAISS index
# -------------------------------------------------------------------
def load_index():
    if not FAISS:
        log.warning("⚠️ FAISS not available.")
        return None, None
    if not os.path.exists(INDEX_PATH):
        log.warning(f"⚠️ FAISS index not found at {INDEX_PATH}")
        return None, None
    try:
        embeddings = OpenAIEmbeddings(model=EMBED_MODEL)  # ✅ replaced BedrockEmbeddings
        db = FAISS.load_local(INDEX_PATH, embeddings, allow_dangerous_deserialization=True)
        log.info(f"✅ Loaded FAISS index ({len(db.index_to_docstore_id)} docs)")
        return db, embeddings
    except Exception as e:
        log.error(f"❌ Failed to load FAISS index: {e}")
        return None, None

# -------------------------------------------------------------------
# Search FAISS index and return results
# -------------------------------------------------------------------
def search_faiss_with_score(query: str, top_k: int = 5) -> List[Tuple[Document, float]]:
    db, _ = load_index()
    if not db:
        return []
    try:
        results = db.similarity_search_with_score(query, k=top_k)
        for i, (doc, score) in enumerate(results, start=1):
            src = doc.metadata.get("source", "unknown")
            snippet = doc.page_content[:200].replace("\n", " ")
            log.debug(f"   ↳ [{i}] {src} | Score={score:.3f} | {snippet}...")
        return results
    except Exception as e:
        log.error(f"❌ FAISS search failed: {e}")
        return []

# -------------------------------------------------------------------
# Hybrid AI suggestion
# -------------------------------------------------------------------
def generate_solution(query: str):
    try:
        results = search_faiss_with_score(query)
        if not results:
            log.warning("⚠️ No FAISS results. Falling back to LLM.")
            return llm_generate(query, context=None)

        top_doc, top_score = results[0]
        sop_text = top_doc.page_content.strip()
        source = top_doc.metadata.get("source", "N/A")

        if SCORE_KIND == "similarity":
            is_relevant = top_score >= SIM_THR
        else:
            is_relevant = top_score <= DIST_THR

        log.info(f"🎯 Top FAISS match score={top_score:.3f} | Relevant={is_relevant}")

        if is_high_confidence(top_score):
            log.info("✅ High-confidence match. Returning formatted SOP (no reasoning).")
            reformat_prompt = f"""
You are AutoResQ, an AI-powered incident responder.

The alert says: "{query}"

Below is an extracted SOP text which may cover multiple scenarios.
Only extract and summarize steps that are directly relevant to the alert topic.
Ignore unrelated sections.

SOP/RCA Text:
{sop_text}
"""
            formatted = llm_generate(reformat_prompt, context=None)
            return (
                f":blue_book: *Source:* `{source}`\n"
                f"{formatted}"
            )

        if not is_relevant:
            log.warning(f"❌ Low relevance (score={top_score:.2f}). Skipping context-based reasoning.")
            context = None
        else:
            context = "\n\n".join([doc.page_content for doc, _ in results])

        return llm_generate(query, context)

    except Exception as e:
        log.error(f"❌ generate_solution failed: {e}")
        return "AI suggestion unavailable."

# -------------------------------------------------------------------
# LLM reasoning helper
# -------------------------------------------------------------------
def llm_generate(query: str, context: str):
    try:
        # ✅ OpenAI version
        llm = ChatOpenAI(model_name=LLM_MODEL, temperature=0.2)

        if not context or len(context.strip()) < 100:
            prompt = f"""
You are AutoResQ — an AI-powered incident responder.

An alert was received:
"{query}"

No relevant SOP context was found in the knowledge base.
Provide a concise, generic set of actionable steps to resolve the issue,
based only on the alert description.
Avoid inventing or assuming internal system names.
Respond in plain text or numbered list — do not include code blocks, functions, or markdown fencing.
"""
        else:
            prompt = f"""
You are AutoResQ — an AI-powered incident responder.

Alert Message:
{query}

Relevant Context:
{context}

Use the SOP context above only if it is directly relevant.
If not, provide a general resolution guide instead.
Respond in plain text or numbered list — do not include code blocks, functions, or markdown fencing.
"""

        log.debug("🧠 LLM Prompt:\n%s", prompt[:800])
        log.info("🧠 LLM Prompt Sent")
        response = llm.invoke(prompt)
        suggestion = response.content.strip() if hasattr(response, "content") else str(response).strip()

        # --- Cleanup ---
        suggestion = suggestion.strip('`').replace('```python', '').replace('```', '')
        suggestion = suggestion.replace('"""', '').replace("'''", '').strip()
        suggestion = "\n".join([line.strip() for line in suggestion.splitlines() if line.strip()])

        log.debug("🤖 LLM Response (trimmed):\n%s", suggestion[:800])
        log.info("🤖 LLM Response Received")
        return suggestion or "AI model returned no suggestion."

    except Exception as e:
        log.error(f"❌ LLM reasoning failed: {e}")
        return "AI suggestion unavailable."
