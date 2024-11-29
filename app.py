import logging
from slack_bolt import App
from slack_sdk.web import WebClient
from onboarding_tutorial import OnboardingTutorial
import ssl as ssl_lib
import certifi
import os
from pprint import pprint
from dotenv import load_dotenv

load_dotenv()
app = App(token=os.environ.get("SLACK_BOT_TOKEN"), signing_secret=os.environ.get("SLACK_SIGNING_SECRET"))

onboarding_tutorials_sent = {}

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



@app.event("assistant_thread_started")
def handle_assistant_thread_started_events(body, logger):
    logger.info(body)

# ================ Team Join Event =============== #
# When the user first joins a team, the type of the event will be 'team_join'.
# Here we'll link the onboarding_message callback to the 'team_join' event.

# Note: Bolt provides a WebClient instance as an argument to the listener function
# we've defined here, which we then use to access Slack Web API methods like conversations_open.
# For more info, checkout: https://slack.dev/bolt-python/concepts#message-listening
@app.event("team_join")
def onboarding_message(event, client):
    """Create and send an onboarding welcome message to new users. Save the
    time stamp of this message so we can update this message in the future.
    """
    # Get the id of the Slack user associated with the incoming event
    user_id = event.get("user", {}).get("id")

    # Open a DM with the new user.
    response = client.conversations_open(users=user_id)
    channel = response["channel"]["id"]

    # Post the onboarding message.
    start_onboarding(user_id, channel, client)


# ============= Reaction Added Events ============= #
# When a users adds an emoji reaction to the onboarding message,
# the type of the event will be 'reaction_added'.
# Here we'll link the update_emoji callback to the 'reaction_added' event.
@app.event("reaction_added")
def update_emoji(event, client):
    """Update the onboarding welcome message after receiving a "reaction_added"
    event from Slack. Update timestamp for welcome message as well.
    """
    # Get the ids of the Slack user and channel associated with the incoming event
    channel_id = event.get("item", {}).get("channel")
    user_id = event.get("user")

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
@app.event("pin_added")
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

@app.event("pin_removed")
def handle_pin_removed_events(body, logger):
    print(f"pin_removed: {body}")
    logger.info(body)

@app.command("/echo")
def repeat_text(ack, say, command):
    # Acknowledge command request
    print(f"Command: {command}")
    ack()
    say(f"{command['text']}")

# ============== Message Events ============= #
# When a user sends a DM, the event type will be 'message'.
# Here we'll link the message callback to the 'message' event.
@app.event("message")
def message(event, client):
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
        client.chat_postMessage(channel=channel_id, text=f"Replying to {user_id} from {channel_id} with {text} and Time Stamp: {ts}")
        return start_onboarding(user_id, channel_id, client)

# @app.message("message")
# def message(message, say):
#     print(f"message: {message}\n\n")
#     pprint(f"message = {message}")
#     # say() sends a message to the channel where the event was triggered
#     say(f"Hey there <@{message['user']}>!")
    

if __name__ == "__main__":
    ssl_context = ssl_lib.create_default_context(cafile=certifi.where())
    logger = logging.getLogger()
    logger.setLevel(logging.DEBUG)
    logger.addHandler(logging.StreamHandler())
    app.start(3000)