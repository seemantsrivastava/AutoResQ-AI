"""
AutoResQ Main Entrypoint
------------------------
Run using: python app/main.py
"""

from flask import Flask
import logging
from app.routes.pagerduty_routes import bp as pagerduty_bp
from app.routes.slack_actions import bp as actions_bp
from app.routes.slack_commands import bp as commands_bp
import os


def create_app():
    """Factory to create and configure the Flask app."""
    flask_app = Flask(__name__)

    flask_app.register_blueprint(pagerduty_bp)
    flask_app.register_blueprint(actions_bp)
    flask_app.register_blueprint(commands_bp)

    return flask_app


if __name__ == "__main__":
    app_instance = create_app()
    logger = logging.getLogger("autoresq")

    log_level = os.getenv("LOG_LEVEL", "INFO")
    slack_channel = os.getenv("SLACK_CHANNEL", "#autoresq-demo")

    logger.info(
        "🚀 Starting AutoResQ Flask App | LOG_LEVEL=%s | SLACK_CHANNEL=%s",
        log_level,
        slack_channel,
    )

    app_instance.run(
        host="0.0.0.0",
        port=int(os.getenv("PORT", "5004")),
        debug=(log_level == "INFO"),
    )
