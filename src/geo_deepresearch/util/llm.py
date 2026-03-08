import os
import json
from geo_deepresearch.tools.time import append_current_datetime
from typing import Optional, List, Callable, TypeVar, Union
from geo_deepresearch.util.tools import function_to_schema
from geo_deepresearch.util.logging import get_logger
from pydantic import BaseModel
from langfuse.openai import AsyncOpenAI as LangfuseAsyncOpenAI
from openai import AsyncOpenAI
from openai.types.chat import ParsedChatCompletionMessage
import re

logger = get_logger()

# Globally shared client to prevent redundant multi initialization
openai_default_client = LangfuseAsyncOpenAI(
    api_key=os.environ.get("DEEP_RESEARCH_API_KEY"),
    base_url=os.environ.get("DEEP_RESEARCH_BASE_URL"),
)
openai_default_model = os.environ.get("DEEP_RESEARCH_MODEL", "z-ai/glm-4.7-flash")

# Create a TypeVar that is bound to BaseModel
# This allows the IDE to know that the return type matches the input schema
T = TypeVar("T", bound=BaseModel)


async def call_llm(
    client: AsyncOpenAI,
    model: str,
    system: str,
    user: str | list[str],
    tools: Optional[List[Callable]] = None,
    force_tool: Optional[Callable] = None,
    output_schema: Optional[type[T]] = None,
    max_tokens: Optional[int] = None,
    temperature: float = 0.6,
) -> Union[ParsedChatCompletionMessage[T], ParsedChatCompletionMessage[str]]:
    """
    Standardized LLM call that introspects Python functions on the fly.
    Automatically appends datetime to the end of the system prompt for temporal awareness.

    Uses .parse() for all calls; if output_schema is passed in, read the parsed JSON from .parsed,
    instead of reading from .content

    Raises:
        pydantic.ValidationError: If the LLM response doesn't match output_schema.
    """
    if isinstance(user, list):
        if not len(user):
            raise ValueError("User message cannot be empty")

        user_messages = [
            {"role": "user", "content": user_message} for user_message in user
        ]
    else:
        user_messages = [
            {"role": "user", "content": user}
        ]

    messages = [
        {"role": "system", "content": append_current_datetime(system)},
        *user_messages
    ]

    kwargs = {"model": model, "messages": messages, "temperature": temperature}

    if max_tokens:
        kwargs["max_tokens"] = max_tokens

    # Handle on-the-fly tool introspection
    if tools:
        kwargs["tools"] = [function_to_schema(f) for f in tools]

    # Handle tool forcing
    if force_tool:
        # If force_tool is passed but not in tools list, add it automatically
        if not tools or force_tool not in tools:
            kwargs.setdefault("tools", []).append(function_to_schema(force_tool))

        kwargs["tool_choice"] = {
            "type": "function",
            "function": {"name": force_tool.__name__},
        }

    response = await client.chat.completions.create(**kwargs)

    message = response.choices[0].message

    # Handle output schema
    if output_schema:
        extracted_json = extract_json_from_llm_output(message.content)
        parsed_data = json.loads(extracted_json)
        message.parsed = output_schema.model_validate(parsed_data)

    # Logging
    reasoning = getattr(message, "reasoning_content", None) or getattr(
        message, "reasoning", None
    )
    logger.debug(
        f"LLM call complete.{f'\nReasoning:\n{reasoning}\n\n' if reasoning else '\n\n'}Content:\n{message.content}"
    )
    logger.debug("Full LLM call message:")
    logger.debug(message)

    return message


def extract_json_from_llm_output(message: str):
    """
    Extract parsable JSON from LLM output
    """
    return re.sub(r"^```[a-zA-Z]*\s+(.*?)\s*```", r"\1", message, flags=re.DOTALL)
