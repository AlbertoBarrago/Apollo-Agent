"""
Chat operations for the ApolloAgent.

This module contains functions for chat operations like chat, execute_tool_call,
fallback_response, and get_available_tools.

Author: Alberto Barrago
License: MIT - 2025
"""
import ollama
from typing import List, Dict, Any
import inspect


async def chat(agent, text: str) -> None | dict[str, str] | dict[str, Any | None]:
    """
    Responds to the user's message, handling potential tool calls and multi-turn interactions.

    Args:
        agent: The ApolloAgent instance.
        text: The user's message.

    Returns:
        Response from the chat model or error information.
    """
    print("""                          
       # #   #####   ####  #      #       ####                # #    ####  ###### #    # ##### 
      #   #  #    # #    # #      #      #    #              #   #  #    # #      ##   #   #   
     #     # #    # #    # #      #      #    #    #####    #     # #      #####  # #  #   #   
     ####### #####  #    # #      #      #    #             ####### #  ### #      #  # #   #   
     #     # #      #    # #      #      #    #             #     # #    # #      #   ##   #   
     #     # #       ####  ###### ######  ####              #     #  ####  ###### #    #   #""")
    print(f"\n>>> You: {text}")

    agent.chat_history.append({"role": "user", "content": text})

    print("\n>>> Assistant: ", end="🤔 Thinking... ", flush=True)

    try:
        while True:
            llm_response = ollama.chat(
                model="llama3.1",
                messages=agent.chat_history,
                tools=get_available_tools(),
                stream=False,
            )

            message = llm_response.get("message")
            if not message:
                print("[WARNING] LLM response missing 'message' field.")
                agent.chat_history.append(
                    {
                        "role": "assistant",
                        "content": "[Error: Empty message received from LLM]",
                    }
                )
                return {"response": "Received an empty message from the model."}

            if isinstance(message, dict):
                tool_calls = message.get("tool_calls")
                content = message.get("content")
            else:
                tool_calls = getattr(message, "tool_calls", None)
                content = getattr(message, "content", None)

            if tool_calls:
                if not isinstance(tool_calls, list):
                    print(
                        f"[ERROR] Received non-list 'tool_calls' from LLM Message. "
                        f"Type: {type(tool_calls)}. Value: {tool_calls}"
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

                agent.chat_history.append(message)

                tool_outputs = []
                for tool_call in tool_calls:
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
                agent.chat_history.extend(tool_outputs)

            elif content is not None:
                agent.chat_history.append(message)
                return {"response": content}

            else:
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
    Execute a tool function call (from LLM) with validated arguments and secure redirection.
    """

    def filter_valid_args(valid_func, args_dict):
        valid_params = valid_func.__code__.co_varnames[:valid_func.__code__.co_argcount]
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
            arguments_dict = __import__('json').loads(raw_args)
        elif isinstance(raw_args, dict):
            arguments_dict = raw_args
        else:
            return f"[ERROR] Unsupported arguments type: {type(raw_args)}"
    except Exception as e:
        return f"[ERROR] Failed to parse tool call: {e}"

    redirect_mapping = {
        "open": "edit_file",
        "touch": "edit_file",
        "edit": "edit_file",
        "create_file": "edit_file",
        "generate_html_file": "edit_file",
        "create_html_file": "edit_file",
    }
    redirected_name = redirect_mapping.get(func_name, func_name)

    if redirected_name == "edit_file":
        file_key = (
                arguments_dict.get("path") or
                arguments_dict.get("filename") or
                arguments_dict.get("target_file")
        )
        if not file_key:
            return "[ERROR] Missing file path for 'edit_file' operation."

        abs_workspace = __import__('os').path.abspath(self.workspace_path)
        abs_target_path = __import__('os').path.abspath(__import__('os').path.join(self.workspace_path, file_key))

        if not abs_target_path.startswith(abs_workspace):
            return f"[ERROR] Unsafe path: '{file_key}' is outside workspace."

        arguments_dict = {
            "target_file": __import__('os').path.relpath(abs_target_path, abs_workspace),
            "code_edit": arguments_dict.get("content") or arguments_dict.get("text") or arguments_dict.get("code_edit",
                                                                                                           ""),
            "instructions": arguments_dict.get("instructions") or arguments_dict.get("instruction", "")
        }

    if redirected_name not in self.available_functions:
        return f"[ERROR] Tool '{redirected_name}' is not available."

    func = self.available_functions[redirected_name]

    filtered_args = filter_valid_args(func, arguments_dict)

    print(f"Executing... {filtered_args}")

    try:
        if getattr(func, "__call__") and getattr(func, "__code__", None):
            if inspect.iscoroutinefunction(func):
                result = await func(**filtered_args)
            else:
                result = func(**filtered_args)
        else:
            return "[ERROR] Function is not callable."

        if isinstance(result, (dict, list)):
            return __import__('json').dumps(result)
        return str(result)
    except TypeError as e:
        return f"[ERROR] Argument mismatch in '{redirected_name}': {e}"
    except Exception as e:
        return f"[ERROR] Exception during execution of '{redirected_name}': {e}"


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
