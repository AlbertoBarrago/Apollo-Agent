"""
ApolloAgent is a custom AI agent that implements various functions for code assistance.
Author: Alberto Barrago
License: MIT - 2025
"""

import asyncio
import os
import re
import ollama
import json
from typing import List, Dict, Any
import fnmatch


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

    async def codebase_search(
        self, query: str, target_directories: List[str] = None, explanation: str = None
    ) -> Dict[str, Any]:
        """
        Find snippets of code from the codebase most relevant to the search query.
        This is a semantic search tool.
        """
        results = []
        search_dirs = target_directories if target_directories else [self.workspace_path]

        for directory in search_dirs:
            absolute_dir = os.path.abspath(directory)
            if not absolute_dir.startswith(os.path.abspath(self.workspace_path)):
                print(f"[WARNING] Skipping directory outside workspace: {directory}")
                continue

            if not os.path.isdir(absolute_dir):
                 print(f"[WARNING] Path is not a directory, skipping: {directory}")
                 continue

            for root, _, files in os.walk(absolute_dir):
                for file in files:
                    if file.endswith(
                        (".py", ".js", ".ts", ".html", ".css", ".java", ".c", ".cpp", ".txt")
                    ):
                        file_path = os.path.join(root, file)
                        try:
                            with open(file_path, "r", encoding="utf-8") as f:
                                content = f.read()
                                if query.lower() in content.lower():
                                    results.append(
                                        {
                                            "file_path": os.path.relpath(file_path, self.workspace_path),
                                            "content_snippet": (
                                                content[:500] + "..."
                                                if len(content) > 500
                                                else content
                                            ),
                                            "relevance_score": 0.8,
                                        }
                                    )
                        except OSError as e:
                            print(f"[ERROR] Error reading file {file_path}: {e}")

        return {"query": query, "results": results}

    async def list_dir(self, relative_workspace_path: str, explanation: str = None) -> Dict[str, Any]:
        """
        List the contents of a directory relative to the workspace root.
        """
        target_path = os.path.join(self.workspace_path, relative_workspace_path)
        absolute_target_path = os.path.abspath(target_path)

        if not absolute_target_path.startswith(os.path.abspath(self.workspace_path)):
             error_msg = f"Attempted to list directory outside workspace: {relative_workspace_path}"
             print(f"[ERROR] {error_msg}")
             return {"error": error_msg}

        if not os.path.exists(absolute_target_path):
            error_msg = f"Path does not exist: {relative_workspace_path}"
            print(f"[ERROR] {error_msg}")
            return {"error": error_msg}

        if not os.path.isdir(absolute_target_path):
            error_msg = f"Path is not a directory: {relative_workspace_path}"
            print(f"[ERROR] {error_msg}")
            return {"error": error_msg}

        contents = os.listdir(absolute_target_path)

        files = []
        directories = []

        for item in contents:
            item_path = os.path.join(absolute_target_path, item)
            if os.path.isdir(item_path):
                directories.append(item)
            else:
                files.append(item)

        return {
            "path": relative_workspace_path,
            "directories": directories,
            "files": files,
        }

    def _match_pattern_sync(self, filename: str, pattern: str) -> bool:
        """
        Synchronous check if a filename matches a glob pattern.
        """
        return fnmatch.fnmatch(filename, pattern)

    async def grep_search(
        self,
        query: str,
        case_sensitive: bool = False,
        include_pattern: str = None,
        exclude_pattern: str = None,
        explanation: str = None
    ) -> Dict[str, Any]:
        """
        Fast text-based regex search that finds exact pattern matches within files or directories.
        Best for finding specific strings or patterns.
        """
        results = []
        flags = 0 if case_sensitive else re.IGNORECASE

        # Note: A real implementation would ideally use `ripgrep` via a subprocess
        # for better performance and features.

        for root, _, files in os.walk(self.workspace_path):
            for file in files:
                file_path = os.path.join(root, file)
                relative_file_path = os.path.relpath(file_path, self.workspace_path)

                if include_pattern and not self._match_pattern_sync(file, include_pattern):
                    continue
                if exclude_pattern and self._match_pattern_sync(file, exclude_pattern):
                    continue

                try:
                    with open(file_path, "r", encoding="utf-8") as f:
                        for i, line in enumerate(f, 1):
                            if re.search(query, line, flags=flags):
                                results.append(
                                    {
                                        "file": relative_file_path,
                                        "line_number": i,
                                        "content": line.strip(),
                                    }
                                )
                                if len(results) >= 50: break

                except OSError as e:
                    print(f"[ERROR] Error reading file {file_path}: {e}")

                if len(results) >= 50: break

        return {
            "query": query, "case_sensitive": case_sensitive, "include_pattern": include_pattern,
            "exclude_pattern": exclude_pattern, "results": results, "total_matches": len(results),
            "capped": len(results) >= 50,
        }

    async def file_search(self, query: str, explanation: str = None) -> Dict[str, Any]:
        """
        Fast file search based on fuzzy matching against file path.
        """
        results = []

        for root, _, files in os.walk(self.workspace_path):
            for file in files:
                if query.lower() in file.lower():
                    file_path = os.path.join(root, file)
                    results.append({"file_path": os.path.relpath(file_path, self.workspace_path), "filename": file})

                    if len(results) >= 10: break

            if len(results) >= 10: break

        return {
            "query": query, "results": results, "total_matches": len(results),
            "capped": len(results) >= 10,
        }


    async def delete_file(self, target_file: str, explanation: str = None) -> Dict[str, Any]:
        """
        Deletes a file at the specified path relative to the workspace root.
        """
        file_path = os.path.join(self.workspace_path, target_file)
        absolute_file_path = os.path.abspath(file_path)

        if not absolute_file_path.startswith(os.path.abspath(self.workspace_path)):
             error_msg = f"Attempted to delete file outside workspace: {target_file}"
             print(f"[ERROR] {error_msg}")
             return {"success": False, "error": error_msg}

        if not os.path.exists(absolute_file_path):
            error_msg = f"File does not exist: {target_file}"
            print(f"[ERROR] {error_msg}")
            return {"success": False, "error": error_msg}

        if not os.path.isfile(absolute_file_path):
            error_msg = f"Path is not a file: {target_file}"
            print(f"[ERROR] {error_msg}")
            return {"success": False, "error": error_msg}

        try:
            os.remove(absolute_file_path)
            return {"success": True, "message": f"File deleted: {target_file}"}
        except OSError as e:
            error_msg = f"Failed to delete file {target_file}: {str(e)}"
            print(f"[ERROR] {error_msg}")
            return {"success": False, "error": error_msg}


    async def edit_file(self, target_file: str, instructions: str, code_edit: str, explanation: str) -> Dict[str, Any]:
        """
        Edit a file at the specified path (relative to workspace root) or CREATE A NEW ONE.
        Provide instructions and the FULL DESIRED CONTENT in `code_edit`.
        When editing existing files, use `// ... existing code ...` (or the appropriate comment style for the language) to represent unchanged lines.
        When creating a NEW file, provide the FULL content for that file in `code_edit`.
        """
        file_path = os.path.join(self.workspace_path, target_file)
        absolute_file_path = os.path.abspath(file_path)
        absolute_workspace_path = os.path.abspath(self.workspace_path)

        if not absolute_file_path.startswith(absolute_workspace_path):
             error_msg = f"Attempted to edit/create file outside workspace: {target_file}"
             print(f"[ERROR] {error_msg}")
             return {"success": False, "error": error_msg}

        self.last_edit_file = target_file
        self.last_edit_content = code_edit

        try:
            os.makedirs(os.path.dirname(absolute_file_path), exist_ok=True)
            # Note: This simplistic implementation overwrites the file.
            # Implementing the patch logic based on "// ... existing code ..." is complex.
            with open(absolute_file_path, "w", encoding="utf-8") as f:
                f.write(code_edit)

            return {"success": True, "message": f"File edited/created: {target_file}"}
        except OSError as e:
            error_msg = f"Failed to edit/create file {target_file}: {str(e)}"
            print(f"[ERROR] {error_msg}")
            return {"success": False, "error": error_msg}

    async def reapply(self, target_file: str, explanation: str = None) -> Dict[str, Any]:
        """
        Reapplies the last edit to the specified file.
        """
        if self.last_edit_file != target_file or self.last_edit_content is None:
            error_msg = "No previous edit found for this file or edit content is missing."
            print(f"[WARNING] {error_msg}")
            return {
                "success": False,
                "error": error_msg,
            }

        return await self.edit_file(target_file, "Reapplying the last edit.", self.last_edit_content, "Reapplying the previous edit due to unexpected results.")


    async def _execute_tool_call(self, tool_call):
        """
        Executes a tool call based on the provided information from ollama.chat response.
        Handles custom object structure from ollama-python, maps arguments, and redirects known invented tool names.
        """
        func_name = None
        arguments_dict = {}
        tool_call_id = "N/A"

        # Try accessing as attributes first (likely for ollama-python custom objects like Message.ToolCall)
        if hasattr(tool_call, 'function') and hasattr(tool_call.function, 'name') and hasattr(tool_call.function, 'arguments'):
             func = tool_call.function
             func_name = func.name
             arguments_payload = func.arguments
             tool_call_id = getattr(tool_call, 'id', 'N/A')

             if isinstance(arguments_payload, str):
                 try:
                      arguments_dict = json.loads(arguments_payload)
                 except json.JSONDecodeError:
                      print(f"[ERROR] Failed to parse arguments JSON string for tool {func_name} (Call ID: {tool_call_id}). Payload: {arguments_payload}")
                      # If JSON parsing fails, try treating the whole string as a single 'code_edit' arg if redirecting to edit_file?
                      # Or just return error. Let's return error for now to be safe.
                      return f"[ERROR] Failed to parse tool call arguments for tool {func_name}: {arguments_payload}"
             elif isinstance(arguments_payload, dict):
                 arguments_dict = arguments_payload
             else:
                  print(f"[WARNING] Unexpected type for arguments payload ({type(arguments_payload)}) from tool call {tool_call_id}. Payload: {arguments_payload}")


        # Fallback: Try accessing as dictionary keys (less likely for ollama-python ToolCall)
        elif isinstance(tool_call, dict) and "function" in tool_call:
             func = tool_call["function"]
             if isinstance(func, dict):
                 func_name = func.get("name")
                 arguments_payload = func.get("arguments", "{}")
                 tool_call_id = tool_call.get("id", "N/A")

                 if isinstance(arguments_payload, str):
                      try:
                           arguments_dict = json.loads(arguments_payload)
                      except json.JSONDecodeError:
                           print(f"[ERROR] Failed to parse arguments JSON string from dict-like tool call {func_name} (Call ID: {tool_call_id}). Payload: {arguments_payload}")
                           return f"[ERROR] Failed to parse tool call arguments for tool {func_name}: {arguments_payload}"
                 elif isinstance(arguments_payload, dict):
                      arguments_dict = arguments_payload
                 else:
                       print(f"[WARNING] Unexpected type for arguments payload ({type(arguments_payload)}) from dict-like tool call {tool_call_id}. Payload: {arguments_payload}")


        # If neither format matched or name/arguments weren't found
        if not func_name or not isinstance(arguments_dict, dict):
             print(f"[ERROR] Received tool_call does not match expected format or is missing name/arguments dict after parsing. Type: {type(tool_call)}. Raw: {tool_call}")
             return f"[ERROR] Received tool call in unexpected format or missing details."


        # --- Tool Name Redirection and Argument Mapping ---
        redirect_mapping = {
            'open': 'edit_file',
            'touch': 'edit_file',
            'create_file': 'edit_file',
            'generate_html_file': 'edit_file',
            'create_html_file': 'edit_file',
        }

        actual_func_name = func_name
        redirected_arguments = {}

        if func_name in redirect_mapping:
             actual_func_name = redirect_mapping[func_name]
             print(f"[INFO] Redirecting tool call '{func_name}' to '{actual_func_name}' (Call ID: {tool_call_id}).")

             # --- Attempt to map arguments from the invented tool's schema to edit_file's schema ---
             # This mapping is heuristic and based on common patterns of file manipulation args
             mapped_args_for_redirect = {}

             # Check for common filename/path keys
             target_file_val = arguments_dict.get('path', arguments_dict.get('filename', arguments_dict.get('target_file')))
             if target_file_val:
                 # Basic path sanitization and workspace check for redirected calls
                 abs_workspace = os.path.abspath(self.workspace_path)
                 provided_path = str(target_file_val) # Ensure it's a string
                 # Join with workspace first to handle relative input like 'file.txt' gracefully
                 abs_provided_path = os.path.abspath(os.path.join(self.workspace_path, provided_path))

                 if abs_provided_path.startswith(abs_workspace):
                      # Convert to relative if path is within workspace
                      mapped_args_for_redirect['target_file'] = os.path.relpath(abs_provided_path, abs_workspace)
                      print(f"[INFO] Mapped path argument '{provided_path}' to relative 'target_file': {mapped_args_for_redirect['target_file']}")
                 else:
                      # Path outside workspace
                      print(f"[ERROR] Redirected call: Provided path '{provided_path}' is outside workspace. Cannot execute.")
                      return f"[ERROR] Cannot execute redirected tool call: Provided path '{provided_path}' is outside the allowed workspace."
             else:
                  # No path/filename found in arguments for redirected call
                  print(f"[ERROR] Redirected call to '{actual_func_name}' missing required filename/path argument after mapping. Provided args for invented tool: {arguments_dict}")
                  return f"[ERROR] Redirected call to '{actual_func_name}' missing required filename/path argument."


             # Check for common content keys
             code_edit_val = arguments_dict.get('content', arguments_dict.get('text', arguments_dict.get('code_edit')))
             if code_edit_val is not None: # Allow empty string content
                  mapped_args_for_redirect['code_edit'] = str(code_edit_val) # Ensure it's a string
                  print(f"[INFO] Mapped content argument to 'code_edit'.")
             else:
                  print(f"[WARNING] Redirected call to '{actual_func_name}' missing content argument. Defaulting to empty content. Provided args for invented tool: {arguments_dict}")
                  mapped_args_for_redirect['code_edit'] = ""


             # Provide placeholders for instructions and explanation if not present in original args
             mapped_args_for_redirect['instructions'] = arguments_dict.get('instructions', arguments_dict.get('instruction', f"Redirected call from invented tool '{func_name}'."))
             mapped_args_for_redirect['explanation'] = arguments_dict.get('explanation', f"Executed via redirection from invented tool '{func_name}'.")

             redirected_arguments = mapped_args_for_redirect
             # print(f"[INFO] Final arguments for redirected call to '{actual_func_name}': {redirected_arguments}") # Keep detailed args for debugging


        # --- No redirection, use the original arguments extracted ---
        else:
             redirected_arguments = arguments_dict
             # print(f"[INFO] No redirection for tool '{func_name}' (Call ID: {tool_call_id}). Using provided arguments directly: {redirected_arguments}") # Keep detailed args for debugging


        # --- Execute the actual function ---
        if actual_func_name in self.available_functions:
            function_to_call = self.available_functions[actual_func_name]
            # print(f"[INFO] Calling function '{actual_func_name}' (Call ID: {tool_call_id}) with args: {redirected_arguments}") # Keep args for debugging
            try:
                 if asyncio.iscoroutinefunction(function_to_call):
                      response = await function_to_call(**redirected_arguments)
                 else:
                      print(f"[WARNING] Calling non-async function {actual_func_name} synchronously (Call ID: {tool_call_id}).")
                      response = function_to_call(**redirected_arguments)

                 if isinstance(response, (dict, list)):
                      response_str = json.dumps(response)
                      # print(f"[INFO] Converted tool response to JSON string for tool {actual_func_name} (Call ID: {tool_call_id}).") # Keep if needed
                      return response_str
                 elif not isinstance(response, (str, int, float, bool, type(None))):
                     response_str = str(response)
                     # print(f"[INFO] Converted non-basic tool response type ({type(response)}) to string for tool {actual_func_name} (Call ID: {tool_call_id}).") # Keep if needed
                     return response_str

                 return response

            except TypeError as e:
                 print(f"[ERROR] Argument mismatch when calling function '{actual_func_name}' (Call ID: {tool_call_id}): {e}. Attempted args: {redirected_arguments}. Original provided args (if redirected): {arguments_dict}")
                 return f"[ERROR] Argument mismatch for tool '{actual_func_name}': {e}. Attempted args: {redirected_arguments}"
            except Exception as e:
                error_message = f"[ERROR] Error executing tool '{actual_func_name}' (Call ID: {tool_call_id}): {e}"
                print(error_message)
                return f"[ERROR] Failed to execute tool '{actual_func_name}': {str(e)}"
        else:
            # This block handles cases where the *actual* func name is not found
            error_message = (
                f"[ERROR] Actual tool '{actual_func_name}' (redirected from '{func_name}' or original) not found in available functions (Call ID: {tool_call_id})."
            )
            print(error_message)
            return error_message

    async def chat(self, text: str) -> Dict[str, Any]:
        """
        Responds to the user's message, handling potential tool calls and multi-turn interactions.
        """
        print(f"\n>>> You: {text}")
        # No "Apollo thinking..." print here, the response will appear when ready.

        self.chat_history.append({"role": "user", "content": text})

        try:
            while True:
                llm_response = ollama.chat(
                    model="llama3.1",
                    messages=self.chat_history,
                    tools=self.get_available_tools(), # Always provide the list of *actual* tools
                    stream=False
                )

                # Access 'message' key first defensively
                message = llm_response.get("message")
                if not message:
                     print("[WARNING] LLM response missing 'message' field.")
                     # Add something to history to prevent potential loops with empty messages
                     self.chat_history.append({"role": "assistant", "content": "[Error: Empty message received from LLM]"})
                     return {"response": "Received an empty message from the model."}

                # --- Access tool_calls and content from the message object/dict ---
                # Use .get() for dictionaries and getattr() for objects defensively
                tool_calls = None
                content = None

                if isinstance(message, dict):
                     tool_calls = message.get("tool_calls")
                     content = message.get("content")
                else: # Assume object with attributes like ollama._types.Message
                     tool_calls = getattr(message, "tool_calls", None)
                     content = getattr(message, "content", None)


                if tool_calls:
                    # Ensure tool_calls is a list before iterating
                    if not isinstance(tool_calls, list):
                        print(f"[ERROR] Received non-list 'tool_calls' from LLM Message. Type: {type(tool_calls)}. Value: {tool_calls}")
                        self.chat_history.append({"role": "assistant", "content": f"[Error: Received non-list tool_calls: {tool_calls}]"})
                        return {"error": f"Received unexpected tool_calls format from LLM: {tool_calls}"}


                    # print(f"[INFO] LLM requested tool calls: {len(tool_calls)}") # Keep this log if helpful, removed for 'dumb comments'
                    self.chat_history.append(message)

                    tool_outputs = []
                    for tool_call in tool_calls:
                        # _execute_tool_call is now robust to the object/dict format, maps args, and redirects names
                        tool_result = await self._execute_tool_call(tool_call)

                        tool_outputs.append({
                            "role": "tool",
                            # Get tool_call_id safely from the object/dict
                            "tool_call_id": getattr(tool_call, 'id', tool_call.get('id', 'N/A')),
                            "content": str(tool_result) # Convert result to string for tool output
                        })
                        # print(f"[INFO] Tool execution result for call {getattr(tool_call, 'id', tool_call.get('id', 'N/A'))} added to history.") # Keep if helpful

                    self.chat_history.extend(tool_outputs)

                    continue # Go back to the start of the while loop

                elif content is not None:
                    # print(f"[INFO] LLM responded with content.") # Keep if helpful
                    self.chat_history.append(message)
                    return {"response": content}

                else:
                     # LLM response had neither tool_calls nor content.
                     print("[WARNING] LLM response had neither tool_calls nor content.")
                     self.chat_history.append(message)
                     return {"response": "Completed processing, but received no final message content."}

        except RuntimeError as e:
            error_message = f"[ERROR] RuntimeError during chat processing: {e}"
            print(error_message)
            return {"error": error_message}
        except Exception as e:
             error_message = f"[ERROR] An unexpected error occurred during chat processing: {e}"
             print(error_message)
             return {"error": error_message}


    @staticmethod
    def get_available_tools() -> List[Dict[str, Any]]:
        """Get all available tools in the Ollama tools format."""

        def create_parameters_dict(params_list):
            properties = {}
            required = []
            for param in params_list:
                param_name = param["name"]
                properties[param_name] = {
                    "type": param["type"],
                    "description": param["description"],
                }
                if param.get("required", False):
                     required.append(param_name)

            parameters_dict = {"properties": properties}
            if required:
                 parameters_dict["required"] = required

            return parameters_dict


        tools = [
            {
                "name": "codebase_search",
                "description": "Find snippets of code from the codebase most "
                "relevant to the search query. This is a semantic search tool. "
                "Reuse the user's exact query/most recent message with their wording unless there is a clear reason not to.",
                "parameters": create_parameters_dict([
                    {"name": "query", "type": "string", "description": "The search query.", "required": True},
                    {"name": "target_directories", "type": "array", "items": {"type": "string"}, "description": "Glob patterns for directories to search over."},
                    {"name": "explanation", "type": "string", "description": "One sentence explanation.", "required": True},
                ]),
            },
            {
                "name": "list_dir",
                "description": "List the contents of a directory, relative to the workspace root. Useful for exploring the file structure.",
                "parameters": create_parameters_dict([
                    {"name": "relative_workspace_path", "type": "string", "description": "Path to list contents of, relative to the workspace root.", "required": True},
                    {"name": "explanation", "type": "string", "description": "One sentence explanation.", "required": True},
                ]),
            },
            {
                "name": "grep_search",
                "description": "Fast text-based regex search that finds exact pattern matches within files or directories. Best for finding specific strings or patterns. Use include/exclude patterns to filter scope.",
                "parameters": create_parameters_dict([
                    {"name": "query", "type": "string", "description": "The regex pattern to search for.", "required": True},
                    {"name": "case_sensitive", "type": "boolean", "description": "Whether the search should be case sensitive."},
                    {"name": "include_pattern", "type": "string", "description": "Glob pattern for files to include (e.g. '*.ts')."},
                    {"name": "exclude_pattern", "type": "string", "description": "Glob pattern for files to exclude."},
                    {"name": "explanation", "type": "string", "description": "One sentence explanation.", "required": True},
                ]),
            },
            {
                "name": "file_search",
                "description": "Fast file search based on fuzzy matching against file path. Use if you know part of the file path.",
                "parameters": create_parameters_dict([
                    {"name": "query", "type": "string", "description": "Fuzzy filename to search for.", "required": True},
                    {"name": "explanation", "type": "string", "description": "One sentence explanation.", "required": True},
                ]),
            },
            {
                "name": "delete_file",
                "description": "Deletes a file at the specified path, relative to the workspace root.",
                "parameters": create_parameters_dict([
                    {"name": "target_file", "type": "string", "description": "The path of the file to delete, relative to the workspace root.", "required": True},
                    {"name": "explanation", "type": "string", "description": "One sentence explanation.", "required": True},
                ]),
            },
            {
                "name": "edit_file",
                "description": "Edit a file at the specified path (relative to workspace root) or CREATE A NEW ONE. This tool is used for creating ANY type of file (text, code, HTML, etc.). Provide instructions and the FULL DESIRED CONTENT in the `code_edit` parameter. For example, to create an HTML file, provide the full HTML content in `code_edit`. When editing existing files, use `// ... existing code ...` (or the appropriate comment style) to represent unchanged lines.",
                "parameters": create_parameters_dict([
                    {"name": "target_file", "type": "string", "description": "The path to the file to create or modify, relative to the workspace root (e.g., 'src/index.html').", "required": True},
                    {"name": "instructions", "type": "string", "description": "A single sentence instruction describing the edit/creation (e.g., 'Creating a new HTML file for the showroom')."},
                    {"name": "code_edit", "type": "string", "description": "The FULL code content for the file (for new files like HTML) or the edited sections with placeholders (for existing files).", "required": True},
                    {"name": "explanation", "type": "string", "description": "One sentence explanation.", "required": True},
                ]),
            },
             {
                "name": "reapply",
                "description": "Reapplies the last edit attempt to the specified file.",
                "parameters": create_parameters_dict([
                    {"name": "target_file", "type": "string", "description": "The relative path to the file.", "required": True},
                    {"name": "explanation", "type": "string", "description": "One sentence explanation.", "required": True},
                ]),
            },
            {
                "name": "chat",
                "description": "Engage in a normal conversational exchange with the user. Use when a specific tool is not required.",
                "parameters": create_parameters_dict([
                    {"name": "text", "type": "string", "description": "The user's message.", "required": True},
                ]),
            },
        ]
        return tools


    @staticmethod
    async def _fallback_response(message: str) -> str:
        """
        Generate a fallback response. (Not used in the main chat loop)
        """
        if any(g in message.lower() for g in ["hello", "hi", "hey"]):
            return "Hello! I'm Apollo, your AI assistant. How can I help you today?"
        if "what can you do" in message.lower() or "help" in message.lower():
            return "I can help with code tasks using tools like search, file listing, editing, and deleting."
        return "I'm here to assist with your coding tasks. What do you need help with?"

    @staticmethod
    async def chat_terminal():
        """
        Start Chat Session in the terminal.
        """
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
                print(f"\nAn unexpected error occurred during chat_terminal execution: {e}")


# Example usage
if __name__ == "__main__":
    asyncio.run(ApolloAgent.chat_terminal())