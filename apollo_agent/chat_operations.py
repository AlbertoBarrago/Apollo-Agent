"""
Chat operations for the ApolloAgent.

This module contains functions for chat operations like chat, execute_tool_call,
fallback_response, and get_available_tools.

Author: Alberto Barrago
License: MIT - 2025
"""

import json
import os
import ollama
import asyncio
from typing import List, Dict, Any


async def chat(agent, text: str) -> None | dict[str, str] | dict[str, Any | None]:
    """
    Responds to the user's message, handling potential tool calls and multi-turn interactions.

    Args:
        agent: The ApolloAgent instance.
        text: The user's message.

    Returns:
        Response from the chat model or error information.
    """
    print(f"\n>>> You: {text}")
    # No "Apollo thinking..." print here, the response will appear when ready.

    agent.chat_history.append({"role": "user", "content": text})

    try:
        while True:
            llm_response = ollama.chat(
                model="llama3.1",
                messages=agent.chat_history,
                tools=get_available_tools(),  # Always provide the list of *actual* tools
                stream=False,
            )

            # Access 'message' key first defensively
            message = llm_response.get("message")
            if not message:
                print("[WARNING] LLM response missing 'message' field.")
                # Add something to history to prevent potential loops with empty messages
                agent.chat_history.append(
                    {
                        "role": "assistant",
                        "content": "[Error: Empty message received from LLM]",
                    }
                )
                return {"response": "Received an empty message from the model."}

            # --- Access tool_calls and content from the message object/dict ---
            # Use .get() for dictionaries and getattr() for objects defensively
            tool_calls = None
            content = None

            if isinstance(message, dict):
                tool_calls = message.get("tool_calls")
                content = message.get("content")
            else:  # Assume object with attributes like ollama._types.Message
                tool_calls = getattr(message, "tool_calls", None)
                content = getattr(message, "content", None)

            if tool_calls:
                # Ensure tool_calls is a list before iterating
                if not isinstance(tool_calls, list):
                    print(
                        f"[ERROR] Received non-list 'tool_calls' from LLM Message. Type: {type(tool_calls)}. Value: {tool_calls}"
                    )
                    agent.chat_history.append(
                        {
                            "role": "assistant",
                            "content": f"[Error: Received non-list tool_calls: {tool_calls}]",
                        }
                    )
                    return {
                        "error": f"Received unexpected tool_calls format from LLM: {tool_calls}"
                    }

                # print(f"[INFO] LLM requested tool calls: {len(tool_calls)}") # Keep this log if helpful, removed for 'dumb comments'
                agent.chat_history.append(message)

                tool_outputs = []
                for tool_call in tool_calls:
                    # _execute_tool_call is now robust to the object/dict format, maps args, and redirects names
                    tool_result = await _execute_tool_call(agent, tool_call)

                    tool_outputs.append(
                        {
                            "role": "tool",
                            "tool_call_id": getattr(
                                tool_call, "id", tool_call.get("id", "N/A")
                            ),
                            "content": str(tool_result),
                        }
                    )
                    # print(f"[INFO] Tool execution result for call {getattr(tool_call, 'id', tool_call.get('id', 'N/A'))} added to history.") # Keep if helpful

                agent.chat_history.extend(tool_outputs)

                continue

            elif content is not None:
                # print(f"[INFO] LLM responded with content.") # Keep if helpful
                agent.chat_history.append(message)
                return {"response": content}

            else:
                # LLM response had neither tool_calls nor content.
                print("[WARNING] LLM response had neither tool_calls nor content.")
                agent.chat_history.append(message)
                return {
                    "response": "Completed processing, but received no final message content."
                }

    except RuntimeError as e:
        error_message = f"[ERROR] RuntimeError during chat processing: {e}"
        print(error_message)
        return {"error": error_message}
    except SystemError as e:
        error_message = (
            f"[ERROR] An unexpected error occurred during chat processing: {e}"
        )
        print(error_message)
        return {"error": error_message}


