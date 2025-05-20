"""
In this file is present the entire list of tools that we are processing in the chat.

Author: Alberto Barrago
License: BSD 3-Clause License - 2025
"""

from typing import List, Dict, Any


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
                    "Create or edit a file at the specified path, relative to the workspace root. "
                    "Used for code, text, config, or markup files. To modify a file, it is highly "
                    "recommended to first read it using other tools like grep_search or list_dir. "
                    "You must supply the full desired contents of the file in `code_edit`."
                ),
                "parameters": {
                    "type": "object",
                    "required": ["target_file", "code_edit", "explanation"],
                    "properties": {
                        "target_file": {
                            "type": "string",
                            "description": "Relative path to the file to create or modify (e.g., 'src/index.html').",
                        },
                        "instructions": {
                            "type": "string",
                            "description": (
                                "Brief explanation of the intent "
                                "(e.g., 'Add missing import for React'). "
                                "Should be a single sentence."
                            ),
                        },
                        "code_edit": {
                            "type": "string",
                            "description": (
                                "Full new content of the file. "
                                "If modifying an existing file, include the "
                                "entire revised content. Do not generate diffs or partial patches. "
                                "Ensure the resulting code is immediately runnable or buildable."
                            ),
                        },
                        "read_first": {
                            "type": "boolean",
                            "description": (
                                "Set to true if the file should be read or "
                                "validated with grep or list_dir "
                                "before editing. Recommended for non-trivial edits."
                            ),
                            "default": "false",
                        },
                        "explanation": {
                            "type": "string",
                            "description": "A concise justification for the action being taken.",
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
