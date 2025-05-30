"""
Tool execution for the ApolloAgent.

This module contains the ToolExecutor class, which is responsible for
executing tool and handling tool calls from the LLM.

Author: Alberto Barrago
License: BSD 3-Clause License - 2025
"""

import inspect
from typing import Any, Dict, Callable


class ToolExecutor:
    """
    ToolExecutor is responsible for executing tools and handling tool calls from the LLM.
    It provides a unified interface for tool execution, resolving the circular dependency
    between ApolloAgent and ApolloAgentChat.
    """

    def __init__(self, workspace_path: str = None):
        """
        Initialize the ToolExecutor with a workspace path.

        Args:
            workspace_path: The root path of the workspace to operate on.
        """
        self.workspace_path = workspace_path
        self.available_functions = {}
        self.last_edit_file = None
        self.last_edit_content = None

    def register_function(self, name: str, func: Callable) -> None:
        """
        Register a function to be available for tool execution.

        Args:
            name: The name of the function.
            func: The function to register.
        """
        self.available_functions[name] = func

    def register_functions(self, functions: Dict[str, Callable]) -> None:
        """
        Register multiple functions to be available for tool execution.

        Args:
            functions: A dictionary mapping function names to functions.
        """
        self.available_functions.update(functions)

    async def execute_tool(self, tool_call) -> Any:
        """
        Execute a tool function call (from LLM) with validated arguments

        Args:
            tool_call: The tool call from the LLM.

        Returns:
            The result of the tool execution.
        """

        def filter_valid_args(valid_func, args_dict):
            valid_params = valid_func.__code__.co_varnames[
                : valid_func.__code__.co_argcount
            ]
            return {k: v for k, v in args_dict.items() if k in valid_params}

        try:
            if hasattr(tool_call, "function"):
                func_name = getattr(tool_call.function, "name", None)
                raw_args = getattr(tool_call.function, "arguments", {})
            elif isinstance(tool_call, dict) and "function" in tool_call:
                func_name = tool_call["function"].get("name")
                raw_args = tool_call["function"].get("arguments", {})
            else:
                return "[ERROR] Invalid tool_call format or missing 'function'."

            if not func_name:
                return "[ERROR] Function name not provided in tool call."

            if isinstance(raw_args, str):
                arguments_dict = __import__("json").loads(raw_args)
            elif isinstance(raw_args, dict):
                arguments_dict = raw_args
            else:
                return f"[ERROR] Unsupported arguments type: {type(raw_args)}"
        except RuntimeError as e:
            return f"[ERROR] Failed to parse tool call: {e}"

        func = self.available_functions.get(func_name)
        if not func:
            return f"[ERROR] Function '{func_name}' not found."

        filtered_args = filter_valid_args(func, arguments_dict)

        sig = inspect.signature(func)
        params = sig.parameters

        args_to_pass = filtered_args.copy()

        if (
            "agent" in params
        ):  # Check if the tool function explicitly accepts an 'agent' parameter
            # If the tool function expects 'agent', pass the ToolExecutor instance itself.
            # This makes the ToolExecutor the "agent" for the tool.
            args_to_pass["agent"] = self

        try:
            if inspect.iscoroutinefunction(func):
                result = await func(**args_to_pass)
            else:
                result = func(**args_to_pass)
            return result
        except RuntimeError as e:
            return f"[ERROR] Failed to execute tool: {e}"
