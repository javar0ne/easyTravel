import logging
import re
from enum import Enum

from flask import Flask
from openai import OpenAI

from app.exceptions import KeyNotFoundException

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

class Assistant:
    def __init__(self):
        self.client = OpenAI()
        self.openai_model = None

    def init_app(self, app: Flask):
        self.openai_model = app.config["OPENAI_MODEL"]

    def ask(self, conversation: Conversation):
        completion = self.client.beta.chat.completions.parse(
            model=self.openai_model,
            messages=conversation.messages,
            response_format=conversation.response_format,
        )

        parsed_response = completion.choices[0].message.parsed

        logger.info("assistant answered with: %s", parsed_response)

        return parsed_response
