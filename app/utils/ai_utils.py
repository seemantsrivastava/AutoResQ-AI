from app.rag_ai_engine import generate_solution
import logging

logger = logging.getLogger("autoresq")

def get_ai_suggestion(summary: str):
    """Wrapper to safely call AI engine."""
    try:
        suggestion = generate_solution(summary)
        if not suggestion or "unavailable" in suggestion.lower():
            logger.warning("AI suggestion unavailable.")
            return "AI suggestion unavailable."
        return suggestion
    except Exception as e:
        logger.exception("AI generation failed: %s", e)
        return "AI suggestion unavailable (error)."
