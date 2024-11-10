import logging
import re
from enum import Enum

from common.exceptions import KeyNotFoundException
from common.extensions import assistant, OPENAI_MODEL, MAX_COMPLETION_TOKEN

logger = logging.getLogger(__name__)

class ConversationRole(Enum):
    USER = "user"
    ASSISTANT = "assistant"
    SYSTEM = "system"

class Conversation:
    def __init__(self, response_format: type):
        self.response_format = response_format
        self.messages = []

    def add_message(self, role, content):
        self.messages.append({
            'role': role,
            'content': self.encode(content)
        })

    def add_message_from(self, element: dict):
        if "role" not in element or "content" not in element:
            raise KeyNotFoundException()

        self.messages.append({
            'role': element["role"],
            'content': self.encode(element["content"])
        })

    @staticmethod
    def create_message(role, content):
        return {
            'role': role,
            'content': Conversation.encode(content)
        }

    @staticmethod
    def encode(content: str):
        return re.sub(r'\s+', ' ', content).strip()

def ask_assistant(conversation: Conversation):
    completion = assistant.beta.chat.completions.parse(
        model=OPENAI_MODEL,
        messages=conversation.messages,
        response_format=conversation.response_format,
    )

    return completion.choices[0].message.parsed

def ask_assistant_long_response(conversation: Conversation, response_format: type):
    completion = assistant.beta.chat.completions.parse(
        model=OPENAI_MODEL,
        messages=conversation.messages,
        response_format=response_format,
        max_completion_tokens=MAX_COMPLETION_TOKEN
    )

    return completion.choices[0].message.parsed
