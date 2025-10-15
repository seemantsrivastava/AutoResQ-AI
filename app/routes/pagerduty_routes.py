from flask import Blueprint, request, jsonify
from app.utils.ai_utils import get_ai_suggestion
from app.utils.slack_utils import client, SLACK_CHANNEL
from app.utils.log_utils import jdump
import logging

bp = Blueprint("pagerduty_routes", __name__)
logger = logging.getLogger("autoresq")


@bp.route("/", methods=["POST"])
def pd_webhook():
    """Receive PagerDuty webhook and forward to Slack."""
    payload = request.get_json(silent=True) or {}
    logger.info("Alert payload received")

    event_type = payload.get("event", {}).get("event_type") or payload.get("event_type", "unknown")
    incident = payload.get("event", {}).get("data") or payload.get("incident") or {}
    incident_id = incident.get("id", "N/A")
    summary = incident.get("summary") or incident.get("title") or "No summary"
    service = (incident.get("service") or {}).get("summary", "unknown")
    title = incident.get("title", "N/A")

    ai_suggestion = None
    if event_type.lower() in ["incident.triggered", "trigger"]:
        ai_suggestion = get_ai_suggestion(summary)

    blocks = [
        {
            "type": "section",
            "text": {
                "type": "mrkdwn",
                "text": (
                    f"🚨 *Incident Alert* for `{service}`\n"
                    f"*Event:* {event_type}\n"
                    f"*Title:* {title}\n"
                    f"*Summary:* {summary}\n"
                    f"*Incident ID:* `{incident_id}`"
                ),
            },
        }
    ]

    if ai_suggestion:
        clean = (
            ai_suggestion.replace("```", "")
            .replace("#", "")
            .replace("**", "*")
            .strip()
        )
        if len(clean) > 3400:
            clean = clean[:3400] + "..."
        blocks.append({"type": "section", "text": {"type": "mrkdwn", "text": f"💡 *AI Suggestion:*\n{clean}"}})

    blocks.append({
        "type": "actions",
        "block_id": incident_id,
        "elements": [
            {"type": "button", "text": {"type": "plain_text", "text": "Acknowledge"}, "value": "ack", "style": "primary"},
            {"type": "button", "text": {"type": "plain_text", "text": "Resolve"}, "value": "resolve", "style": "danger"},
        ],
    })

    try:
        resp = client.chat_postMessage(channel=SLACK_CHANNEL, text=f"🚨 Incident for `{service}`: {summary}", blocks=blocks)
        logger.info("Slack post OK | ts=%s", resp.data.get("ts"))
    except Exception as e:
        logger.exception("Slack post failed | incident=%s error=%s", incident_id, e)

    return jsonify({"status": "ok"}), 200
