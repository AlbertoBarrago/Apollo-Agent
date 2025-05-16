"""
ApolloAgent is a custom AI agent that implements various functions for code assistance.
Author: Alberto Barrago
License: MIT - 2025
"""

import asyncio
import json
import os
import re
import ollama
from typing import List, Dict, Any


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
        self.available_functions = {
            "codebase_search": self.codebase_search,
            "list_dir": self.list_dir,
            "grep_search": self.grep_search,
            "file_search": self.file_search,
            "delete_file": self.delete_file,
            "edit_file": self.edit_file,
            "reapply": self.reapply,
        }

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

    async def _generate_response(self, message: str) -> Dict[str, Any]:
        print(f"[_generate_response] Received message: {message}")

        try:
            llm_response = ollama.chat(
                model="llama3.1",
                messages=[{"role": "user", "content": message}],
                tools=self.get_available_tools()
            )

            print(llm_response["message"])

        except RuntimeError as e:
            print(f"[_generate_response] Error: {str(e)}")
            return {"error": f"Error generating response: {str(e)}"}

    async def _execute_tool_call(self, tool_call):
        """
        Executes a tool call based on the provided information.

        Args:
            tool_call: An object containing information about the tool to execute,
                       including the function name and arguments.

        Returns:
            The result of the tool execution, or an error message if execution fails
            or the tool is not found. Returns None if the tool call format is invalid.
        """
        if not (hasattr(tool_call, "function") and hasattr(tool_call.function, "name")):
            print(
                "[ERROR] Invalid tool call format: Missing 'function' or 'name' attribute."
            )
            return None

        func_name = tool_call.function.name
        arguments = tool_call.function.arguments

        if func_name in self.available_functions:
            function_to_call = self.available_functions[func_name]
            print(
                f"[_tool_execution] Calling function: {func_name} with args: {arguments}"
            )
            try:
                response = await function_to_call(**arguments)
                return response
            except Exception as e:  # Catch broader exceptions for robustness
                error_message = f"[ERROR] Error executing tool '{func_name}': {e}"
                print(error_message)
                return error_message
        else:
            error_message = (
                f"[ERROR] Tool '{func_name}' not found in available functions."
            )
            print(error_message)
            return error_message

    @staticmethod
    async def chat(text: str) -> Dict[str, Any]:
        """
        Responds to the user's message in a normal conversational way.

        Args:
            text: The user's message.

        Returns:
            A dictionary containing the chat response.
        """
        print(f"[_tool_execution] Executing chat with text: {text}")
        # Here, you would typically call the language model again
        # without any tools to get a natural chat response.
        try:
            llm_response = ollama.chat(
                model="llama3.1",
                messages=[{"role": "user", "content": text}],
            )
            response_content = (
                llm_response.message.content
                if hasattr(llm_response, "message")
                else str(llm_response)
            )
            print(f"[_tool_execution] Chat response: {response_content}")
            return {"response": response_content}
        except RuntimeError as e:
            error_message = f"[ERROR] Error generating chat response: {e}"
            print(error_message)
            return {"error": error_message}

    @staticmethod
    def get_available_tools() -> List[Dict[str, Any]]:
        """Get all available tools"""
        tools = [
            {
                "name": "codebase_search",
                "description": "Find snippets of code from the codebase most "
                "relevant to the search query.\nThis is a semantic search tool, "
                "so the query should ask for something semantically matching what "
                "is needed.\nIf it makes sense to only search in particular directories, "
                "please specify them in the target_directories field.\nUnless there is a "
                "clear reason to use your own search query, please just reuse the user's "
                "exact query with their wording.\nTheir exact wording/phrasing can often "
                "be helpful for the semantic search query. Keeping the same exact question "
                "format can also be helpful.",
                "parameters": [
                    {
                        "name": "query",
                        "type": "string",
                        "description": "The search query to find relevant code. "
                        "You should reuse the user's exact query/most recent message with "
                        "their wording unless there is a clear reason not to.",
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
                        "description": "One sentence explanation as to why this tool "
                        "is being used, and how it contributes to the goal.",
                    },
                ],
            },
            {
                "name": "list_dir",
                "description": "List the contents of a directory. The quick tool to use "
                "for discovery, before using more targeted tools like semantic "
                "search or file reading. Useful to try to understand the file "
                "structure before diving deeper into specific files. Can be used "
                "to explore the codebase.",
                "parameters": [
                    {
                        "name": "relative_workspace_path",
                        "type": "string",
                        "description": "Path to list contents of, relative to the workspace root.",
                    },
                    {
                        "name": "explanation",
                        "type": "string",
                        "description": "One sentence explanation as to why this tool is being used, "
                        "and how it contributes to the goal.",
                    },
                ],
            },
            {
                "name": "grep_search",
                "description": "Fast text-based regex search that finds exact pattern matches within files "
                "or directories, utilizing the ripgrep command for efficient searching."
                "Results will be formatted in the style of ripgrep and can be configured to include line numbers and content.\nTo avoid overwhelming output, the results are capped at 50 matches.\nUse the include or exclude patterns to filter the search scope by file type or specific paths.\n\nThis is best for finding exact text matches or regex patterns.\nMore precise than semantic search for finding specific strings or patterns.\nThis is preferred over semantic search when we know the exact symbol/function name/etc. to search in some set of directories/file types.",
                "parameters": [
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
                        "description": "One sentence explanation as to why this tool is being used, "
                        "and how it contributes to the goal.",
                    },
                ],
            },
            {
                "name": "file_search",
                "description": "Fast file search based on fuzzy matching against file path. "
                "Use if you know part of the file path but don't know where it's "
                "located exactly. The Response will be capped to 10 results. "
                "Make your query more specific if need to filter results further.",
                "parameters": [
                    {
                        "name": "query",
                        "type": "string",
                        "description": "Fuzzy filename to search for",
                    },
                    {
                        "name": "explanation",
                        "type": "string",
                        "description": "One sentence explanation as to why this tool is being used, "
                        "and how it contributes to the goal.",
                    },
                ],
            },
            {
                "name": "delete_file",
                "description": "Deletes a file at the specified path. The operation will fail gracefully if:\n    - The file doesn't exist\n    - The operation is rejected for security reasons\n    - The file cannot be deleted",
                "parameters": [
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
                "description": "Use this tool to propose an edit to an existing file.\n\n"
                "This will be read by a less intelligent model, which will quickly apply the edit. "
                "You should make it clear what the edit is, "
                "while also minimizing the unchanged code you write.\n"
                "When writing the edit, you should specify each edit in sequence, "
                "with the special comment `// ... existing code ...` to represent "
                "unchanged code in between edited lines.\n\nFor example:\n\n```\n// ... "
                "existing code ...\nFIRST_EDIT\n// ... existing code ...\nSECOND_EDIT\n// ... existing code ...\nTHIRD_EDIT\n// ... existing code ...\n```\n\nYou should still bias towards repeating as few lines of the original file as possible to convey the change.\nBut, each edit should contain sufficient context of unchanged lines around the code you're editing to resolve ambiguity.\nDO NOT omit spans of pre-existing code (or comments) without using the `// ... existing code ...` comment to indicate its absence. If you omit the existing code comment, the model may inadvertently delete these lines.\nMake sure it is clear what the edit should be, and where it should be applied.\n\nYou should specify the following arguments before the others: [target_file]",
                "parameters": [
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
                "parameters": [
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
                "name": "chat",
                "description": "Engage in a normal conversational exchange with the user. Use this when the user's request doesn't seem to require a specific tool or code-related action.",
                "parameters": [
                    {
                        "name": "text",
                        "type": "string",
                        "description": "The user's message to respond to in a conversational manner.",
                    },
                ],
            },
        ]
        return tools

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
        """
        Start Chat Session
        :return:
        """
        agent_apollo = ApolloAgent()
        print("Welcome to ApolloAgent Chat Mode!")
        print("Type 'exit' to end the conversation.")

        while True:
            user_input = input("> You: ")
            if user_input.lower() == "exit":
                break

            print("Apollo thinking...")
            response = await agent_apollo.chat(user_input, interactive=True)
            if response and isinstance(response, dict) and "error" in response:
                print(f"\nApollo (Error): {response['error']}")
            elif response and isinstance(response, dict) and "response" in response:
                print(f"\nApollo: {response['response']}")
            elif response and isinstance(response, str):
                print(f"\nApollo: {response}")
            elif response:
                print(f"\nApollo: {response}")


# Example usage
if __name__ == "__main__":
    asyncio.run(ApolloAgent.chat_terminal())
