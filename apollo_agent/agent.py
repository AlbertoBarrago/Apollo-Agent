"""
ApolloAgent is a custom AI agent that implements various functions for code assistance.
Author: Alberto Barrago
License: MIT - 2025
"""

import asyncio
import os
from typing import List, Dict, Any

from apollo_agent.file_operations import list_dir, delete_file, edit_file, reapply
from apollo_agent.search_operations import codebase_search, grep_search, file_search
from apollo_agent.chat_operations import (
    chat,
    _execute_tool_call,
    get_available_tools,
)


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
        self.chat_history = []
        self.available_functions = {
            "codebase_search": self.codebase_search,
            "list_dir": self.list_dir,
            "grep_search": self.grep_search,
            "file_search": self.file_search,
            "delete_file": self.delete_file,
            "edit_file": self.edit_file,
            "reapply": self.reapply,
            "chat": self.chat,
        }

    # File operations
    async def list_dir(self, relative_workspace_path: str) -> Dict[str, Any]:
        """List the contents of a directory relative to the workspace root."""
        return await list_dir(self.workspace_path, relative_workspace_path)

    async def delete_file(self, target_file: str) -> Dict[str, Any]:
        """Deletes a file at the specified path relative to the workspace root."""
        return await delete_file(self.workspace_path, target_file)

    async def edit_file(self, target_file: str, code_edit: str) -> Dict[str, Any]:
        """
        Edit a file at the specified path (relative to workspace root) or CREATE A NEW ONE.
        Provide instructions and the FULL-DESIRED CONTENT in `code_edit`.
        """
        result = await edit_file(self.workspace_path, target_file, code_edit)
        self.last_edit_file = target_file
        self.last_edit_content = code_edit
        return result

    async def reapply(self, target_file: str) -> Dict[str, Any]:
        """Reapplies the last edit to the specified file."""
        return await reapply(self, target_file)

    # Search operations
    async def codebase_search(
        self, query: str, target_directories: List[str] = None
    ) -> Dict[str, Any]:
        """
        Find snippets of code from the codebase most relevant to the search query.
        This is a semantic search tool.
        """
        return await codebase_search(self.workspace_path, query, target_directories)

    async def grep_search(
        self,
        query: str,
        case_sensitive: bool = False,
        include_pattern: str = None,
        exclude_pattern: str = None,
    ) -> Dict[str, Any]:
        """
        Fast text-based regex search that finds exact pattern matches within files or directories.
        Best for finding specific strings or patterns.
        """
        return await grep_search(
            self.workspace_path, query, case_sensitive, include_pattern, exclude_pattern
        )

    async def file_search(self, query: str) -> Dict[str, Any]:
        """Fast file search based on fuzzy matching against a file path."""
        return await file_search(self.workspace_path, query)

    async def _execute_tool_call(self, tool_call):
        """
        Executes a tool call based on the provided information from ollama.chat response.
        """
        return await _execute_tool_call(self, tool_call)

    async def chat(self, text: str) -> None | dict[str, str] | dict[str, Any | None]:
        """
        Responds to the user's message, handling potential tool calls and multi-turn interactions.
        """
        return await chat(self, text)

    @staticmethod
    def get_available_tools() -> List[Dict[str, Any]]:
        """Get all available tools in the Ollama tools format."""
        return get_available_tools()

    @staticmethod
    async def chat_terminal():
        """Start a Chat Session in the terminal."""
        print("""                          
              # #   #####   ####  #      #       ####                # #    ####  ###### #    # ##### 
             #   #  #    # #    # #      #      #    #              #   #  #    # #      ##   #   #   
            #     # #    # #    # #      #      #    #    #####    #     # #      #####  # #  #   #   
            ####### #####  #    # #      #      #    #             ####### #  ### #      #  # #   #   
            #     # #      #    # #      #      #    #             #     # #    # #      #   ##   #   
            #     # #       ####  ###### ######  ####              #     #  ####  ###### #    #   #""")

        if not os.path.exists("./workspace"):
            os.makedirs("./workspace")
            print("Created a dummy './workspace' directory for testing.")

        agent_apollo = ApolloAgent(workspace_path="./workspace")
        print("Welcome to ApolloAgent Chat Mode!")
        print("Type 'exit' to end the conversation.")
        print("Workspace set to:", os.path.abspath("./workspace"))

        while True:
            try:
                user_input = input("\n> You: ")
                if user_input.lower() == "exit":
                    break

                response = await agent_apollo.chat(user_input)

                if response and isinstance(response, dict) and "response" in response:
                    print(f"\n>>> Apollo: {response['response']}")
                elif response and isinstance(response, dict) and "error" in response:
                    print(f"\n>>> Apollo (Error): {response['error']}")
                else:
                    print(f"\n>>> Apollo (Unexpected Response Format): {response}")

            except EOFError:
                print("\nExiting chat.")
                break
            except KeyboardInterrupt:
                print("\nExiting chat.")
                break
            except Exception as e:
                print(
                    f"\nAn unexpected error occurred during chat_terminal execution: {e}"
                )


# Example usage
if __name__ == "__main__":
    asyncio.run(ApolloAgent.chat_terminal())
