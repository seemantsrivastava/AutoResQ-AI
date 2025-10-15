from flask import Blueprint, request, abort
from app.utils.slack_utils import client, signature_verifier
from app.utils.log_utils import jdump
import json, logging

bp = Blueprint("slack_actions", __name__)
logger = logging.getLogger("autoresq")

@bp.route("/slack/actions", methods=["POST"])
def slack_actions():
    raw = request.get_data()
    if not signature_verifier.is_valid_request(raw, request.headers):
        logger.warning("Slack signature invalid on /slack/actions")
        abort(403, "Invalid Slack signature")

    payload = json.loads(request.form.get("payload", "{}"))
    logger.info("Slack action received:\n%s", jdump(payload))

    user = payload.get("user", {}).get("username") or payload.get("user", {}).get("name", "unknown")
    action = (payload.get("actions") or [{}])[0].get("value", "unknown")
    incident_id = (payload.get("actions") or [{}])[0].get("block_id", "N/A")
    channel_id = payload.get("channel", {}).get("id")

    if action == "ack":
        msg = f"✅ {user} acknowledged incident `{incident_id}`"
    elif action == "resolve":
        msg = f"🎉 {user} resolved incident `{incident_id}`"
    else:
        msg = f"ℹ️ {user} performed `{action}` on `{incident_id}`"

    try:
        client.chat_postMessage(channel=channel_id, text=msg)
        logger.info("Slack confirmation OK | incident=%s action=%s", incident_id, action)
    except Exception as e:
        logger.exception("Slack confirmation failed | incident=%s error=%s", incident_id, e)

    return "", 200
