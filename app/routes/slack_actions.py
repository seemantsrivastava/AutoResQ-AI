from flask import Blueprint, request, abort
from app.utils.slack_utils import client, signature_verifier
from app.utils.log_utils import jdump
import json, logging

bp = Blueprint("slack_actions", __name__)
logger = logging.getLogger("autoresq")


# ----------------------------------------
# 🔁 Slack Feedback Feature
# ----------------------------------------
def attach_feedback_buttons(client, channel, ts, incident, ai_suggestion):
    """
    Adds interactive feedback (👍 or 💬) below AI suggestion message.
    """
    client.chat_postMessage(
        channel=channel,
        thread_ts=ts,
        text="Was this AI suggestion helpful?",
        blocks=[
            {
                "type": "section",
                "text": {"type": "mrkdwn", "text": "🤖 *Was this AI suggestion correct?*"}
            },
            {
                "type": "actions",
                "elements": [
                    {
                        "type": "button",
                        "text": {"type": "plain_text", "text": "👍 Correct Suggestion"},
                        "style": "primary",
                        "value": json.dumps({"incident": incident, "ai_suggestion": ai_suggestion}),
                        "action_id": "ai_feedback_positive"
                    },
                    {
                        "type": "button",
                        "text": {"type": "plain_text", "text": "💬 Add More Details"},
                        "value": json.dumps({"incident": incident, "ai_suggestion": ai_suggestion}),
                        "action_id": "ai_feedback_negative"
                    }
                ]
            }
        ]
    )

# ----------------------------------------
# 🧩 Unified Slack Actions Endpoint
# ----------------------------------------
@bp.route("/slack/actions", methods=["POST"])
def slack_actions():
    """Handles all Slack button interactions (acknowledge, resolve, feedback)."""
    raw = request.get_data()
    if not signature_verifier.is_valid_request(raw, request.headers):
        logger.warning("Slack signature invalid on /slack/actions")
        abort(403, "Invalid Slack signature")

    payload = json.loads(request.form.get("payload", "{}"))
    # 🔍 Log only summary in INFO, full payload in DEBUG
    if logger.isEnabledFor(logging.DEBUG):
        logger.debug("Slack action received full payload:\n%s", jdump(payload))
    else:
        user_disp = payload.get("user", {}).get("username") or payload.get("user", {}).get("name", "unknown")
        action_obj = (payload.get("actions") or [{}])[0]
        logger.info("Slack action: user=%s action_id=%s value=%s",
                    user_disp, action_obj.get("action_id"), action_obj.get("value"))

    user = payload.get("user", {}).get("username") or payload.get("user", {}).get("name", "unknown")
    action_obj = (payload.get("actions") or [{}])[0]
    action_id = action_obj.get("action_id", "")
    action_value = action_obj.get("value", "")  # ✅ actual button action name (ack/resolve)
    channel_id = payload.get("channel", {}).get("id")
    ts = payload.get("message", {}).get("ts")

    # ✅ Identify incident ID from block_id
    incident_id = action_obj.get("block_id", "N/A")

    # ----------------------------------------
    # 🟩 Handle Acknowledge / Resolve Buttons
    # ----------------------------------------
    if action_value in ["ack", "resolve"]:  # ✅ FIXED: use value, not action_id
        if action_value == "ack":
            msg = f"✅ {user} acknowledged incident `{incident_id}`"
        else:
            msg = f"🎉 {user} resolved incident `{incident_id}`"

        try:
            client.chat_postMessage(channel=channel_id, text=msg)
            logger.info("Slack confirmation OK | incident=%s action=%s", incident_id, action_value)
        except Exception as e:
            logger.exception("Slack confirmation failed | incident=%s error=%s", incident_id, e)
        return "", 200

    # ----------------------------------------
    # 💬 Handle AI Feedback Buttons
    # ----------------------------------------
    elif action_id in ["ai_feedback_positive", "ai_feedback_negative"]:
        try:
            data = json.loads(action_obj.get("value", "{}"))
        except Exception:
            data = {}
        incident = data.get("incident")
        ai_suggestion = data.get("ai_suggestion")

        if action_id == "ai_feedback_positive":
            client.chat_postMessage(
                channel=channel_id,
                thread_ts=ts,
                text=f"✅ Thanks <@{user}>! Marked this AI suggestion as *correct* for incident `{incident}`."
            )
        else:
            client.chat_postMessage(
                channel=channel_id,
                thread_ts=ts,
                text="📝 Please reply in this thread with the correct resolution or extra notes. I’ll index it."
            )
        return "", 200

    else:
        logger.warning("Unhandled Slack action | action_id=%s | value=%s", action_id, action_value)
        return "", 200
