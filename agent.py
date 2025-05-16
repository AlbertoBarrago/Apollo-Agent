"""
ApolloAgent is a custom AI agent that implements various functions for code assistance.
Author: Alberto Barrago
License: MIT - 2025
"""
import asyncio
import os
import re
from typing import List, Dict, Any


class ApolloAgent:
    """
    ApolloAgent is a custom AI agent that implements various functions for code assistance.
    This agent is inspired by the Claude 3.7 Sonnet agent for Cursor IDE.
    """

    def __init__(self, workspace_path: str = None):
        """
        Initialize the ApolloAgent with a workspace path and configure Gemini API.

        Args:
            workspace_path: The root path of the workspace to operate on
            to use GOOGLE_API_KEY environment variable
        """
        self.workspace_path = workspace_path or os.getcwd()
        self.last_edit_file = None
        self.last_edit_content = None
        self.chat_history = []

        from code_agent import HuggingFaceTools
        self.hf_tools = HuggingFaceTools(self)
        self.hf_tools.prepare_code_agent()

    def get_available_tools(self):
        """Get all available tools including HuggingFace CodeAgent tools"""
        tools = [
            {
                "name": "codebase_search",
                "description": "Find snippets of code from the codebase most "
                               "relevant to the search query",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "query": {
                            "type": "string",
                            "description": "The search query to find relevant code"
                        },
                        "target_directories": {
                            "type": "array",
                            "items": {"type": "string"},
                            "description": "Glob patterns for directories to search over"
                        }
                    },
                    "required": ["query"]
                }
            },
            {
                "name": "list_dir",
                "description": "List the contents of a directory",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "relative_workspace_path": {
                            "type": "string",
                            "description": "Path to list contents of, relative to the workspace root"
                        }
                    },
                    "required": ["relative_workspace_path"]
                }
            },
            {
                "name": "grep_search",
                "description": "Fast text-based regex search that finds exact pattern "
                               "matches within files or directories",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "query": {
                            "type": "string",
                            "description": "The regex pattern to search for"
                        },
                        "case_sensitive": {
                            "type": "boolean",
                            "description": "Whether the search should be case-sensitive"
                        },
                        "include_pattern": {
                            "type": "string",
                            "description": "Glob pattern for files to include"
                        },
                        "exclude_pattern": {
                            "type": "string",
                            "description": "Glob pattern for files to exclude"
                        }
                    },
                    "required": ["query"]
                }
            },
            {
                "name": "file_search",
                "description": "Fast file search based on fuzzy matching against a file path",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "query": {
                            "type": "string",
                            "description": "Fuzzy filename to search for"
                        }
                    },
                    "required": ["query"]
                }
            },
            {
                "name": "delete_file",
                "description": "Deletes a file at the specified path",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "target_file": {
                            "type": "string",
                            "description": "The path of the file to delete, relative to the workspace root"
                        }
                    },
                    "required": ["target_file"]
                }
            },
            {
                "name": "edit_file",
                "description": "Edit a file with the provided content",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "target_file": {
                            "type": "string",
                            "description": "The path of the file to edit, relative to the workspace root"
                        },
                        "content": {
                            "type": "string",
                            "description": "The new content for the file"
                        }
                    },
                    "required": ["target_file", "content"]
                }
            },
            {
                "name": "reapply",
                "description": "Reapplies the last edit to the specified file",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "target_file": {
                            "type": "string",
                            "description": "The path of the file to reapply the last edit to"
                        }
                    },
                    "required": ["target_file"]
                }
            },
            {
                "name": "web_search",
                "description": "Search the web for real-time information about any topic",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "search_term": {
                            "type": "string",
                            "description": "The search term to look up on the web"
                        }
                    },
                    "required": ["search_term"]
                }
            },
            {
                "name": "diff_history",
                "description": "Retrieve the history of recent changes made "
                               "to files in the workspace",
                "parameters": {
                    "type": "object",
                    "properties": {},
                    "required": []
                }
            }
        ]
        tools.extend(self.hf_tools.get_tools())
        return tools

    async def execute_tool(self, tool_name: str, **kwargs):
        """Execute a tool by name with given parameters"""
        if hasattr(self.hf_tools, "code_agent") and tool_name in self.hf_tools.code_agent.tools:
            print(f"CodeAgent is calling tool: {tool_name} with arguments: {kwargs}")
            if tool_name == "codebase_search":
                return await self.codebase_search(query=kwargs["query"],
                                                  target_directories=kwargs.get("target_directories"))
            if tool_name == "list_dir":
                return await self.list_dir(relative_workspace_path=kwargs["relative_workspace_path"])
            if tool_name == "grep_search":
                return await self.grep_search(query=kwargs["query"], case_sensitive=kwargs.get("case_sensitive", False),
                                              include_pattern=kwargs.get("include_pattern"),
                                              exclude_pattern=kwargs.get("exclude_pattern"))
            if tool_name == "file_search":
                return await self.file_search(query=kwargs["query"])
            if tool_name == "delete_file":
                return await self.delete_file(target_file=kwargs["target_file"])
            if tool_name == "edit_file":
                return await self.edit_file(target_file=kwargs["target_file"], content=kwargs["content"])
            if tool_name == "reapply":
                return await self.reapply(target_file=kwargs["target_file"])
            if tool_name == "web_search":
                return await self.web_search(search_term=kwargs["search_term"])
            if tool_name == "diff_history":
                return await self.diff_history()

            return {"error": f"Tool '{tool_name}' not implemented in ApolloAgent"}

        # Handle existing tools (if you intend to call them directly as well)
        if tool_name == "list_dir":
            return await self.list_dir(**kwargs)  # Ensure consistency with async if needed
        return None

    async def codebase_search(
            self, query: str, target_directories: List[str] = None
    ) -> Dict[str, Any]:
        """
        Find snippets of code from the codebase most relevant to the search query.

        Args:
            query: The search query to find relevant code
            target_directories: Glob patterns for directories to search over

        Returns:
            Dictionary containing search results
        """
        print(f"Performing semantic search for: {query}")

        # This is a placeholder implementation
        # In a real implementation, this would use a vector database or similar technology
        results = []

        if target_directories:
            search_dirs = target_directories
        else:
            search_dirs = [self.workspace_path]

        for directory in search_dirs:
            for root, _, files in os.walk(directory):
                for file in files:
                    if file.endswith(
                            (".py", ".js", ".ts", ".html", ".css", ".java", ".c", ".cpp")
                    ):
                        file_path = os.path.join(root, file)
                        try:
                            with open(file_path, "r", encoding="utf-8") as f:
                                content = f.read()
                                if query.lower() in content.lower():
                                    results.append(
                                        {
                                            "file_path": file_path,
                                            "content": (
                                                content[:200] + "..."
                                                if len(content) > 200
                                                else content
                                            ),
                                            "relevance_score": 0.8,  # Placeholder score
                                        }
                                    )
                        except ValueError as e:
                            print(f"Error reading file {file_path}: {e}")

        return {"query": query, "results": results}

    async def list_dir(self, relative_workspace_path: str) -> Dict[str, Any]:
        """
        List the contents of a directory.

        Args:
            relative_workspace_path: Path to list contents of relative to the workspace root

        Returns:
            Dictionary containing directory contents
        """
        target_path = os.path.join(self.workspace_path, relative_workspace_path)

        if not os.path.exists(target_path):
            return {"error": f"Path does not exist: {target_path}"}

        if not os.path.isdir(target_path):
            return {"error": f"Path is not a directory: {target_path}"}

        contents = os.listdir(target_path)

        files = []
        directories = []

        for item in contents:
            item_path = os.path.join(target_path, item)
            if os.path.isdir(item_path):
                directories.append(item)
            else:
                files.append(item)

        return {
            "path": relative_workspace_path,
            "directories": directories,
            "files": files,
        }

    async def grep_search(
            self,
            query: str,
            case_sensitive: bool = False,
            include_pattern: str = None,
            exclude_pattern: str = None,
    ) -> Dict[str, Any]:
        """
        Fast text-based regex search that finds exact pattern matches within files or directories.

        Args:
            query: The regex pattern to search for
            case_sensitive: Whether the search should be case-sensitive
            include_pattern: Glob pattern for files to include
            exclude_pattern: Glob pattern for files to exclude

        Returns:
            Dictionary containing search results
        """
        results = []
        flags = 0 if case_sensitive else re.IGNORECASE

        for root, _, files in os.walk(self.workspace_path):
            for file in files:
                file_path = os.path.join(root, file)

                # Apply to include/exclude patterns if provided
                if include_pattern and not self._match_pattern(file, include_pattern):
                    continue
                if exclude_pattern and self._match_pattern(file, exclude_pattern):
                    continue

                try:
                    with open(file_path, "r", encoding="utf-8") as f:
                        for i, line in enumerate(f, 1):
                            if re.search(query, line, flags=flags):
                                results.append(
                                    {
                                        "file": file_path,
                                        "line_number": i,
                                        "content": line.strip(),
                                    }
                                )

                                # Cap results at 50 matches
                                if len(results) >= 50:
                                    break
                except Exception as e:
                    print(f"Error reading file {file_path}: {e}")

                # Cap results at 50 matches
                if len(results) >= 50:
                    break

        return {
            "query": query,
            "case_sensitive": case_sensitive,
            "include_pattern": include_pattern,
            "exclude_pattern": exclude_pattern,
            "results": results,
            "total_matches": len(results),
            "capped": len(results) >= 50,
        }

    async def file_search(self, query: str) -> Dict[str, Any]:
        """
        Fast file search based on fuzzy matching against a file path.

        Args:
            query: Fuzzy filename to search for

        Returns:
            Dictionary containing search results
        """
        results = []

        for root, _, files in os.walk(self.workspace_path):
            for file in files:
                if query.lower() in file.lower():
                    file_path = os.path.join(root, file)
                    results.append({"file_path": file_path, "filename": file})

                    # Cap results at 10
                    if len(results) >= 10:
                        break

            # Cap results at 10
            if len(results) >= 10:
                break

        return {
            "query": query,
            "results": results,
            "total_matches": len(results),
            "capped": len(results) >= 10,
        }

    async def delete_file(self, target_file: str) -> Dict[str, Any]:
        """
        Deletes a file at the specified path.

        Args:
            target_file: The path of the file to delete, relative to the workspace root

        Returns:
            Dictionary containing an operation result
        """
        file_path = os.path.join(self.workspace_path, target_file)

        if not os.path.exists(file_path):
            return {"success": False, "error": f"File does not exist: {file_path}"}

        if not os.path.isfile(file_path):
            return {"success": False, "error": f"Path is not a file: {file_path}"}

        try:
            os.remove(file_path)
            return {"success": True, "message": f"File deleted: {target_file}"}
        except Exception as e:
            return {"success": False, "error": f"Failed to delete file: {str(e)}"}

    async def edit_file(self, target_file: str, content: str) -> Dict[str, Any]:
        """
        Edit a file with the provided content.

        Args:
            target_file: The path of the file to edit, relative to the workspace root
            content: The new content for the file

        Returns:
            Dictionary containing an operation result
        """
        file_path = os.path.join(self.workspace_path, target_file)

        # Store the last edit for potential reapplication
        self.last_edit_file = target_file
        self.last_edit_content = content

        try:
            # Create a directory if it doesn't exist
            os.makedirs(os.path.dirname(file_path), exist_ok=True)

            with open(file_path, "w", encoding="utf-8") as f:
                f.write(content)

            return {"success": True, "message": f"File edited: {target_file}"}
        except Exception as e:
            return {"success": False, "error": f"Failed to edit file: {str(e)}"}

    async def reapply(self, target_file: str) -> Dict[str, Any]:
        """
        Reapplies the last edit to the specified file.

        Args:
            target_file: The path of the file to reapply the last edit to

        Returns:
            Dictionary containing an operation result
        """
        if self.last_edit_file != target_file or self.last_edit_content is None:
            return {
                "success": False,
                "error": "No previous edit found for this file or edit content is missing",
            }

        return self.edit_file(target_file, self.last_edit_content)

    async def web_search(self, search_term: str) -> Dict[str, Any]:
        """
        Search the web for real-time information about any topic.

        Args:
            search_term: The search term to look up on the web

        Returns:
            Dictionary containing search results
        """
        # This is a placeholder implementation
        # In a real implementation, this would use a search API
        print(f"Performing web search for: {search_term}")

        return {
            "search_term": search_term,
            "message": "Web search functionality requires integration with a search API.",
        }

    async  def _generate_response(self, message: str) -> str:
        """
        Generate a response to the user's message using Gemini Flash if available.

        Args:
            message: The user's message

        Returns:
            The agent's response
        """
        # Use Gemini Flash if available
        if hasattr(self, "gemini_available") and self.gemini_available:
            try:
                # Send a message to Gemini and get a response
                response = self.chat_session.send_message(message)
                return response.text
            except SystemError as e:
                print(f"Error generating response with Gemini: {str(e)}")
                # Fall back to placeholder implementation if Gemini fails
                return self._fallback_response(message)
        else:
            # Use placeholder implementation if Gemini is not available
            return self._fallback_response(message)

    @staticmethod
    async def diff_history() -> Dict[str, Any]:
        """
        Retrieve the history of recent changes made to files in the workspace.

        Returns:
            Dictionary containing diff history
        """
        # This is a placeholder implementation
        # In a real implementation, this would track file changes
        # TODO: please fix me
        return {
            "message": "Diff history functionality requires "
                       "integration with a version control system."
        }

    @staticmethod
    async def _match_pattern(filename: str, pattern: str) -> bool:
        """
        Check if a filename matches a glob pattern.

        Args:
            filename: The filename to check
            pattern: The glob pattern to match against

        Returns:
            True if the filename matches the pattern, False otherwise
        """
        import fnmatch

        return fnmatch.fnmatch(filename, pattern)

    async def chat(
            self, message: str, interactive: bool = False, execute_python: bool = False
    ) -> Dict[str, Any]:
        """
        Simulates a chat conversation with the agent, similar to ChatGPT.
        Can also execute Python code if requested.

        Args:
            message: The user's message
            interactive: Whether to run in interactive mode (for CLI)
            execute_python: Whether to execute Python code found in the message or response

        Returns:
            Dictionary containing the agent's response
        """
        # Add a user message to the chat history
        self.chat_history.append({"role": "user", "content": message})

        # Check if the message contains Python code to execute
        python_result = None
        if execute_python:
            python_result = self._execute_python_if_present(message)
            if python_result:
                message += f"\n\nExecution result:\n{python_result}"

        # Generate a response based on the message
        response = self._generate_response(message)

        # Add agent response to chat history
        self.chat_history.append({"role": "assistant", "content": response})

        # Check if the response contains Python code to execute
        response_python_result = None
        if execute_python:
            response_python_result = self._execute_python_if_present(response)
            if response_python_result:
                response += f"\n\nExecution result:\n{response_python_result}"
                # Update the chat history with the execution result
                self.chat_history[-1]["content"] = response

        if interactive:
            # In interactive mode, print the response directly
            print(f"\nApollo: {response}")
            return {"success": True}

        # In non-interactive mode, return the response as part of the result
        result_resp = {
            "message": message,
            "response": response,
            "history_length": len(self.chat_history),
        }

        if python_result:
            result_resp["user_code_execution"] = python_result
        if response_python_result:
            result_resp["assistant_code_execution"] = response_python_result

        return result_resp

    @staticmethod
    async def _execute_python_if_present(text: str) -> str | None:
        """
        Extracts and executes Python code blocks from a text.

        Args:
            text: Text that may contain Python code blocks

        Returns:
            Execution result as string, or None if no code was executed
        """
        import re
        import sys
        from io import StringIO

        # Find Python code blocks (```python ... ```)
        code_blocks = re.findall(r"```python\s+(.*?)\s+```", text, re.DOTALL)

        if not code_blocks:
            return None

        results = []
        for code in code_blocks:
            # Capture stdout
            old_stdout = sys.stdout
            redirected_output = StringIO()
            sys.stdout = redirected_output

            try:
                # Execute the code
                exec(code)
                execution_result = redirected_output.getvalue()
                results.append(f"Execution successful:\n{execution_result}")
            except Exception as e:
                results.append(f"Execution failed: {str(e)}")
            finally:
                # Restore stdout
                sys.stdout = old_stdout

        return "\n\n".join(results)

    @staticmethod
    async def _fallback_response(message: str) -> str:
        """
        Generate a fallback response when Gemini is not available.

        Args:
            message: The user's message

        Returns:
            The agent's fallback response
        """
        # Check for greetings
        if any(
                greeting in message.lower()
                for greeting in ["hello", "hi", "hey", "greetings"]
        ):
            return "Hello! I'm Apollo, your AI assistant. How can I help you today?"

        # Check for questions about capabilities
        if "what can you do" in message.lower() or "help" in message.lower():
            return (
                "I can help you with various tasks related to code assistance, such as:\n"
                "- Searching your codebase\n"
                "- Listing directory contents\n"
                "- Searching for files\n"
                "- Editing files\n"
                "- Answering questions about programming\n"
                "Just let me know what you need!"
            )

        # Check for code-related questions
        if any(
                code_term in message.lower()
                for code_term in ["code", "program", "function", "class", "method"]
        ):
            return "I can help with coding questions. Could you provide more details about what you're working on?"

        # Default response
        return "I'm here to assist with your coding tasks. Could you please provide more details about what you need help with?"

    @staticmethod
    async def chat_terminal():
        """Runs an interactive chat session with the ApolloAgent in the terminal."""
        agent_apollo = ApolloAgent()
        print("Welcome to ApolloAgent Chat Mode!")
        print("Type 'exit' to end the conversation.")

        while True:
            user_input = input("> You: ")
            if user_input.lower() == 'exit':
                break

            print("Apollo thinking...")
            response = await agent_apollo.chat(user_input)
            if response and "response" in response:
                print(f"Apollo: {response['response']}")
            elif response and "message" in response:
                print(f"Apollo: {response['message']}")
            elif response and "error" in response:
                print(f"Apollo (Error): {response['error']}")
            else:
                print("Apollo: (No response)")


# Example usage
if __name__ == "__main__":
    asyncio.run(ApolloAgent.chat_terminal())