async def _execute_tool_call(self, tool_call):
    """
    Executes a tool call based on the provided information from ollama.chat response.
    Handles custom object structure from ollama-python, maps arguments, and redirects known invented tool names.
    """
    func_name = None
    arguments_dict = {}
    tool_call_id = "N/A"

    # Try accessing as attributes first (likely for ollama-python custom objects like Message.ToolCall)
    if (
            hasattr(tool_call, "function")
            and hasattr(tool_call.function, "name")
            and hasattr(tool_call.function, "arguments")
    ):
        func = tool_call.function
        func_name = func.name
        arguments_payload = func.arguments
        tool_call_id = getattr(tool_call, "id", "N/A")

        if isinstance(arguments_payload, str):
            try:
                arguments_dict = json.loads(arguments_payload)
            except json.JSONDecodeError:
                print(
                    f"[ERROR] Failed to parse arguments JSON string for tool {func_name} (Call ID: {tool_call_id}). Payload: {arguments_payload}"
                )
                # If JSON parsing fails, try treating the whole string as a single 'code_edit' arg if redirecting to edit_file?
                # Or just return error. Let's return error for now to be safe.
                return f"[ERROR] Failed to parse tool call arguments for tool {func_name}: {arguments_payload}"
        elif isinstance(arguments_payload, dict):
            arguments_dict = arguments_payload
        else:
            print(
                f"[WARNING] Unexpected type for arguments payload ({type(arguments_payload)}) "
                f"from tool call {tool_call_id}. Payload: {arguments_payload}"
            )

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
                    print(
                        f"[ERROR] Failed to parse arguments JSON string from dict-like tool call {func_name} (Call ID: {tool_call_id}). Payload: {arguments_payload}"
                    )
                    return f"[ERROR] Failed to parse tool call arguments for tool {func_name}: {arguments_payload}"
            elif isinstance(arguments_payload, dict):
                arguments_dict = arguments_payload
            else:
                print(
                    f"[WARNING] Unexpected type for arguments payload ({type(arguments_payload)}) from dict-like tool call {tool_call_id}. Payload: {arguments_payload}"
                )

    # If neither format matched or name/arguments weren't found
    if not func_name or not isinstance(arguments_dict, dict):
        print(
            f"[ERROR] Received tool_call does not match expected format or is "
            f"missing name/arguments dict after parsing. Type: {type(tool_call)}. Raw: {tool_call}"
        )
        return (
            "[ERROR] Received tool call in unexpected format or missing details."
        )

    # --- Tool Name Redirection and Argument Mapping ---
    redirect_mapping = {
        "open": "edit_file",
        "touch": "edit_file",
        "edit": "edit_file",
        "create_file": "edit_file",
        "generate_html_file": "edit_file",
        "create_html_file": "edit_file",
    }

    actual_func_name = func_name

    if func_name in redirect_mapping:
        actual_func_name = redirect_mapping[func_name]
        print(
            f"[INFO] Redirecting tool call '{func_name}' to "
            f"'{actual_func_name}' (Call ID: {tool_call_id})."
        )

        # --- Attempt to map arguments from the invented tool's schema to edit_file's schema ---
        # This mapping is heuristic and based on common patterns of file manipulation args
        mapped_args_for_redirect = {}

        # Check for common filename/path keys
        target_file_val = arguments_dict.get(
            "path",
            arguments_dict.get("filename", arguments_dict.get("target_file")),
        )
        if target_file_val:
            # Basic path sanitization and workspace check for redirected calls
            abs_workspace = os.path.abspath(self.workspace_path)
            provided_path = str(target_file_val)  # Ensure it's a string
            # Join with workspace first to handle relative input like 'file.txt' gracefully
            abs_provided_path = os.path.abspath(
                os.path.join(self.workspace_path, provided_path)
            )

            if abs_provided_path.startswith(abs_workspace):
                # Convert to relative if path is within workspace
                mapped_args_for_redirect["target_file"] = os.path.relpath(
                    abs_provided_path, abs_workspace
                )
                print(
                    f"[INFO] Mapped path argument '{provided_path}' to relative 'target_file': {mapped_args_for_redirect['target_file']}"
                )
            else:
                # Path outside workspace
                print(
                    f"[ERROR] Redirected call: Provided path '{provided_path}' is outside workspace. Cannot execute."
                )
                return f"[ERROR] Cannot execute redirected tool call: Provided path '{provided_path}' is outside the allowed workspace."
        else:
            # No path/filename found in arguments for a redirected call
            print(
                f"[ERROR] Redirected call to '{actual_func_name}' missing required filename/path argument after mapping. Provided args for invented tool: {arguments_dict}"
            )
            return f"[ERROR] Redirected call to '{actual_func_name}' missing required filename/path argument."

        # Check for common content keys
        code_edit_val = arguments_dict.get(
            "content", arguments_dict.get("text", arguments_dict.get("code_edit"))
        )
        if code_edit_val is not None:  # Allow empty string content
            mapped_args_for_redirect["code_edit"] = str(
                code_edit_val
            )  # Ensure it's a string
            print("[INFO] Mapped content argument to 'code_edit'.")
        else:
            print(
                f"[WARNING] Redirected call to '{actual_func_name}' missing content argument. "
                f"Defaulting to empty content. Provided args for invented tool: {arguments_dict}"
            )
            mapped_args_for_redirect["code_edit"] = ""

        # Provide placeholders for instructions and explanation if not present in original args
        mapped_args_for_redirect["instructions"] = arguments_dict.get(
            "instructions",
            arguments_dict.get(
                "instruction", f"Redirected call from invented tool '{func_name}'."
            ),
        )
        mapped_args_for_redirect["explanation"] = arguments_dict.get(
            "explanation",
            f"Executed via redirection from invented tool '{func_name}'.",
        )

        redirected_arguments = mapped_args_for_redirect
        # print(f"[INFO] Final arguments for a redirected call to '{actual_func_name}': {redirected_arguments}") # Keep detailed args for debugging

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
                print(
                    f"[WARNING] Calling non-async function {actual_func_name} synchronously (Call ID: {tool_call_id})."
                )
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
            print(
                f"[ERROR] Argument mismatch when calling function '{actual_func_name}' (Call ID: {tool_call_id}): {e}. Attempted args: {redirected_arguments}. Original provided args (if redirected): {arguments_dict}"
            )
            return f"[ERROR] Argument mismatch for tool '{actual_func_name}': {e}. Attempted args: {redirected_arguments}"
        except Exception as e:
            error_message = f"[ERROR] Error executing tool '{actual_func_name}' (Call ID: {tool_call_id}): {e}"
            print(error_message)
            return f"[ERROR] Failed to execute tool '{actual_func_name}': {str(e)}"
    else:
        # This block handles cases where the *actual* func name is not found
        error_message = f"[ERROR] Actual tool '{actual_func_name}' (redirected from '{func_name}' or original) not found in available functions (Call ID: {tool_call_id})."
        print(error_message)
        return error_message


