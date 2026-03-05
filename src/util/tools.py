import inspect
from typing import Dict, Any, Callable, get_type_hints, get_origin, get_args, Union
from util.logging import get_logger

logger = get_logger()

def function_to_schema(func: Callable) -> Dict[str, Any]:
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
        if origin is int: json_type = "integer"
        elif origin is float: json_type = "number"
        elif origin is bool: json_type = "boolean"
        elif origin is list: json_type = "array"
        elif origin is dict: json_type = "object"
        else: json_type = "string"

        parameters["properties"][name] = {
            "type": json_type,
            "description": f"The {name} parameter."
        }

        # Array items handling
        if origin is list:
            args = get_args(hint)
            if args:
                # Recursively check the inner type if it's a simple type
                inner_origin = get_origin(args[0]) or args[0]
                inner_map = {str: "string", int: "integer", float: "number", bool: "boolean"}
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
        }
    }
    return schema