import os
from slack_sdk import WebClient
from slack_sdk.signature import SignatureVerifier

client = WebClient(token=os.getenv("SLACK_BOT_TOKEN"))
signature_verifier = SignatureVerifier(os.getenv("SLACK_SIGNING_SECRET"))
SLACK_CHANNEL = os.getenv("SLACK_CHANNEL", "#autoresq-demo")
