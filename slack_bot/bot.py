from pydantic import BaseModel
from functools import lru_cache
import asyncio
from pydantic_core import to_jsonable_python
from logging import getLogger
from pydantic_ai import UserPromptNode

from session_manager import get_session, Session, get_agent
from slack_setup import slack_bot

logger = getLogger(__name__)
# def get_slack_conversation(thread_ts: str):
#     if thread_ts not in message_history:
#         message_history[thread_ts] = []
#     messages_json = message_history.get(thread_ts, [])
#     return messages_json


# def get_session_messages(session_id: str):
#     if session_id not in message_history:
#         message_history[session_id] = []
#     # messages_json = message_history.get(session_id, [])
#     messages_json = session.get_messages()
#     print(messages_json)
#     if not messages_json:
#         return []
#     messages = ModelMessagesTypeAdapter.validate_python(messages_json)
#     return messages


def remove_bot_user_id(input: str):
    return input.replace(f"<@{slack_bot.bot_user_id}>", "").strip()
    # bot_user_id.set_bot_user_id(None)


async def get_response(input: str, session: Session) -> str:
    # Get or create SessionManager instance from cache
    # if session_id not in session_cache:
    # session = session_cache[session_id]

    session_messages = session.get_messages()

    agent = get_agent()
    output = await agent.run(input, message_history=session_messages)

    session.append_message(output.new_messages())

    return output.output


if __name__ == "__main__":
    session = Session("123")

    session.redis_client.json().delete("123", "$")
    # print(get_response("hi", "123"))
    print(get_response("tell me joke", "123"))
    print(get_response("explain", "123"))

    output = session.get_messages()
    print(output)
    #

    # print(get_response("explain", "123"))
    # > This is an excellent joke invented by Samuel Colvin, it needs no explanation.
# print(get_response("hi", "123"))

# print(get_response("tell me joke", "123"))

# print(get_response("explain", "123"))
# > This is an excellent joke invented by Samuel Colvin, it needs no explanation.

# print(result2.all_messages())
# print(result2.new_messages())
# print(output.all_messages_json())  # Print all messages in the conversation
# print("-----------")
# print(output.new_messages_json())
