import asyncio
import logging
import time
from slack_bolt.adapter.socket_mode.async_handler import AsyncSocketModeHandler

from config import settings
from message_converter import (
    convert_slack_messages_to_model_messages,
    get_message_with_role,
    get_new_thread_messages,
)
from slack_bot import app, get_session, get_response

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


@app.event("app_mention")
async def mention_handler(body, say, client, logger):
    """Handle app mentions in Slack."""
    event = body.get("event", {})
    is_first_message = "thread_ts" not in event

    if is_first_message:
        thread_ts = event.get("ts")
        session = get_session(thread_ts)
    else:
        thread_ts = event.get("thread_ts")
        session = get_session(thread_ts)
        # print("Latest message timestamp 1:", session.latest_message_ts)
        thread_messages = await get_new_thread_messages(
            client, event["channel"], thread_ts, session.latest_message_ts
        )
        # logger.info()
        logger.debug(
            f"thread messages: {thread_messages}",
        )
        messages_to_add = thread_messages[
            1:-1
        ]  # Exclude the first (previous bot reply) and last messages (current user mention)
        if messages_to_add:
            model_messages_to_add = convert_slack_messages_to_model_messages(
                messages_to_add
            )
            # print("old message", model_messages_to_add)
            session.append_message(model_messages_to_add)

    # Get response using the full thread context
    input_text = get_message_with_role(event)
    output = await get_response(
        input_text=input_text,
        session=session,
    )
    session_messages = session.get_messages()
    logger.debug(f"session messages: {session_messages}")
    await say(text=output, thread_ts=thread_ts)

    # Update the latest message timestamp
    session.set_latest_message_ts(timestamp=str(time.time()))


async def main():
    """Start the Slack bot."""
    await AsyncSocketModeHandler(app, settings.slack_app_token).start_async()


if __name__ == "__main__":
    asyncio.run(main())
