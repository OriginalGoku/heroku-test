import logging
from slack_bolt import App
from slack_bolt.adapter.flask import SlackRequestHandler
from flask import Flask, request
from slack_sdk.web import WebClient
from dotenv import load_dotenv
import os
import ssl as ssl_lib
import certifi
from onboarding_tutorial import OnboardingTutorial
# Load environment variables
load_dotenv()

# Create a Slack Bolt app
bolt_app = App(token=os.environ.get("SLACK_BOT_TOKEN"), signing_secret=os.environ.get("SLACK_SIGNING_SECRET"))

# Flask app for serving the Bolt app
flask_app = Flask(__name__)
handler = SlackRequestHandler(bolt_app)

onboarding_tutorials_sent = {}

# ============= Reaction Added Events ============= #
# When a users adds an emoji reaction to the onboarding message,
# the type of the event will be 'reaction_added'.
# Here we'll link the update_emoji callback to the 'reaction_added' event.
@bolt_app.event("reaction_added")
def update_emoji(event, client):
    """Update the onboarding welcome message after receiving a "reaction_added"
    event from Slack. Update timestamp for welcome message as well.
    """
    # Get the ids of the Slack user and channel associated with the incoming event
    channel_id = event.get("item", {}).get("channel")
    user_id = event.get("user")

    print(f"update_emoji: {event}\n\n")
    if channel_id not in onboarding_tutorials_sent:
        return

    # Get the original tutorial sent.
    onboarding_tutorial = onboarding_tutorials_sent[channel_id][user_id]

    # Mark the reaction task as completed.
    onboarding_tutorial.reaction_task_completed = True

    # Get the new message payload
    message = onboarding_tutorial.get_message_payload()

    # Post the updated message in Slack
    updated_message = client.chat_update(**message)


# =============== Pin Added Events ================ #
# When a users pins a message the type of the event will be 'pin_added'.
# Here we'll link the update_pin callback to the 'pin_added' event.
@bolt_app.event("pin_added")
def update_pin(event, client):
    """Update the onboarding welcome message after receiving a "pin_added"
    event from Slack. Update timestamp for welcome message as well.
    """
    # Get the ids of the Slack user and channel associated with the incoming event
    channel_id = event.get("channel_id")
    user_id = event.get("user")

    # Get the original tutorial sent.
    onboarding_tutorial = onboarding_tutorials_sent[channel_id][user_id]

    # Mark the pin task as completed.
    onboarding_tutorial.pin_task_completed = True

    # Get the new message payload
    message = onboarding_tutorial.get_message_payload()

    # Post the updated message in Slack
    updated_message = client.chat_update(**message)

def start_onboarding(user_id: str, channel: str, client: WebClient):
    # Create a new onboarding tutorial.
    onboarding_tutorial = OnboardingTutorial(channel)

    # Get the onboarding message payload
    message = onboarding_tutorial.get_message_payload()

    # Post the onboarding message in Slack
    response = client.chat_postMessage(**message)

    # Capture the timestamp of the message we've just posted so
    # we can use it to update the message after a user
    # has completed an onboarding task.
    onboarding_tutorial.timestamp = response["ts"]

    # Store the message sent in onboarding_tutorials_sent
    if channel not in onboarding_tutorials_sent:
        onboarding_tutorials_sent[channel] = {}
    onboarding_tutorials_sent[channel][user_id] = onboarding_tutorial

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
    return start_onboarding(user_id, channel_id, client)
if __name__ == "__main__":
    ssl_context = ssl_lib.create_default_context(cafile=certifi.where())
    logger = logging.getLogger()
    logger.setLevel(logging.DEBUG)
    logger.addHandler(logging.StreamHandler())
    flask_app.run(port=3000)