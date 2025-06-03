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
                "description": "Performs a semantic search for code snippets "
                "within the codebase that are most relevant"
                " to a natural language query. Ideal for finding code "
                "related to a concept or functionality "
                "when the exact syntax is unknown. For optimal results, use "
                "the user's original phrasing for the query.",
                "parameters": {
                    "type": "object",
                    "required": ["query"],
                    "properties": {
                        "query": {
                            "type": "string",
                            "description": "The natural language search query for semantic understanding.",
                        }
                    },
                },
            },
        },
        {
            "type": "function",
            "function": {
                "name": "list_dir",
                "description": "Lists all files and subdirectories within "
                "a specified directory path, "
                "relative to the workspace root. "
                "This is useful for exploring the project structure and discovering files.",
                "parameters": {
                    "type": "object",
                    "required": ["target_file"],
                    "properties": {
                        "target_file": {
                            "type": "string",
                            "description": "The path to the directory to be listed. Use '.' "
                            "to list the contents of the workspace root.",
                        },
                        "explanation": {
                            "type": "string",
                            "description": "A clear and concise explanation of why the contents of "
                            "this directory are being listed.",
                        },
                    },
                },
            },
        },
        {
            "type": "function",
            "function": {
                "name": "grep_search",
                "description": "Performs a fast, text-based search for an exact "
                "string or regular expression pattern within files. "
                "This is highly effective for locating specific function names, "
                "variable declarations, "
                "or log messages when the exact text is known.",
                "parameters": {
                    "type": "object",
                    "required": ["query", "explanation"],
                    "properties": {
                        "query": {
                            "type": "string",
                            "description": "The exact string or regular expression pattern to search for.",
                        },
                        "explanation": {
                            "type": "string",
                            "description": "A brief explanation of why this search is being performed or what is being looked for.",
                        },
                    },
                },
            },
        },
        {
            "type": "function",
            "function": {
                "name": "file_search",
                "description": "Finds files by performing a fuzzy search against their paths. This is useful when you "
                "know a part of the filename or path but are unsure of the exact location or spelling.",
                "parameters": {
                    "type": "object",
                    "required": ["query", "explanation"],
                    "properties": {
                        "query": {
                            "type": "string",
                            "description": "The partial or fuzzy filename to search for.",
                        },
                        "explanation": {
                            "type": "string",
                            "description": "A clear and concise explanation of why this file is being searched for.",
                        },
                    },
                },
            },
        },
        {
            "type": "function",
            "function": {
                "name": "delete_file",
                "description": "Permanently deletes a file from the workspace.",
                "parameters": {
                    "type": "object",
                    "required": ["target_file", "explanation"],
                    "properties": {
                        "target_file": {
                            "type": "string",
                            "description": "The exact path of the file to be deleted, "
                            "relative to the workspace root.",
                        },
                        "explanation": {
                            "type": "string",
                            "description": "A clear and concise explanation "
                            "of why this file is being deleted.",
                        },
                    },
                },
            },
        },
        {
            "type": "function",
            "function": {
                "name": "create_file",
                "description": "Creates a new file with a variety of granular operations. "
                "Always provide a clear explanation for the modification.",
                "parameters": {
                    "type": "object",
                    "required": ["target_file", "instructions", "explanation"],
                    "properties": {
                        "target_file": {
                            "type": "string",
                            "description": "The relative path to the file to be modified "
                            "or created (e.g., 'src/main.py', 'config.json').",
                        },
                        "instructions": {
                            "type": "object",
                            "description": "A JSON object specifying the editing operation. "
                            "Choose ONE of the following: ... "
                            "(Your detailed instructions are excellent here and remain unchanged)",
                        },
                        "explanation": {
                            "type": "string",
                            "description": "A clear and concise justification "
                            "for why this file modification is necessary.",
                        },
                    },
                },
            },
        },
        {
            "type": "function",
            "function": {
                "name": "edit_file",
                "description": "Modifies an existing one with a variety of granular operations. "
                "It is critical to first inspect the file's content "
                "to ensure the edit is appropriate. "
                "Always provide a clear explanation for the modification.",
                "parameters": {
                    "type": "object",
                    "required": ["target_file", "instructions", "explanation"],
                    "properties": {
                        "target_file": {
                            "type": "string",
                            "description": "The relative path to the file to be modified or "
                            "created (e.g., 'src/main.py', 'config.json').",
                        },
                        "instructions": {
                            "type": "object",
                            "description": "A JSON object specifying the editing operation. "
                            "Choose ONE of the following: ... "
                            "(Your detailed instructions are excellent "
                            "here and remain unchanged)",
                        },
                        "explanation": {
                            "type": "string",
                            "description": "A clear and concise justification "
                            "for why this file modification is necessary.",
                        },
                    },
                },
            },
        },
        {
            "type": "function",
            "function": {
                "name": "remove_dir",
                "description": "Recursively and permanently removes a directory and all of "
                "its contents. This action is irreversible.",
                "parameters": {
                    "type": "object",
                    "required": ["target_file", "explanation"],
                    "properties": {
                        "target_file": {
                            "type": "string",
                            "description": "The path of the directory to be removed, "
                            "relative to the workspace root.",
                        },
                        "explanation": {
                            "type": "string",
                            "description": "A clear and concise explanation of why this "
                            "directory is being removed.",
                        },
                    },
                },
            },
        },
        {
            "type": "function",
            "function": {
                "name": "web_search",
                "description": "Searches the web to find up-to-date information on a given topic."
                "This tool is best used for general knowledge, "
                "current events, or technical information "
                "not present in the local codebase or Wikipedia.",
                "parameters": {
                    "type": "object",
                    "required": ["query"],
                    "properties": {
                        "query": {
                            "type": "string",
                            "description": "The search query to be sent to the search engine.",
                        }
                    },
                },
                "returns": {},
            },
        },
        {
            "type": "function",
            "function": {
                "name": "wiki_search",
                "description": "Searches Wikipedia for encyclopedic "
                "information on a topic. This is best for historical events, "
                "scientific concepts, or detailed biographies.",
                "parameters": {
                    "type": "object",
                    "required": ["query"],
                    "properties": {
                        "query": {
                            "type": "string",
                            "description": "The topic to search for on Wikipedia.",
                        }
                    },
                },
            },
        },
    ]

    return tools
