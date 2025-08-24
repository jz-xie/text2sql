from pydantic import BaseModel, Field
from typing import List, Optional


class SlackBlockElement(BaseModel):
    type: str
    text: Optional[str] = None
    user_id: Optional[str] = Field(None, alias="user_id")


class SlackBlockElementSection(BaseModel):
    type: str
    elements: List[SlackBlockElement]


class SlackBlock(BaseModel):
    type: str
    block_id: str
    elements: List[SlackBlockElementSection]


class SlackBotProfile(BaseModel):
    id: str
    deleted: bool
    name: str
    updated: int
    app_id: str
    user_id: str
    icons: dict
    team_id: str


class SlackMessage(BaseModel):
    user: str
    type: str
    ts: str
    client_msg_id: Optional[str] = None
    text: str
    team: str
    thread_ts: Optional[str] = None
    reply_count: Optional[int] = None
    reply_users_count: Optional[int] = None
    latest_reply: Optional[str] = None
    reply_users: Optional[List[str]] = None
    is_locked: Optional[bool] = False
    subscribed: Optional[bool] = False
    blocks: List[SlackBlock]
    parent_user_id: Optional[str] = None
    bot_id: Optional[str] = None
    app_id: Optional[str] = None
    bot_profile: Optional[SlackBotProfile] = None


# Example usage:
if __name__ == "__main__":
    # Sample message data
    message_data = {
        "user": "U09AP8D5T6Z",
        "type": "message",
        "ts": "1755916792.936009",
        "client_msg_id": "cc1bcedc-50b1-42e2-b0e4-6b3cbd021fd0",
        "text": "Tell me a joke",
        "team": "T09AP8D5T4M",
        "thread_ts": "1755916792.936009",
        "reply_count": 1,
        "reply_users_count": 1,
        "latest_reply": "1755916802.520679",
        "reply_users": ["U09AP8D5T6Z"],
        "is_locked": False,
        "subscribed": False,
        "blocks": [
            {
                "type": "rich_text",
                "block_id": "ShBWU",
                "elements": [
                    {
                        "type": "rich_text_section",
                        "elements": [{"type": "text", "text": "Tell me a joke"}],
                    }
                ],
            }
        ],
    }

    # Parse the message
    slack_message = SlackMessage.model_validate(message_data)
    print(slack_message.model_dump_json(indent=2))
