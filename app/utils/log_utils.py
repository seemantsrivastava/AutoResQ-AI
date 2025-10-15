import json

def jdump(obj) -> str:
    """Pretty JSON string for DEBUG logging (safe fallback)."""
    try:
        return json.dumps(obj, indent=2, ensure_ascii=False)
    except Exception:
        return str(obj)
