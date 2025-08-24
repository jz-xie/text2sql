from slack_bolt.async_app import AsyncApp
from slack_sdk.errors import SlackApiError
from config import settings
from slack_bolt.adapter.socket_mode.async_handler import AsyncSocketModeHandler
import logging
import asyncio

logging.basicConfig(level=logging.INFO)

logger = logging.getLogger(__name__)

app = AsyncApp(token=settings.slack_bot_token)


class SlackBot:
    def __init__(self, bot_user_id: str):
        self.bot_user_id = bot_user_id
        self.system_prompt = f"""You are a helpful Slack bot with ID {self.bot_user_id}.

When you refer someone, mention them with '<@USER_ID>'.

User input will be with the following format:
User: <@USER_ID>
Message: <MESSAGE_CONTENT>

Your role is to assist users with their queries and provide accurate, helpful responses.
When users mention you in a thread, you have access to the full conversation history of that thread.
Please be professional, concise, and clear in your responses.

"""


async def get_bot_user_id() -> str:
    try:
        # Run auth test to verify credentials
        auth_response = await app.client.auth_test()

        logger.info(
            f"Slack Connection Established. Bot User ID: {auth_response['user_id']}"
        )
        return auth_response["user_id"]

    except SlackApiError as e:
        logger.error(f"Error creating Slack app: {e}")
        raise Exception(e)


slack_bot = SlackBot(bot_user_id=asyncio.run(get_bot_user_id()))
