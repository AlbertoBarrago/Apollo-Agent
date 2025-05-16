"""
ApolloAgent is a custom AI agent that implements various functions for code assistance.
Author: Alberto Barrago
License: MIT - 2025
"""

import asyncio
import os
import re
from typing import List, Dict, Any, Coroutine


class ApolloAgent:
    """
    ApolloAgent is a custom AI agent that implements various functions for code assistance.
    This agent is inspired by the Claude 3.7 Sonnet agent for Cursor IDE.
    """

    def __init__(self, workspace_path: str = None):
        """
        Initialize the ApolloAgent with a workspace path and configure HuggingFace tools.

        Args:
            workspace_path: The root path of the workspace to operate on.
                            Defaults to the current working directory if None.
        """
        self.workspace_path = workspace_path or os.getcwd()
        self.last_edit_file = None
        self.last_edit_content = None
        self.chat_history = []

        from code_agent import HuggingFaceTools

        self.hf_tools = HuggingFaceTools(self)
        self.hf_tools.prepare_code_agent()

    def get_available_tools(self) -> List[Dict[str, Any]]:
        """Get all available tools, including HuggingFace CodeAgent tools."""
        tools = [
            {
                "name": "codebase_search",
                "description": "Find snippets of code from the codebase most relevant to the search query.\nThis is a semantic search tool, so the query should ask for something semantically matching what is needed.\nIf it makes sense to only search in particular directories, please specify them in the target_directories field.\nUnless there is a clear reason to use your own search query, please just reuse the user's exact query with their wording.\nTheir exact wording/phrasing can often be helpful for the semantic search query. Keeping the same exact question format can also be helpful.",
                "parameters": [  # Changed to a list
                    {
                        "name": "query",
                        "type": "string",
                        "description": "The search query to find relevant code. You should reuse the user's exact query/most recent message with their wording unless there is a clear reason not to.",
                    },
                    {
                        "name": "target_directories",
                        "type": "array",
                        "items": {"type": "string"},
                        "description": "Glob patterns for directories to search over",
                    },
                    {
                        "name": "explanation",
                        "type": "string",
                        "description": "One sentence explanation as to why this tool is being used, and how it contributes to the goal.",
                    },
                ],
            },
            {
                "name": "list_dir",
                "description": "List the contents of a directory. The quick tool to use for discovery, before using more targeted tools like semantic search or file reading. Useful to try to understand the file structure before diving deeper into specific files. Can be used to explore the codebase.",
                "parameters": [  # Changed to a list
                    {
                        "name": "relative_workspace_path",
                        "type": "string",
                        "description": "Path to list contents of, relative to the workspace root.",
                    },
                    {
                        "name": "explanation",
                        "type": "string",
                        "description": "One sentence explanation as to why this tool is being used, and how it contributes to the goal.",
                    },
                ],
            },
            {
                "name": "grep_search",
                "description": "Fast text-based regex search that finds exact pattern matches within files or directories, utilizing the ripgrep command for efficient searching.\nResults will be formatted in the style of ripgrep and can be configured to include line numbers and content.\nTo avoid overwhelming output, the results are capped at 50 matches.\nUse the include or exclude patterns to filter the search scope by file type or specific paths.\n\nThis is best for finding exact text matches or regex patterns.\nMore precise than semantic search for finding specific strings or patterns.\nThis is preferred over semantic search when we know the exact symbol/function name/etc. to search in some set of directories/file types.",
                "parameters": [  # Changed to a list
                    {
                        "name": "query",
                        "type": "string",
                        "description": "The regex pattern to search for",
                    },
                    {
                        "name": "case_sensitive",
                        "type": "boolean",
                        "description": "Whether the search should be case sensitive",
                    },
                    {
                        "name": "include_pattern",
                        "type": "string",
                        "description": "Glob pattern for files to include (e.g. '*.ts' for TypeScript files)",
                    },
                    {
                        "name": "exclude_pattern",
                        "type": "string",
                        "description": "Glob pattern for files to exclude",
                    },
                    {
                        "name": "explanation",
                        "type": "string",
                        "description": "One sentence explanation as to why this tool is being used, and how it contributes to the goal.",
                    },
                ],
            },
            {
                "name": "file_search",
                "description": "Fast file search based on fuzzy matching against file path. Use if you know part of the file path but don't know where it's located exactly. The Response will be capped to 10 results. Make your query more specific if need to filter results further.",
                "parameters": [  # Changed to a list
                    {
                        "name": "query",
                        "type": "string",
                        "description": "Fuzzy filename to search for",
                    },
                    {
                        "name": "explanation",
                        "type": "string",
                        "description": "One sentence explanation as to why this tool is being used, and how it contributes to the goal.",
                    },
                ],
            },
            {
                "name": "delete_file",
                "description": "Deletes a file at the specified path. The operation will fail gracefully if:\n    - The file doesn't exist\n    - The operation is rejected for security reasons\n    - The file cannot be deleted",
                "parameters": [  # Changed to a list
                    {
                        "name": "target_file",
                        "type": "string",
                        "description": "The path of the file to delete, relative to the workspace root.",
                    },
                    {
                        "name": "explanation",
                        "type": "string",
                        "description": "One sentence explanation as to why this tool is being used, and how it contributes to the goal.",
                    },
                ],
            },
            {
                "name": "edit_file",
                "description": "Use this tool to propose an edit to an existing file.\n\nThis will be read by a less intelligent model, which will quickly apply the edit. You should make it clear what the edit is, while also minimizing the unchanged code you write.\nWhen writing the edit, you should specify each edit in sequence, with the special comment `// ... existing code ...` to represent unchanged code in between edited lines.\n\nFor example:\n\n```\n// ... existing code ...\nFIRST_EDIT\n// ... existing code ...\nSECOND_EDIT\n// ... existing code ...\nTHIRD_EDIT\n// ... existing code ...\n```\n\nYou should still bias towards repeating as few lines of the original file as possible to convey the change.\nBut, each edit should contain sufficient context of unchanged lines around the code you're editing to resolve ambiguity.\nDO NOT omit spans of pre-existing code (or comments) without using the `// ... existing code ...` comment to indicate its absence. If you omit the existing code comment, the model may inadvertently delete these lines.\nMake sure it is clear what the edit should be, and where it should be applied.\n\nYou should specify the following arguments before the others: [target_file]",
                "parameters": [  # Changed to a list
                    {
                        "name": "target_file",
                        "type": "string",
                        "description": "The target file to modify. Always specify the target file as the first argument. You can use either a relative path in the workspace or an absolute path. If an absolute path is provided, it will be preserved as is.",
                    },
                    {
                        "name": "instructions",
                        "type": "string",
                        "description": "A single sentence instruction describing what you are going to do for the sketched edit. This is used to assist the less intelligent model in applying the edit. Please use the first person to describe what you are going to do. Dont repeat what you have said previously in normal messages. And use it to disambiguate uncertainty in the edit.",
                    },
                    {
                        "name": "code_edit",
                        "type": "string",
                        "description": "Specify ONLY the precise lines of code that you wish to edit. **NEVER specify or write out unchanged code**. Instead, represent all unchanged code using the comment of the language you're editing in - example: `// ... existing code ...`",
                    },
                    {
                        "name": "explanation",
                        "type": "string",
                        "description": "One sentence explanation as to why this tool is being used, and how it contributes to the goal.",
                    },
                ],
            },
            {
                "name": "reapply",
                "description": "Calls a smarter model to apply the last edit to the specified file.\nUse this tool immediately after the result of an edit_file tool call ONLY IF the diff is not what you expected, indicating the model applying the changes was not smart enough to follow your instructions.",
                "parameters": [  # Changed to a list
                    {
                        "name": "target_file",
                        "type": "string",
                        "description": "The relative path to the file to reapply the last edit to. You can use either a relative path in the workspace or an absolute path. If an absolute path is provided, it will be preserved as is.",
                    },
                    {
                        "name": "explanation",
                        "type": "string",
                        "description": "One sentence explanation as to why this tool is being used, and how it contributes to the goal.",
                    },
                ],
            },
            {
                "name": "what_is_luck",
                "description": "Explains the concept of luck.",
                "parameters": [  # Changed to a list
                    {
                        "name": "explanation",
                        "type": "string",
                        "description": "One sentence explanation as to why this tool is being used, and how it contributes to the goal.",
                    },
                ],
            },
        ]
        tools.extend(self.hf_tools.get_tools())
        return tools

    async def execute_tool(
        self, tool_name: str, **kwargs: Any
    ) -> Dict[str, Any] | None:
        """Execute a tool by name with given parameters."""
        if (
            hasattr(self.hf_tools, "code_agent")
            and tool_name in self.hf_tools.code_agent.tools
        ):
            print(f"CodeAgent is calling tool: {tool_name} with arguments: {kwargs}")
            # Use a dictionary to map tool names to methods for cleaner code
            tool_methods = {
                "codebase_search": self.codebase_search,
                "list_dir": self.list_dir,
                "grep_search": self.grep_search,
                "file_search": self.file_search,
                "delete_file": self.delete_file,
                "edit_file": self.edit_file,
                "reapply": self.reapply,
            }
            if tool_name in tool_methods:
                return await tool_methods[tool_name](**kwargs)

            return {"error": f"Tool '{tool_name}' not implemented in ApolloAgent"}

        # Handle existing tools (if you intend to call them directly as well)
        if tool_name == "list_dir":
            return await self.list_dir(
                **kwargs
            )  # Ensure consistency with async if needed
        return None

    async def codebase_search(
        self, query: str, target_directories: List[str] = None
    ) -> Dict[str, Any]:
        """
        Find snippets of code from the codebase most relevant to the search query.

        Args:
            query: The search query to find relevant code.
            target_directories: Glob patterns for directories to search over.

        Returns:
            Dictionary containing search results.
        """
        print(f"Performing semantic search for: {query}")

        # This is a placeholder implementation
        # In a real implementation, this would use a vector database or similar technology
        results = []

        search_dirs = (
            target_directories if target_directories else [self.workspace_path]
        )

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
                        except OSError as e:  # Changed ValueError to OSError
                            print(f"Error reading file {file_path}: {e}")

        return {"query": query, "results": results}

    async def list_dir(self, relative_workspace_path: str) -> Dict[str, Any]:
        """
        List the contents of a directory.

        Args:
            relative_workspace_path: Path to list contents of, relative to the workspace root.

        Returns:
            Dictionary containing directory contents.
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
            query: The regex pattern to search for.
            case_sensitive: Whether the search should be case-sensitive.
            include_pattern: Glob pattern for files to include.
            exclude_pattern: Glob pattern for files to exclude.

        Returns:
            Dictionary containing search results.
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
                except OSError as e:
                    print(f"Error reading file {file_path}: {e}")

                # Cap results at 50 matches
                if len(results) >= 50:
                    break

        return (
            {
                "query": query,
                "case_sensitive": case_sensitive,
                "include_pattern": include_pattern,
                "exclude_pattern": exclude_pattern,
                "results": results,
                "total_matches": len(results),
                "capped": len(results) >= 50,
            }
            if results
            else {
                "query": query,
                "case_sensitive": case_sensitive,
                "include_pattern": include_pattern,
                "exclude_pattern": exclude_pattern,
                "results": [],
                "total_matches": 0,
                "capped": False,
            }
        )

    async def file_search(self, query: str) -> Dict[str, Any]:
        """
        Fast file search based on fuzzy matching against a file path.

        Args:
            query: Fuzzy filename to search for.

        Returns:
            Dictionary containing search results.
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
            target_file: The path of the file to delete, relative to the workspace root.

        Returns:
            Dictionary containing an operation result.
        """
        file_path = os.path.join(self.workspace_path, target_file)

        if not os.path.exists(file_path):
            return {"success": False, "error": f"File does not exist: {file_path}"}

        if not os.path.isfile(file_path):
            return {"success": False, "error": f"Path is not a file: {file_path}"}

        try:
            os.remove(file_path)
            return {"success": True, "message": f"File deleted: {target_file}"}
        except OSError as e:  # Changed RuntimeError to OSError
            return {"success": False, "error": f"Failed to delete file: {str(e)}"}

    async def edit_file(self, target_file: str, content: str) -> Dict[str, Any]:
        """
        Edit a file with the provided content.

        Args:
            target_file: The path of the file to edit, relative to the workspace root.
            content: The new content for the file.

        Returns:
            Dictionary containing an operation result.
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
        except OSError as e:  # Changed RuntimeError to OSError
            return {"success": False, "error": f"Failed to edit file: {str(e)}"}

    async def reapply(self, target_file: str) -> Dict[str, Any]:
        """
        Reapplies the last edit to the specified file.

        Args:
            target_file: The path of the file to reapply the last edit to.

        Returns:
            Dictionary containing an operation result.
        """
        if self.last_edit_file != target_file or self.last_edit_content is None:
            return {
                "success": False,
                "error": "No previous edit found for this file or edit content is missing.",
            }

        return await self.edit_file(target_file, self.last_edit_content)

    async def _generate_response(
        self, message: str
    ) -> Coroutine[Any, Any, Dict[str, Any]] | Dict[str, Any]:
        """
        Generate a response to the user's message using the HuggingFace CodeAgent.

        Args:
            message: The user's message

        Returns:
            A dictionary containing the agent's response (and potential additional information).
        """
        if hasattr(self, "hf_tools") and self.hf_tools.code_agent:
            try:
                response = await self.hf_tools.run_code_agent(message)
                return {"response": response}
            except Exception as e:
                print(f"Errore durante l'esecuzione del CodeAgent: {e}")
                return {"error": f"Errore durante l'esecuzione del CodeAgent: {e}"}
        else:
            print("HuggingFace CodeAgent non inizializzato.")
            return {"message": await self._fallback_response(message)}

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
            python_result = await self._execute_python_if_present(message)
            if python_result:
                message += f"\n\nExecution result:\n{python_result}"

        # Generate a response based on the message
        response = await self._generate_response(message)

        # Add agent response to chat history
        self.chat_history.append({"role": "assistant", "content": response})

        # Check if the response contains Python code to execute
        response_python_result = None
        if execute_python:
            if isinstance(response, dict) and "response" in response:
                response_content = response["response"]
                execution_result = await self._execute_python_if_present(
                    response_content
                )
                if execution_result:
                    response["response"] += f"\n\nExecution result:\n{execution_result}"
                    # Update the chat history with the execution result
                    self.chat_history[-1]["content"] = response["response"]
            elif isinstance(response, str):
                execution_result = await self._execute_python_if_present(response)
                if execution_result:
                    response += f"\n\nExecution result:\n{execution_result}"
                    # Update the chat history with the execution result
                    self.chat_history[-1]["content"] = response

        if interactive:
            # In interactive mode, print the response directly
            if isinstance(response, dict) and "response" in response:
                print(f"\nApollo: {response['response']}")
                return {"success": True}
            elif isinstance(response, dict) and "message" in response:
                print(f"\nApollo: {response['message']}")
                return {"success": True}
            elif isinstance(response, dict) and "error" in response:
                print(f"\nApollo (Error): {response['error']}")
                return {"success": False, "error": response["error"]}
            else:
                print(f"\nApollo: {response}")
                return {"success": True}

        # In non-interactive mode, return the response as part of the result
        result_resp = {
            "message": message,
            "history_length": len(self.chat_history),
        }

        if isinstance(response, dict) and "response" in response:
            result_resp["response"] = response["response"]
        elif isinstance(response, dict) and "message" in response:
            result_resp["response"] = response["message"]
        elif isinstance(response, str):
            result_resp["response"] = response

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
        Generate a fallback response when the CodeAgent is not available.

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
                "- Reapplying the last edit\n"
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
            if user_input.lower() == "exit":
                break

            print("Apollo thinking...")
            response = await agent_apollo.chat(user_input, interactive=True)
            if response and "error" in response:
                pass


# Example usage
if __name__ == "__main__":
    asyncio.run(ApolloAgent.chat_terminal())
