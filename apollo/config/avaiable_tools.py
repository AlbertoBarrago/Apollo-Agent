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
                "description": "Lists all files and directories in a specified path relative "
                "to the workspace root. "
                "Returns structured information about the directory contents "
                "including separate lists for files and subdirectories.",
                "parameters": {
                    "type": "object",
                    "required": ["target_file"],
                    "properties": {
                        "target_file": {
                            "type": "string",
                            "description": "Path to the directory you want to list, relative "
                            'to the workspace root. Use empty string or "." '
                            "to list the workspace root directory.",
                        },
                        "explanation": {
                            "type": "string",
                            "description": "Optional explanation of why you're "
                            "listing this directory. Not required "
                            "for function execution.",
                        },
                    },
                },
                "returns": {
                    "type": "object",
                    "properties": {
                        "path": {
                            "type": "string",
                            "description": "The path that was listed",
                        },
                        "directories": {
                            "type": "array",
                            "description": "List of subdirectories in the specified path",
                        },
                        "files": {
                            "type": "array",
                            "description": "List of files in the specified path",
                        },
                        "error": {
                            "type": "string",
                            "description": "Error message if the operation failed",
                        },
                    },
                },
            },
        },
        {
            "type": "function",
            "function": {
                "name": "web_search",
                "description": "Search the web for information about a topic. "
                "IMPORTANT use this tool if user ask info about something",
                "parameters": {
                    "type": "object",
                    "required": ["search_query"],
                    "properties": {
                        "search_query": {
                            "type": "string",
                            "description": "The content send by the user",
                        }
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
                "name": "edit_file_or_create",
                "description": (
                    "Modifies a file at the specified path within the workspace based on granular instructions. "
                    "This tool is highly versatile for editing code, text, configuration, or markup files. "
                    "It allows for specific operations like appending content, inserting/replacing lines, "
                    "using regular expressions for replacements, or modifying structured data like HTML or JSON. "
                    "Before using this tool, it is strongly recommended to first read the file's content "
                    "using `grep_search` or `list_dir` to understand its current state and structure. "
                    "You MUST always provide 'target_file', 'instructions', and 'explanation' parameters."
                    "IMPORTANT if 'target_file' does not exist, it will be created."
                ),
                "parameters": {
                    "type": "object",
                    "required": ["target_file", "instructions", "explanation"],
                    "properties": {
                        "target_file": {
                            "type": "string",
                            "description": "The relative path to the file to modify (e.g., 'src/main.py', 'config.json', 'index.html').",
                        },
                        "instructions": {
                            "type": "object",
                            "description": (
                                "A JSON object specifying the editing operation and its parameters. "
                                "Choose ONE operation based on your goal:\n"
                                '- **To replace the entire file content:** `{"operation": "replace_file_content", "content": "FULL NEW CONTENT STRING"}`\n'
                                "  (Use this only when a complete overhaul is needed, ensuring you provide the *entire* desired file content).\n"
                                '- **To append content to the end of the file:** `{"operation": "append", "content": "STRING TO ADD"}`\n'
                                '- **To prepend content to the beginning of the file:** `{"operation": "prepend", "content": "STRING TO ADD"}`\n'
                                '- **To insert a line at a specific position (1-based index):** `{"operation": "insert_line", "line_number": <INTEGER>, "content": "STRING TO INSERT\\n"}`\n'
                                "  (Remember to include `\\n` if you want a newline).\n"
                                '- **To replace a specific line (1-based index):** `{"operation": "replace_line", "line_number": <INTEGER>, "content": "NEW STRING FOR THAT LINE\\n"}`\n'
                                '- **To delete a specific line (1-based index):** `{"operation": "delete_line", "line_number": <INTEGER>}`\n'
                                '- **To replace text matching a regular expression:** `{"operation": "replace_regex", "regex": "YOUR_REGEX_PATTERN", "new_content": "REPLACEMENT_STRING", "count": <INTEGER>}`\n'
                                "  (`count`: 0 for all occurrences, 1 for first, etc. Default is 0).\n"
                                '- **To insert HTML content into the `<body>` of an HTML file:** `{"operation": "insert_html_body", "html_content": "<p>New paragraph</p>"}`\n'
                                '- **To update a specific field in a JSON file:** `{"operation": "update_json_field", "path": "field.subfield.array[0].key", "value": ANY_JSON_COMPATIBLE_VALUE}`\n'
                                "  (Use dot notation for objects and `[index]` for arrays. The `value` can be a string, number, boolean, array, or object).\n"
                            ),
                        },
                        "explanation": {
                            "type": "string",
                            "description": "A concise, single-sentence justification "
                            "for the action being taken, explaining *why* this edit is necessary.",
                        },
                    },
                },
            },
        },
        {
            "type": "function",
            "function": {
                "name": "remove_dir",
                "description": "Removes a directory at the specified path, "
                "relative to the workspace root.",
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
                "name": "chat",
                "description": (
                    "Engage in a normal conversational exchange with the user. "
                    "Use when a specific tool is not required. "
                    "ALWAYS remember that you are Apollo a nerd code assistant. "
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
        {
            "type": "function",
            "function": {
                "name": "wiki_search",
                "description": "Search the Wikipedia for information about a topic. "
                "IMPORTANT use this tool if user ask info about something",
                "parameters": {
                    "type": "object",
                    "required": ["search_query"],
                    "properties": {
                        "search_query": {
                            "type": "string",
                            "description": "The content send by the user",
                        }
                    },
                },
            },
        },
    ]

    return tools
