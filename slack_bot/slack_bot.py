import asyncio
import logging
import redis
from functools import lru_cache
from typing import Optional

from pydantic_ai.messages import ModelMessage, ModelMessagesTypeAdapter
from pydantic_core import to_jsonable_python
from slack_bolt.async_app import AsyncApp
from slack_sdk.errors import SlackApiError

from config import settings

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = AsyncApp(token=settings.slack_bot_token)


class Session:
    """Session manager for storing conversation history in Redis."""

    # Class-level Redis client shared by all instances
    _redis_client: Optional[redis.Redis] = None

    @classmethod
    def _get_redis_client(cls) -> redis.Redis:
        """Get or create Redis client."""
        if cls._redis_client is None:
            cls._redis_client = redis.Redis(
                host="localhost", port=6379, decode_responses=True
            )
            try:
                cls._redis_client.ping()
                logger.info("Connected to Redis")
            except redis.ConnectionError:
                raise Exception("Redis connection error")
        return cls._redis_client

    def __init__(self, session_id: str):
        self.session_id = session_id
        self.redis_client = self._get_redis_client()
        self.latest_message_ts: Optional[str] = None

    def get_messages(self) -> list[ModelMessage]:
        """Get messages from Redis for this session."""
        messages_json = self.redis_client.json().get(self.session_id)
        if not messages_json:
            return []
        else:
            return ModelMessagesTypeAdapter.validate_python(messages_json)

    def append_message(self, messages: list[ModelMessage]) -> None:
        """Append messages to the session in Redis."""
        messages_json = to_jsonable_python(messages)

        if self.is_new():
            # Initialize with the messages at root level to avoid extra nesting
            self.redis_client.json().set(self.session_id, ".", messages_json)
            logger.debug("Session initialized in Redis")
        else:
            self.redis_client.json().arrappend(self.session_id, ".", *messages_json)
            logger.debug(f"Appended values in Redis: {messages_json}")

    def is_new(self) -> bool:
        """Check if this is a new session."""
        return not self.redis_client.exists(self.session_id)

    def set_latest_message_ts(self, timestamp: str) -> None:
        """Set the latest message timestamp for this session."""
        self.latest_message_ts = timestamp


_bot_user_id_cache: Optional[str] = None


async def get_bot_user_id() -> str:
    """Get the bot user ID from Slack API."""
    global _bot_user_id_cache

    if _bot_user_id_cache is not None:
        return _bot_user_id_cache

    try:
        # Run auth test to verify credentials
        auth_response = await app.client.auth_test()
        user_id = auth_response.get("user_id")

        if not user_id:
            raise Exception("Failed to get user_id from Slack auth response")

        logger.info(f"Slack Connection Established. Bot User ID: {user_id}")
        _bot_user_id_cache = user_id
        return user_id

    except SlackApiError as e:
        logger.error(f"Error creating Slack app: {e}")
        raise Exception(e)


@lru_cache(maxsize=256)
def get_session(session_id: str) -> Session:
    """Get or create a session instance."""
    return Session(session_id)


def remove_bot_user_id(input_text: str, bot_user_id: str) -> str:
    """Remove bot user ID mention from input text."""
    return input_text.replace(f"<@{bot_user_id}>", "").strip()


async def get_response(input_text: str, session: Session) -> str:
    """Get response from the AI agent using session context."""
    from agent import get_agent

    session_messages = session.get_messages()
    # Filter out None values
    valid_messages = [msg for msg in session_messages if msg is not None]

    bot_user_id = await get_bot_user_id()
    agent = await get_agent(bot_user_id)
    output = await agent.run(input_text, message_history=valid_messages)
    session.append_message(output.new_messages())

    return output.output


if __name__ == "__main__":

    async def main():
        session = Session("123")
        session.redis_client.json().delete("123", "$")

        response1 = await get_response("tell me joke", session)
        print(response1)

        response2 = await get_response("explain", session)
        print(response2)

        output = session.get_messages()
        print(output)

    import asyncio

    asyncio.run(main())
