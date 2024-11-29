import logging
from slack_bolt import App
from slack_bolt.adapter.flask import SlackRequestHandler
from flask import Flask, request
from dotenv import load_dotenv
import os
import ssl as ssl_lib
import certifi

# Load environment variables
load_dotenv()

# Create a Slack Bolt app
bolt_app = App(token=os.environ.get("SLACK_BOT_TOKEN"), signing_secret=os.environ.get("SLACK_SIGNING_SECRET"))

# Flask app for serving the Bolt app
flask_app = Flask(__name__)
handler = SlackRequestHandler(bolt_app)

# Define a Flask route to handle Slack events
@flask_app.route("/slack/events", methods=["POST"])
def slack_events():
    return handler.handle(request)

# Define other Bolt app event handlers
@bolt_app.event("team_join")
def onboarding_message(event, client):
    user_id = event.get("user", {}).get("id")
    response = client.conversations_open(users=user_id)
    channel = response["channel"]["id"]
    client.chat_postMessage(channel=channel, text="Welcome to the team!")

@bolt_app.command("/echo")
def repeat_text(ack, say, command):
    ack()
    say(f"{command['text']}")


# Register the `message` event listener
@bolt_app.event("message")
def message_handler(event, client):
    """Display the onboarding welcome message after receiving a message
    that contains "start".
    """
    channel_id = event.get("channel")
    user_id = event.get("user")
    text = event.get("text")
    ts = event.get("ts")

    print(f"user_id: {user_id}")
    print(f"channel_id: {channel_id}")
    print(f"Message: {text}")
    print(f"ts: {ts}")

    if text and "*start simulation*" in text.lower():
        client.chat_postMessage(
            channel=channel_id,
            text=f"Replying to {user_id} from {channel_id} with {text} and Time Stamp: {ts}",
        )
if __name__ == "__main__":
    ssl_context = ssl_lib.create_default_context(cafile=certifi.where())
    logger = logging.getLogger()
    logger.setLevel(logging.DEBUG)
    logger.addHandler(logging.StreamHandler())
    flask_app.run(port=3000)