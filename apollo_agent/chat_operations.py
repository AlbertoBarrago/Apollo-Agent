"""
Chat interaction logic and tool function definitions for ApolloAgent.

This module defines the core `chat()` coroutine, which handles LLM interactions,
including tool calls using Ollama's function calling API. It also provides the
`get_available_tools()` function, which returns the tool definitions available
to the model, enabling functionality such as file editing, searching, and listing
workspace directories.

Author: Alberto Barrago
License: MIT - 2025
"""

import ollama
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

    agent.chat_history.append({"role": "user", "content": text})

    print("🤖 Give me a second, be patience and kind ", flush=True)

    try:
        while True:
            llm_response = ollama.chat(
                model="llama3.1",
                messages=agent.chat_history,
                tools=get_available_tools(),
                stream=False
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
                    tool_result = await agent.execute_tool(tool_call)

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
                        "query": {"type": "string", "description": "The search query."},
                        "target_directories": {
                            "type": "array",
                            "items": {"type": "string"},
                            "description": "Glob patterns for directories to search over.",
                        },
                        "explanation": {
                            "type": "string",
                            "description": "One sentence explanation.",
                        },
                    },
                },
            },
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
                            ),
                        },
                        "explanation": {
                            "type": "string",
                            "description": "One sentence explanation.",
                        },
                    },
                },
            },
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
                            "description": "The regex pattern to search for.",
                        },
                        "case_sensitive": {
                            "type": "boolean",
                            "description": "Whether the search should be case sensitive.",
                        },
                        "include_pattern": {
                            "type": "string",
                            "description": "Glob pattern for files to include (e.g. '*.ts').",
                        },
                        "exclude_pattern": {
                            "type": "string",
                            "description": "Glob pattern for files to exclude.",
                        },
                        "explanation": {
                            "type": "string",
                            "description": "One sentence explanation.",
                        },
                    },
                },
            },
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
                            "description": "Fuzzy filename to search for.",
                        },
                        "explanation": {
                            "type": "string",
                            "description": "One sentence explanation.",
                        },
                    },
                },
            },
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
                            ),
                        },
                        "explanation": {
                            "type": "string",
                            "description": "One sentence explanation.",
                        },
                    },
                },
            },
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
                    "in `code_edit`."
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
                            ),
                        },
                        "instructions": {
                            "type": "string",
                            "description": (
                                "A single sentence instruction describing the edit/creation "
                                "(e.g., 'Creating a new HTML file for the showroom')."
                            ),
                        },
                        "code_edit": {
                            "type": "string",
                            "description": ("""When making code changes, NEVER output code to the USER, unless requested. 
                                    Instead, use one of the code edit tools to implement the change.
                                    Use the code edit tools at most once per turn.
                                    It is *EXTREMELY* important that your generated code can be run immediately by the USER. To ensure this, follow these instructions carefully:
                                    1. Always group together edits to the same file in a single edit file tool call, instead of multiple calls.
                                    2. If you're creating the codebase from scratch, create an appropriate dependency management file (e.g., requirements.txt) with package versions and a helpful README.
                                    3. If you're building a web app from scratch, give it a beautiful and modern UI, imbued with the best UX practices.
                                    4. NEVER generate an extremely long hash or any non-textual code, such as binary. These are not helpful to the USER and are very expensive.
                                    5. Unless you are appending some small easy-to-apply edit to a file or creating a new file, you MUST read the contents or section of what you're editing before editing it.
                                    6. If you've introduced (linter) errors, fix them if clear how to (or you can easy figure out how to). Do not make uneducated guesses. 
                                    And DO NOT loop more than 3 times on fixing linter errors on the same file. On the third time, you should stop and ask the user what to do next.
                                    7. If you've suggested a reasonable code_edit that wasn't followed by the applied model, you should try reapplying the edit.
                                """
                            ),
                        },
                        "explanation": {
                            "type": "string",
                            "description": "One sentence explanation.",
                        },
                    },
                },
            },
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
                            "description": "The relative path to the file.",
                        },
                        "explanation": {
                            "type": "string",
                            "description": "One sentence explanation.",
                        },
                    },
                },
            },
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
                        "text": {"type": "string", "description": "The user's message."}
                    },
                },
            },
        },
    ]

    return tools
