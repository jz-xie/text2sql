from datetime import datetime, timezone
from typing import List, Optional
from slack_sdk.web.client import WebClient
from slack_sdk.errors import SlackApiError
from logging import getLogger
from pydantic_ai.messages import (
    ModelRequest,
    ModelResponse,
    TextPart,
    UserPromptPart,
    ModelMessage,
)
# from slack_sdk.models.messages.message import Message

logger = getLogger(__name__)


def remove_user_bot_id(message: str, user_bot_id: str) -> str:
    return message.replace(f"<@{user_bot_id}>", "").strip()


def get_message_with_role(slack_message: dict) -> str:
    content = f"User: <@{slack_message.get('user', '')}>\nMessage: {slack_message.get('text', '')}"
    return content


def convert_slack_messages_to_model_messages(
    slack_messages: list[dict],
) -> list[ModelMessage]:
    """
    Convert a list of Slack messages into a format compatible with pydantic-ai's message history.
    Each user message becomes a ModelRequest, and each bot message becomes a ModelResponse.
    """
    model_messages: list[ModelRequest | ModelResponse] = []

    for message in slack_messages:
        timestamp = datetime.fromtimestamp(
            float(message.get("ts", "")), tz=timezone.utc
        )

        if "bot_id" in message:  # This is a bot message
            # Convert bot messages to ModelResponse
            model_messages.append(
                ModelResponse(
                    parts=[TextPart(content=message.get("text", ""))],
                    # model_name="llama3.2",  # Using your default model
                    timestamp=timestamp,
                )
            )
        else:  # This is a user message
            # Convert user messages to ModelRequest with UserPromptPart
            user_message = get_message_with_role(message)
            model_messages.append(
                ModelRequest(
                    parts=[
                        UserPromptPart(
                            content=user_message,
                            timestamp=timestamp,
                        )
                    ]
                )
            )

    return model_messages


async def get_new_thread_messages(
    client: WebClient, channel_id: str, thread_ts: str, after_ts: str | None
) -> list[dict]:
    """Get all messages in a thread"""
    try:
        result = await client.conversations_replies(
            channel=channel_id,
            ts=thread_ts,
            inclusive=True,  # Include the parent message
        )
        messages = result.get("messages", [])

        if after_ts:
            messages = [msg for msg in messages if msg.get("ts", "") > after_ts]

        return messages
        # [:-1]  # Filter out the immediate message mentioning the bot
    except SlackApiError as e:
        logger.error(f"Error fetching thread replies: {e}")
        return []
