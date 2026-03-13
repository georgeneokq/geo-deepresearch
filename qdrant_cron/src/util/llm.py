import asyncio
import random
import re
import inspect
import json
from typing import Optional, List, Callable, TypeVar, Union
from pydantic import BaseModel
from openai import AsyncOpenAI, RateLimitError
from openai.types.chat import ParsedChatCompletionMessage
from util.logger import get_logger

from typing import Dict, Any, Callable, get_type_hints, get_origin, get_args, Union

logger = get_logger()


def function_to_schema(func: Callable) -> Dict[str, Any]:
    sig = inspect.signature(func)
    type_hints = get_type_hints(func)
    doc = inspect.getdoc(func) or "No description provided."

    parameters = {"type": "object", "properties": {}, "required": []}

    for name, param in sig.parameters.items():
        if name in ("self", "cls"):
            continue

        hint = type_hints.get(name, str)
        origin = get_origin(hint) or hint

        # --- Handle Optional/Union types ---
        # If it's Union[int, None], origin is Union. We want the 'int'.
        if origin is Union:
            args = get_args(hint)
            # Filter out NoneType (type(None))
            non_none_args = [a for a in args if a is not type(None)]
            if non_none_args:
                hint = non_none_args[0]
                origin = get_origin(hint) or hint

        # Type Mapping Logic
        if origin is int:
            json_type = "integer"
        elif origin is float:
            json_type = "number"
        elif origin is bool:
            json_type = "boolean"
        elif origin is list:
            json_type = "array"
        elif origin is dict:
            json_type = "object"
        else:
            json_type = "string"

        parameters["properties"][name] = {
            "type": json_type,
            "description": f"The {name} parameter.",
        }

        # Array items handling
        if origin is list:
            args = get_args(hint)
            if args:
                # Recursively check the inner type if it's a simple type
                inner_origin = get_origin(args[0]) or args[0]
                inner_map = {
                    str: "string",
                    int: "integer",
                    float: "number",
                    bool: "boolean",
                }
                inner_type = inner_map.get(inner_origin, "object")
                parameters["properties"][name]["items"] = {"type": inner_type}

        if param.default is inspect.Parameter.empty:
            parameters["required"].append(name)

    schema = {
        "type": "function",
        "function": {
            "name": func.__name__,
            "description": doc,
            "parameters": parameters,
        },
    }
    return schema


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
        user_messages = [{"role": "user", "content": user}]

    messages = [{"role": "system", "content": system}, *user_messages]

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

    response = None
    max_retries = 3
    for attempt in range(max_retries):
        try:
            response = await client.chat.completions.create(**kwargs)
            break
        except RateLimitError as e:
            logger.error(str(e))
            # Exponential backoff with a little bit of random jitter (0 to 1000ms)
            wait_time = (2**attempt) + random.random()

            logger.warning(
                f"Rate limit hit in call_llm. Retrying in {wait_time:.2f}s..."
            )
            await asyncio.sleep(wait_time)

    if not response:
        raise RuntimeError(f"call_llm failed after {max_retries} tries.")

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
