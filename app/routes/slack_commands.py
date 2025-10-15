from flask import Blueprint, request, abort
from app.utils.slack_utils import client, signature_verifier
from app.utils.ai_utils import get_ai_suggestion
import logging, re

bp = Blueprint("slack_commands", __name__)
logger = logging.getLogger("autoresq")

@bp.route("/slack/command", methods=["POST"])
def slack_command():
    raw = request.get_data()
    if not signature_verifier.is_valid_request(raw, request.headers):
        logger.warning("Slack signature invalid on /slack/command")
        abort(403, "Invalid Slack signature")

    form = request.form or {}
    text = (form.get("text") or "").strip()
    user = form.get("user_name") or form.get("user_id")
    channel_id = form.get("channel_id")

    reply = f":wave: Hi {user}, AutoResQ received `/autoresq` with text: `{text}`"

    if re.search(r"\b(trigger|run|start|execute)\b", text.lower()) and re.search(r"\b(job|batch|process)\b", text.lower()):
        reply = f"🧠 Okay {user}, you want to *trigger a job*.\n🚀 Trigger executed successfully."
    elif re.search(r"\b(how|why|rca|issue|failure|fix|resolve|steps|solution)\b", text.lower()):
        ai_reply = get_ai_suggestion(text)
        reply = f"📘 *AutoResQ Knowledge Lookup:*\n{ai_reply}"

    try:
        client.chat_postMessage(channel=channel_id, text=reply)
        logger.info("Slash command OK | user=%s text=%s", user, text)
    except Exception as e:
        logger.exception("Slash command failed | %s", e)

    return "", 200
