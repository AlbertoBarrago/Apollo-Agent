"""
ApolloAgent is a custom AI agent that implements various functions for code assistance.

This is the main module for the ApolloAgent agent.
The functions chat_terminal and execute_tool are responsible
for the chat mode and tool execution, respectively.

Author: Alberto Barrago
License: BSD 3-Clause License - 2025
"""

import os

from apollo.tools.search import (
    codebase_search,
    file_search,
    grep_search,
)
from apollo.tools.chat import ApolloAgentChat
from apollo.tools.files import (
    list_dir,
    delete_file,
    edit_file_or_create,
    remove_dir,
)
from apollo.tools.executor import ToolExecutor
from apollo.config.const import Constant
from apollo.tools.web import web_search, wiki_search


class ApolloAgent:
    """
    ApolloAgent is a custom AI agent that implements various functions for code assistance.
    """

    def __init__(self, workspace_path: str = None):
        """
        Initialize the ApolloAgent with a workspace path.

        Args:
            workspace_path: The root path of the workspace to operate on.
                            Defaults to the current working directory if None.
        """
        self.workspace_path = workspace_path or os.getcwd()

        # Initialize the tool executor
        self.tool_executor = ToolExecutor(self.workspace_path)

        # Initialize the chat agent
        self.chat_agent = ApolloAgentChat()
        self.chat_agent.set_tool_executor(self.tool_executor)

        # Register functions with the tool executor
        self.tool_executor.register_functions(
            {   "edit_file_or_create": edit_file_or_create,
                "delete_file": delete_file,
                "list_dir": list_dir,
                "file_search": file_search,
                "chat": self.chat_agent.chat,
                "grep_search": grep_search,
                "web_search": web_search,
                "remove_dir": remove_dir,
                "wiki_search": wiki_search,
            }
        )

        # Load chat history
        # self.chat_agent.load_chat_history(
        #     file_path=Constant.CHAT_HISTORY_FILE,
        #     max_session_messages=Constant.MAX_SESSION_MESSAGES)

    async def execute_tool(self, tool_call):
        """
        Execute a tool function call (from LLM) with
        validated arguments and secure redirection.

        This method is now a wrapper around the ToolExecutor's
        execute_tool method for backward compatibility.
        """
        return await self.tool_executor.execute_tool(tool_call)

    @staticmethod
    async def chat_terminal():
        """Start a Chat Session in the terminal."""
        print(Constant.APPOLO_WELCOME)
        workspace_cabled = Constant.WORKSPACE_CABLED  # ./workspace
        if not os.path.exists(workspace_cabled):
            workspace_path = input(
                "Enter the workspace path." f"The workspace path is ${workspace_cabled}"
            )
        else:
            workspace_path = workspace_cabled
        if not os.path.exists(workspace_path) and workspace_path != "exit":
            os.makedirs(workspace_path)
        if workspace_path == "exit":
            return

        agent = ApolloAgent(workspace_path=workspace_path)
        print("🌟 Welcome to ApolloAgent Chat Mode!")
        print("Type 'exit' to end the conversation.")
        print("Workspace set to:", os.path.abspath(workspace_path))

        while True:
            try:
                user_input = input("\n> You: ")
                if user_input.lower() == "exit":
                    break

                prompt = f"${Constant.PROMPT_FINE_TUNE_V1} The command is ${user_input}"
                response = await agent.chat_agent.chat(prompt)

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
