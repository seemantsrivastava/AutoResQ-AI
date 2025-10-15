from flask import Blueprint, request, jsonify

from app.routes.slack_actions import attach_feedback_buttons
from app.utils.ai_utils import get_ai_suggestion
from app.utils.slack_utils import client, SLACK_CHANNEL
from app.utils.log_utils import jdump
import logging

bp = Blueprint("pagerduty_routes", __name__)
logger = logging.getLogger("autoresq")

import sqlite3, datetime, json, os
from dotenv import load_dotenv
load_dotenv()

DB_PATH = os.getenv("DATABASE_PATH")

def insert_event(payload):
    """Insert a new PagerDuty alert into the events table."""
    try:
        conn = sqlite3.connect(DB_PATH, check_same_thread=False)

        # ✅ Extract data from both possible payload shapes
        event_type = payload.get("event", {}).get("event_type") or payload.get("event_type", "unknown")
        incident = payload.get("event", {}).get("data") or payload.get("incident") or {}

        incident_id = incident.get("id", "N/A")
        title = incident.get("title") or incident.get("summary") or "PagerDuty Incident"
        summary = incident.get("summary") or title
        status = incident.get("status", "triggered").upper()
        service = (incident.get("service") or {}).get("summary", "PagerDuty")

        details = json.dumps(incident, indent=2)
        ai_plan = "AI plan pending"

        with conn:
            conn.execute("""
                INSERT INTO events (
                    incident_id,
                    received_at,
                    event_type,
                    summary,
                    service,
                    details,
                    raw_json,
                    ai_plan,
                    status
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                incident_id,  # e.g. "Q1X7SI90B4Z1E6"
                datetime.datetime.utcnow().isoformat(),
                status,  # event_type = current incident status
                f"{title}",  # summary = title + ID
                service,  # service name
                details,  # full incident object or description
                json.dumps(payload, indent=2),  # raw payload
                ai_plan,
                "NEW"
            ))

        print(f"✅ Stored PagerDuty incident {incident_id}: {title} [{status}]")

    except Exception as e:
        print(f"❌ DB insert failed: {e}")

@bp.route("/", methods=["POST"])
def pd_webhook():
    """Receive PagerDuty webhook and forward to Slack."""
    payload = request.get_json(silent=True) or {}
    logger.info("Alert payload received")
    logger.debug("Alert payload received:\n%s", jdump(payload))
    insert_event(payload)
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
        attach_feedback_buttons(client, SLACK_CHANNEL, resp["ts"], incident_id, ai_suggestion)
        logger.info("Slack post OK | ts=%s", resp.data.get("ts"))
    except Exception as e:
        logger.exception("Slack post failed | incident=%s error=%s", incident_id, e)

    return jsonify({"status": "ok"}), 200
