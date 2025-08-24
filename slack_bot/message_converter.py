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
    model_messages = []

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


async def get_thread_messages(
    client: WebClient, channel_id: str, thread_ts: str
) -> list[dict | None]:
    """Get all messages in a thread"""
    try:
        result = await client.conversations_replies(
            channel=channel_id,
            ts=thread_ts,
            inclusive=True,  # Include the parent message
        )
        return result["messages"]
    except SlackApiError as e:
        print(f"Error fetching thread replies: {e}")
        return []


# async def get_thread_messages(
#     client: WebClient, channel_id: str, thread_ts: str, limit: int = 100
# ) -> List[SlackMessage]:
#     """
#     Retrieve all messages from a Slack thread.

#     Args:
#         client: Slack WebClient instance
#         channel_id: The ID of the channel containing the thread
#         thread_ts: The timestamp of the parent message
#         limit: Maximum number of messages to retrieve (default: 100)

#     Returns:
#         List[SlackMessage]: List of messages in the thread, including the parent message
#     """
#     try:
#         # Get the thread messages
#         result = await client.conversations_replies(
#             channel=channel_id,
#             ts=thread_ts,
#             limit=limit,
#             inclusive=True,  # Include the parent message
#         )

#         if not result["ok"]:
#             logger.error(f"Failed to fetch thread messages: {result['error']}")
#             return []

#         # Convert raw messages to SlackMessage objects
#         messages = [SlackMessage.model_validate(msg) for msg in result["messages"]]

#         # Sort messages by timestamp
#         return sorted(messages, key=lambda x: float(x.ts))

#     except SlackApiError as e:
#         logger.error(f"Error fetching thread messages: {e.response['error']}")
#         return []


# async def get_conversation_history(
#     client: WebClient,
#     channel_id: str,
#     thread_ts: Optional[str] = None,
#     limit: int = 100,
# ) -> List[SlackMessage]:
#     """
#     Get conversation history from a channel or thread.
#     If thread_ts is provided, fetches thread messages, otherwise fetches channel messages.

#     Args:
#         client: Slack WebClient instance
#         channel_id: The ID of the channel
#         thread_ts: Optional timestamp of thread parent message
#         limit: Maximum number of messages to retrieve

#     Returns:
#         List[SlackMessage]: List of messages in chronological order
#     """
#     try:
#         if thread_ts:
#             return await get_thread_messages(client, channel_id, thread_ts, limit)

#         # Get channel messages if no thread_ts provided
#         result = await client.conversations_history(channel=channel_id, limit=limit)

#         if not result["ok"]:
#             logger.error(f"Failed to fetch channel messages: {result['error']}")
#             return []

#         # Convert and sort messages
#         messages = [SlackMessage.model_validate(msg) for msg in result["messages"]]
#         return sorted(messages, key=lambda x: float(x.ts))

#     except SlackApiError as e:
#         logger.error(f"Error fetching conversation history: {e.response['error']}")
#         return []


# Example usage:
if __name__ == "__main__":
    import asyncio
    from slack_sdk.web.async_client import AsyncWebClient
    from config import settings

    async def main():
        # Initialize Slack client
        client = AsyncWebClient(token=settings.slack_bot_token)

        # Example thread fetch
        messages = await get_conversation_history(
            client=client, channel_id="C1234567890", thread_ts="1234567890.123456"
        )

        # Convert to model history
        conversation_messages = extract_conversation_messages(messages)
        model_history = convert_slack_messages_to_model_history(conversation_messages)

        # Print results
        for msg in model_history:
            print(msg.model_dump_json(indent=2))

    # Run the async example
    asyncio.run(main())
