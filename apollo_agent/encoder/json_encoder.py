"""
Custom JSON encoder to handle complex objects in ApolloAgent.

This module provides a custom JSONEncoder implementation that properly handles
objects from Ollama API responses that aren't natively JSON serializable.

Author: Alberto Barrago
License: BSD 3-Clause License - 2024
"""

import json
from typing import Any


class ApolloJSONEncoder(json.JSONEncoder):
    """
    Custom JSON encoder that handles complex objects from Ollama API responses.
    Handles Message objects, tool_calls, and other non-serializable types.
    Also cleans the content strings by removing excess whitespace.
    """

    def default(self, obj: Any) -> Any:
        """
        Process objects that aren't natively JSON serializable.

        Args:
            obj: The object to encode

        Returns:
            A JSON serializable representation of the object
        """
        # Handle objects with __dict__ attribute (like Message objects)
        if hasattr(obj, "__dict__"):
            result = obj.__dict__.copy()
            return result

        # Handle objects with role and content attributes
        if hasattr(obj, "role") and hasattr(obj, "content"):
            result = {"role": obj.role, "content": obj.content}

            # Handle additional attributes that might be present
            if hasattr(obj, "tool_calls"):
                result["tool_calls"] = obj.tool_calls
            if hasattr(obj, "images"):
                result["images"] = obj.images

            return result

        # Handle other special cases like tool_calls objects
        if hasattr(obj, "id") and (hasattr(obj, "function") or hasattr(obj, "type")):
            result = {"id": obj.id}

            if hasattr(obj, "function"):
                result["function"] = obj.function
            if hasattr(obj, "type"):
                result["type"] = obj.type

            return result

        # As a last resort, convert to string
        try:
            return str(obj)
        except SystemError as e:
            return f"<Unserializable object of type {type(obj).__name__}, error: {e}>"
