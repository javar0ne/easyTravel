import logging

from common.extensions import assistant, OPENAI_MODEL

logger = logging.getLogger(__name__)

def ask_assistant(system_instructions: list[dict], response_format: type):
    completion = assistant.beta.chat.completions.parse(
        model=OPENAI_MODEL,
        messages=system_instructions,
        response_format=response_format,
    )

    return completion.choices[0].message.parsed
