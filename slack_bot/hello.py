from slack_bolt.async_app import AsyncApp
from slack_sdk.errors import SlackApiError
from config import settings
from slack_bolt.adapter.socket_mode.async_handler import AsyncSocketModeHandler
import logging
from bot import get_response
from message_converter import (
    convert_slack_messages_to_model_messages,
    get_thread_messages,
    get_message_with_role,
    remove_user_bot_id,
)

from bot import get_session
import asyncio
from slack_setup import app, slack_bot

logging.basicConfig(level=logging.INFO)

logger = logging.getLogger(__name__)

# app = AsyncApp(token=settings.slack_bot_token)

# auth_response = await app.client.auth_test()

# bot = SlackBot(bot_user_id=await get_bot_user_id(app))
# @app.message("hello")
# def message_goodbye(message, say):
#     responses = ["Adios", "Au revoir", "Farewell"]
#     parting = random.choice(responses)
#     say(f"{parting} {message['user']}!")


# @app.event("message")
# def handle_message_events(body, logger):
#     # Do nothing or log, but don't reply
#     pass


@app.event("app_mention")
# @app.event("message")
async def mention_handler(body, say, client, logger):
    # responses = ["Adios", "Au revoir", "Farewell"]
    event = body.get("event", {})
    is_first_message = "thread_ts" not in event

    if is_first_message:
        thread_ts = event.get("ts")
        session = get_session(thread_ts)
        pass
    else:
        thread_ts = event.get("thread_ts")
        session = get_session(thread_ts)
        thread_messages = await get_thread_messages(client, event["channel"], thread_ts)
        logger.info("thread messages")
        logger.info(thread_messages)

        if session.is_new():
            logger.info(f"Thread messages: {thread_messages}")
            message_history = convert_slack_messages_to_model_messages(thread_messages)
            session.append_message(message_history)
        else:
            session_messages = session.get_messages()
            logger.info("session messages")
            logger.info(session_messages)

        # thread_ts = ''
        # thread_ts = event.get("thread_ts") or event.get("ts")

    # logger.info(f"Thread messages: {event}")

    # Get all messages in the thread
    # thread_messages = get_thread_replies(client, event["channel"], thread_ts)
    # logger.info(f"Thread messages: {thread_messages}")

    # Get response using the full thread context

    input_text = get_message_with_role(event)
    final_input = remove_user_bot_id(input_text, slack_bot.bot_user_id)
    output = await get_response(
        input=final_input,
        session=session,
    )

    await say(text=f"<@{event['user']}>\n{output}", thread_ts=thread_ts)


# def main():
#     print("Hello from slack-bot!")


async def main():
    # Create the Slack app and get the bot user ID
    # await run_slack_app()
    # await app.client.auth_test()
    await AsyncSocketModeHandler(app, settings.slack_app_token).start_async()


if __name__ == "__main__":
    asyncio.run(main())
    # x = asyncio.run(get_thread_replies(app.client, "C09AP8DLV6Z", "1756019160.212569"))
    # print(x)
    # AsyncSocketModeHandler(
    #     app,
    # ).start_async()
    # AsyncSlackRequestHandler(app, settings.slack_app_token).start()
    # app.start()
