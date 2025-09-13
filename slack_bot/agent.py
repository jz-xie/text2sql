import logging
from typing import Optional

from openai import AsyncAzureOpenAI
from pydantic_ai import Agent
from pydantic_ai.models.openai import OpenAIChatModel
from pydantic_ai.providers.openai import OpenAIProvider

from config import settings

logger = logging.getLogger(__name__)


class OnCallAgent:
    """OnCall Slack bot agent configuration."""

    def __init__(self, bot_user_id: Optional[str] = None):
        self.bot_user_id = bot_user_id
        self.system_prompt = f"""You are a helpful Slack bot with ID {bot_user_id}.

When you refer someone, mention them with '<@USER_ID>'.

User input will be with the following format:
User: <@USER_ID>
Message: <MESSAGE_CONTENT>

Your role is to assist users with their queries and provide accurate, helpful responses.
When users mention you in a thread, you have access to the full conversation history of that thread.
Please be professional, concise, and clear in your responses.
"""


_agent_cache: Optional[Agent] = None


async def get_agent(bot_user_id: str) -> Agent:
    """Get the AI agent instance."""
    global _agent_cache

    if _agent_cache is not None:
        return _agent_cache

    if settings.openai is not None:
        client = AsyncAzureOpenAI(
            azure_endpoint=settings.openai.azure_endpoint,
            api_version=settings.openai.api_version,
            api_key=settings.openai.api_key,
            azure_deployment=settings.openai.azure_deployment,
        )
        model = OpenAIChatModel(
            "gpt-4o",
            provider=OpenAIProvider(openai_client=client),
        )

    else:
        model = OpenAIChatModel(
            model_name="llama3.2",
            provider=OpenAIProvider(
                base_url="http://localhost:11434/v1"
            ),  # Ollama's default API endpoint
        )

    # Create agent with default system prompt, bot ID will be resolved at runtime
    slack_bot = OnCallAgent(bot_user_id=bot_user_id)
    agent = Agent(model=model, instructions=slack_bot.system_prompt)
    _agent_cache = agent
    return agent
