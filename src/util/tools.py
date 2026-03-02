import json
import logging
import inspect
from typing import Optional, Dict, Any, List, Callable, get_type_hints

logger = logging.getLogger()
logger.setLevel(logging.DEBUG)

def function_to_schema(func: Callable) -> Dict[str, Any]:
    """
    Introspects a function to create an OpenAI tool schema.
    Skips 'self' and 'cls' to ensure the LLM doesn't try to pass them.
    """
    sig = inspect.signature(func)
    type_hints = get_type_hints(func)
    doc = inspect.getdoc(func) or "No description provided."
    
    parameters = {
        "type": "object",
        "properties": {},
        "required": []
    }

    for name, param in sig.parameters.items():
        if name in ("self", "cls"):
            continue
            
        arg_type = type_hints.get(name, str)
        # TODO: Fix list[str] causes type of types.GenericAlias
        if arg_type == int: json_type = "integer"
        elif arg_type == float: json_type = "number"
        elif arg_type == bool: json_type = "boolean"
        elif arg_type == list: json_type = "array"
        elif arg_type == dict: json_type = "object"
        else: json_type = "string"

        parameters["properties"][name] = {
            "type": json_type,
            "description": f"The {name} parameter."
        }

        if param.default is inspect.Parameter.empty:
            parameters["required"].append(name)

    schema = {
        "type": "function",
        "function": {
            "name": func.__name__,
            "description": doc,
            "parameters": parameters,
        }
    }
    logger.debug(f"Converted function to tool schema:\n{json.dumps(schema)}")

    return schema