def get_available_tools() -> List[Dict[str, Any]]:
    """
    Get all available tools in the Ollama tools format.

    Returns:
        List of tool definitions.
    """
    tools = [
        {
            "type": "function",
            "function": {
                "name": "codebase_search",
                "description": (
                    "Find snippets of code from the codebase most relevant to the search query. "
                    "This is a semantic search tool. Reuse the user's exact query/most recent "
                    "message with their wording unless there is a clear reason not to."
                ),
                "parameters": {
                    "type": "object",
                    "required": ["query", "explanation"],
                    "properties": {
                        "query": {
                            "type": "string",
                            "description": "The search query."
                        },
                        "target_directories": {
                            "type": "array",
                            "items": {"type": "string"},
                            "description": "Glob patterns for directories to search over."
                        },
                        "explanation": {
                            "type": "string",
                            "description": "One sentence explanation."
                        }
                    }
                }
            }
        },
        {
            "type": "function",
            "function": {
                "name": "list_dir",
                "description": (
                    "List the contents of a directory, relative to the workspace root. "
                    "Useful for exploring the file structure."
                ),
                "parameters": {
                    "type": "object",
                    "required": ["relative_workspace_path", "explanation"],
                    "properties": {
                        "relative_workspace_path": {
                            "type": "string",
                            "description": (
                                "Path to list contents of, relative to the workspace root."
                            )
                        },
                        "explanation": {
                            "type": "string",
                            "description": "One sentence explanation."
                        }
                    }
                }
            }
        },
        {
            "type": "function",
            "function": {
                "name": "grep_search",
                "description": (
                    "Fast text-based regex search that finds exact pattern matches within files "
                    "or directories. Best for finding specific strings or patterns. Use "
                    "include/exclude patterns to filter scope."
                ),
                "parameters": {
                    "type": "object",
                    "required": ["query", "explanation"],
                    "properties": {
                        "query": {
                            "type": "string",
                            "description": "The regex pattern to search for."
                        },
                        "case_sensitive": {
                            "type": "boolean",
                            "description": "Whether the search should be case sensitive."
                        },
                        "include_pattern": {
                            "type": "string",
                            "description": "Glob pattern for files to include (e.g. '*.ts')."
                        },
                        "exclude_pattern": {
                            "type": "string",
                            "description": "Glob pattern for files to exclude."
                        },
                        "explanation": {
                            "type": "string",
                            "description": "One sentence explanation."
                        }
                    }
                }
            }
        },
        {
            "type": "function",
            "function": {
                "name": "file_search",
                "description": (
                    "Fast file search based on fuzzy matching against file path. "
                    "Use if you know part of the file path."
                ),
                "parameters": {
                    "type": "object",
                    "required": ["query", "explanation"],
                    "properties": {
                        "query": {
                            "type": "string",
                            "description": "Fuzzy filename to search for."
                        },
                        "explanation": {
                            "type": "string",
                            "description": "One sentence explanation."
                        }
                    }
                }
            }
        },
        {
            "type": "function",
            "function": {
                "name": "delete_file",
                "description": (
                    "Deletes a file at the specified path, relative to the workspace root."
                ),
                "parameters": {
                    "type": "object",
                    "required": ["target_file", "explanation"],
                    "properties": {
                        "target_file": {
                            "type": "string",
                            "description": (
                                "The path of the file to delete, relative to the workspace root."
                            )
                        },
                        "explanation": {
                            "type": "string",
                            "description": "One sentence explanation."
                        }
                    }
                }
            }
        },
        {
            "type": "function",
            "function": {
                "name": "edit_file",
                "description": (
                    "Edit a file at the specified path (relative to workspace root) or CREATE A "
                    "NEW ONE. This tool is used for creating ANY type of file (text, code, HTML, "
                    "etc.). Provide instructions and the FULL DESIRED CONTENT in the `code_edit` "
                    "parameter. For example, to create an HTML file, provide the full HTML content "
                    "in `code_edit`. When editing existing files, use `// ... existing code ...` "
                    "(or the appropriate comment style) to represent unchanged lines."
                ),
                "parameters": {
                    "type": "object",
                    "required": ["target_file", "code_edit", "explanation"],
                    "properties": {
                        "target_file": {
                            "type": "string",
                            "description": (
                                "The path to the file to create or modify, relative to the "
                                "workspace root (e.g., 'src/index.html')."
                            )
                        },
                        "instructions": {
                            "type": "string",
                            "description": (
                                "A single sentence instruction describing the edit/creation "
                                "(e.g., 'Creating a new HTML file for the showroom')."
                            )
                        },
                        "code_edit": {
                            "type": "string",
                            "description": (
                                "The FULL code content for the file (for new files like HTML) or "
                                "the edited sections with placeholders (for existing files)."
                            )
                        },
                        "explanation": {
                            "type": "string",
                            "description": "One sentence explanation."
                        }
                    }
                }
            }
        },
        {
            "type": "function",
            "function": {
                "name": "reapply",
                "description": "Reapplies the last edit attempt to the specified file.",
                "parameters": {
                    "type": "object",
                    "required": ["target_file", "explanation"],
                    "properties": {
                        "target_file": {
                            "type": "string",
                            "description": "The relative path to the file."
                        },
                        "explanation": {
                            "type": "string",
                            "description": "One sentence explanation."
                        }
                    }
                }
            }
        },
        {
            "type": "function",
            "function": {
                "name": "chat",
                "description": (
                    "Engage in a normal conversational exchange with the user. "
                    "Use when a specific tool is not required."
                ),
                "parameters": {
                    "type": "object",
                    "required": ["text"],
                    "properties": {
                        "text": {
                            "type": "string",
                            "description": "The user's message."
                        }
                    }
                }
            }
        }
    ]

    return tools
