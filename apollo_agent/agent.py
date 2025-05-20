"""
ApolloAgent is a custom AI agent that implements various functions for code assistance.
Author: Alberto Barrago
License: BSD 3-Clause License - 2025
"""

import inspect
import os

from apollo_agent.search_operations import codebase_search, file_search
from apollo_agent.chat_operations import (
    chat,
)
from apollo_agent.file_operations import (
    list_dir,
    delete_file,
    edit_file,
    reapply,
)

APPOLO_WELCOME = """
                     
        # #   #####   ####  #      #       ####        
       #   #  #    # #    # #      #      #    #       
🤖     #     # #    # #    # #      #      #    #     🤖
      ####### #####  #    # #      #      #    #       
      #     # #      #    # #      #      #    #       
      #     # #       ####  ###### ######  ####        
    
      BSD 3-Clause License

      Copyright (c) 2025, Alberto Barrago
      All rights reserved.

            
            """


class ApolloAgent:
    """
    ApolloAgent is a custom AI agent that implements various functions for code assistance.
    This agent is inspired by the Claude 3.7 Sonnet agent for Cursor IDE.
    """

    def __init__(self, workspace_path: str = None):
        """
        Initialize the ApolloAgent with a workspace path.

        Args:
            workspace_path: The root path of the workspace to operate on.
                            Defaults to the current working directory if None.
        """
        self.workspace_path = workspace_path or os.getcwd()
        self.last_edit_file = None
        self.last_edit_content = None
        self.available_functions = {
            "codebase_search": codebase_search,
            "list_dir": list_dir,
            "file_search": file_search,
            "delete_file": delete_file,
            "edit_file": edit_file,
            "reapply": reapply,
            "chat": chat,
        }
        self.chat_history = []
        self.redirect_mapping = {
            "open": "edit_file",
            "touch": "edit_file",
            "edit": "edit_file",
            "create_file": "edit_file",
        }

    async def execute_tool(self, tool_call):
        """
        Execute a tool function call (from LLM) with validated arguments and secure redirection.
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

        redirected_name = self.redirect_mapping.get(func_name, func_name)

        func = self.available_functions.get(redirected_name)
        if not func:
            return f"[ERROR] Function '{redirected_name}' not found."

        filtered_args = filter_valid_args(func, arguments_dict)

        try:
            if inspect.iscoroutinefunction(func):
                result = await func(self, **filtered_args)
            else:
                result = func(self, **filtered_args)
            return result
        except RuntimeError as e:
            return f"[ERROR] Exception while executing '{redirected_name}': {e}"

    @staticmethod
    async def chat_terminal():
        """Start a Chat Session in the terminal."""
        print(APPOLO_WELCOME)
        workspace_path = input(
            "Enter the workspace path (or press Enter for current directory): "
        )
        if not workspace_path:
            workspace_path = os.getcwd()

        if not os.path.exists(workspace_path):
            os.makedirs(workspace_path)

        agent = ApolloAgent(workspace_path=workspace_path)
        print("🌟 Welcome to ApolloAgent Chat Mode!")
        print("Type 'exit' to end the conversation.")
        print("Workspace set to:", os.path.abspath(workspace_path))

        while True:
            try:
                user_input = input("\n> You: ")
                if user_input.lower() == "exit":
                    break

                text_improved = """
                You are a powerful agentic AI coding assistant, powered by Apollo Agent. You operate exclusively in Apollo.
                You are pair programming with a USER to solve their coding task.
                The task may require creating a new codebase, modifying or debugging an existing codebase, or simply answering a question.
                Each time the USER sends a message, we may automatically attach some information about their current state, such as what files they have opened, where their cursor is, recently viewed files, edit history in their session so far, linter errors, and more.
                This information may or may not be relevant to the coding task, it is up to you to decide.
                """
                response = await chat(agent, text_improved + user_input)

                if response and isinstance(response, dict) and "response" in response:
                    print(f"🤖 Apollo: {response['response']}")
                elif response and isinstance(response, dict) and "error" in response:
                    print(f"🤖 Apollo (Error): {response['error']}")
                else:
                    print(f"🤖 Apollo (Unexpected Response Format): {response}")

            except EOFError:
                print("\nExiting chat.")
                break
            except KeyboardInterrupt:
                print("\nExiting chat.")
                break
