import logging

from common.extensions import assistant, OPENAI_MODEL, MAX_COMPLETION_TOKEN

logger = logging.getLogger(__name__)

def ask_assistant(system_instructions: list[dict], response_format: type):
    completion = assistant.beta.chat.completions.parse(
        model=OPENAI_MODEL,
        messages=system_instructions,
        response_format=response_format,
    )

    return completion.choices[0].message.parsed

def ask_assistant_long_response(messages: list[dict], response_format: type):
    completion = assistant.beta.chat.completions.parse(
        model=OPENAI_MODEL,
        messages=messages,
        response_format=response_format,
        max_completion_tokens=MAX_COMPLETION_TOKEN
    )

    return completion.choices[0].message.parsed
