from typing import Iterable, Optional
from openai import OpenAI
from openai.types.chat.chat_completion_assistant_message_param import (
    ChatCompletionAssistantMessageParam,
)
from openai.types.chat.chat_completion_function_message_param import (
    ChatCompletionFunctionMessageParam,
)
from openai.types.chat.chat_completion_message_param import ChatCompletionMessageParam
from openai.types.chat.chat_completion_system_message_param import (
    ChatCompletionSystemMessageParam,
)
from openai.types.chat.chat_completion_tool_message_param import (
    ChatCompletionToolMessageParam,
)
from openai.types.chat.chat_completion_user_message_param import (
    ChatCompletionUserMessageParam,
)

from text2sql.backend.connectors.clients import get_openai_chat_client


def system_message(
    message: str, name: Optional[str] = None
) -> ChatCompletionSystemMessageParam:
    if name is None:
        return ChatCompletionSystemMessageParam(role="system", content=message)
    else:
        return ChatCompletionSystemMessageParam(
            role="system", content=message, name=name
        )


def user_message(
    message: str, name: Optional[str] = None
) -> ChatCompletionUserMessageParam:
    if name is None:
        return ChatCompletionUserMessageParam(role="user", content=message)
    else:
        return ChatCompletionUserMessageParam(role="user", content=message, name=name)


def assistant_message(
    message: str, name: Optional[str] = None
) -> ChatCompletionAssistantMessageParam:
    if name is None:
        return ChatCompletionAssistantMessageParam(role="assistant", content=message)
    else:
        return ChatCompletionAssistantMessageParam(
            role="assistant", content=message, name=name
        )


def submit_prompt(
    prompt: Iterable[ChatCompletionMessageParam],
    client: OpenAI = get_openai_chat_client(),
    model: str = "gpt-4o-2024-10-21",
    temperature: float = 0.7,
) -> str | None:
    if prompt is None:
        raise Exception("Prompt is None")

    if len(prompt) == 0:
        raise Exception("Prompt is empty")

    response = client.chat.completions.create(
        model=model,
        messages=prompt,
        stop=None,
        temperature=temperature,
    )

    tokens = response.usage.total_tokens

    # If no response with text is found, return the first response's content (which may be empty)
    return response.choices[0].message.content
