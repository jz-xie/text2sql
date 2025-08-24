import redis
from logging import getLogger
from typing import Any, Optional
from functools import lru_cache
from pydantic_ai import Agent
from pydantic_ai.models.openai import OpenAIModel
from pydantic_ai.providers.openai import OpenAIProvider
from pydantic_core import to_jsonable_python
from pydantic_ai.messages import ModelMessagesTypeAdapter, ModelMessage
from slack_setup import slack_bot

logger = getLogger(__name__)


class Session:
    # Class-level Redis client shared by all instances
    _redis_client: Optional[redis.Redis] = None

    @classmethod
    def _get_redis_client(cls):
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

    def get_messages(self) -> list[ModelMessage | None]:
        messages_json = self.redis_client.json().get(self.session_id)
        if not messages_json:
            return []
        else:
            return ModelMessagesTypeAdapter.validate_python(messages_json)

    def append_message(self, messages: list[ModelMessage]):
        messages_json = to_jsonable_python(messages)

        if self.is_new():
            # Initialize with the messages at root level to avoid extra nesting
            self.redis_client.json().set(self.session_id, ".", messages_json)
            logger.info("Session initialized in Redis")
        else:
            self.redis_client.json().arrappend(self.session_id, ".", *messages_json)
            logger.info("Appended values in Redis")

    def is_new(self):
        return not self.redis_client.exists(self.session_id)


@lru_cache(maxsize=256)
def get_session(session_id: str) -> Session:
    return Session(session_id)


@lru_cache
def get_agent():
    # Create the Ollama-backed model
    ollama_model = OpenAIModel(
        model_name="llama3.2",
        provider=OpenAIProvider(
            base_url="http://localhost:11434/v1"
        ),  # Ollama's default API endpoint
    )
    #
    agent = Agent(model=ollama_model, instructions=slack_bot.system_prompt)
    return agent
