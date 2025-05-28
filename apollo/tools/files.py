"""
File operations for the ApolloAgent.

This module contains functions for file operations like listing directories,
deleting files, editing files, and reapplying edits.

Author: Alberto Barrago
License: BSD 3-Clause License - 2025
"""

import json
import mimetypes
import os
import re
from typing import Dict, Any
from bs4 import BeautifulSoup


async def list_dir(agent, target_file: str, explanation: str = None) -> Dict[str, Any]:
    """
    List the contents of a directory relative to the workspace root.

    Args:
        agent: Apollo instance class.
        target_file: Path relative to the workspace root.
        explanation: Optional explanation of why you're listing this directory.


    Returns:
        Dictionary with directory contents information.
    """

    target_path = os.path.join(agent.workspace_path, target_file)
    absolute_target_path = os.path.abspath(target_path)

    if not absolute_target_path.startswith(os.path.abspath(agent.workspace_path)):
        error_msg = f"Attempted to list directory outside workspace: {target_file}"
        print(f"[ERROR] {error_msg}")
        return {"error": error_msg}

    if not os.path.exists(absolute_target_path):
        error_msg = f"Path does not exist: {target_file}"
        print(f"[ERROR] {error_msg}")
        return {"error": error_msg}

    if not os.path.isdir(absolute_target_path):
        error_msg = f"Path is not a directory: {target_file}"
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
        "path": target_file,
        "explanation": explanation,
        "directories": directories,
        "files": files,
    }


async def remove_dir(agent, target_file: str) -> Dict[str, Any]:
    """
    Remove dir from the workspace when a user asks for it
    :param agent:
    :param target_file:
    :return:
    """
    target_path = os.path.join(agent.workspace_path, target_file)
    absolute_target_path = os.path.abspath(target_path)
    if not absolute_target_path.startswith(os.path.abspath(agent.workspace_path)):
        error_msg = f"Attempted to remove directory outside workspace: {target_file}"
        print(f"[ERROR] {error_msg}")
        return {"error": error_msg}
    if not os.path.exists(absolute_target_path):
        error_msg = f"Path does not exist: {target_file}"
        print(f"[ERROR] {error_msg}")
        return {"error": error_msg}
    if not os.path.isdir(absolute_target_path):
        error_msg = f"Path is not a directory: {target_file}"
        print(f"[ERROR] {error_msg}")
        return {"error": error_msg}
    try:
        os.rmdir(absolute_target_path)
        return {"success": True, "message": f"Directory removed: {target_file}"}
    except OSError as e:
        error_msg = f"Failed to remove directory {target_file}: {str(e)}"
        print(f"[ERROR] {error_msg}")
        return {"success": False, "error": error_msg}


async def delete_file(agent, target_file: str) -> Dict[str, Any]:
    """
    Deletes a file at the specified path relative to the workspace root.

    Args:
        agent: The ApolloAgent instance.
        target_file: The path to the file to delete, relative to the workspace root.

    Returns:
        Dictionary with success status and message or error.
    """
    file_path = os.path.join(agent.workspace_path, target_file)
    absolute_file_path = os.path.abspath(file_path)

    if not absolute_file_path.startswith(os.path.abspath(agent.workspace_path)):
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


async def edit_file_or_create(
    agent, target_file: str, instructions: Dict[str, Any], explanation: str
) -> Dict[str, Any]:
    """
    Edits a file at the specified path based on detailed instructions.
    This function supports various operations like inserting content, replacing lines,
    or modifying structured data (HTML, JSON). It's designed to be robust and
    handle different file types intelligently.

    Args:
        agent: The agent object (must have a `workspace_path` attribute).
        target_file: The relative path to the file to create or modify
                     (e.g., 'index.html', 'main.py', 'style.css').
        instructions: A dictionary defining the editing operations. This
                      allows for granular control over file modifications.
                      Examples:
                      - To append content: {"operation": "append", "content": "New line\n"}
                      - To insert at a specific line: {"operation": "insert_line", "line_number": 5, "content": "import sys\n"}
                      - To replace content matching a regex: {"operation": "replace_regex", "regex": "old_pattern", "new_content": "new_pattern"}
                      - To insert HTML into body: {"operation": "insert_html_body", "html_content": "<div>New HTML</div>"}
                      - To update a JSON field: {"operation": "update_json_field", "path": "$.settings.debug", "value": true}
                      - To replace an entire file: {"operation": "replace_file_content", "content": "Full new file content"}
                      See tool description for full instruction types.
        explanation: A concise justification for the action being taken.

    Returns:
        A dictionary indicating success or failure, with a message or error.
        :param agent:
        :param target_file:
        :param instructions:
        :param explanation:
    """

    if not target_file:
        return {"success": False, "error": "Missing target file"}

    target_file = os.path.normpath(target_file).lstrip(os.sep)
    file_path = os.path.join(agent.workspace_path, target_file)
    absolute_workspace_path = os.path.abspath(agent.workspace_path)

    if not file_path.startswith(absolute_workspace_path):
        return {"success": False, "error": "Unsafe file path outside of workspace"}

    directory = os.path.dirname(file_path)
    if directory and not os.path.exists(directory) and os.path.sep in target_file:
        try:
            os.makedirs(directory, exist_ok=True)
            print(
                f"[INFO] Created directory: {os.path.relpath(directory, absolute_workspace_path)}"
            )
        except OSError as e:
            return {"success": False, "error": f"Failed to create directory: {e}"}

    try:
        original_content = ""
        file_exists = os.path.exists(file_path)
        if file_exists:
            with open(file_path, "r", encoding="utf-8") as f:
                original_content = f.read()

        edited_content = original_content
        operation = instructions.get("operation")

        if operation is None:
            return {"success": False, "error": "Missing 'operation' in instructions."}

        # --- File Type Detection (more robust) ---
        mime_type, _ = mimetypes.guess_type(file_path)
        is_html = target_file.lower().endswith(".html") or (
            mime_type and "html" in mime_type
        )
        is_json = target_file.lower().endswith(".json") or (
            mime_type and "json" in mime_type
        )
        # --- Dispatch based on Operation and File Type ---
        if operation == "replace_file_content":
            # This operation effectively overwrites the entire file.
            edited_content = instructions.get("content", "")
            if edited_content is None:  # Allow empty content to a clear file
                edited_content = ""

        elif operation == "append":
            content_to_add = instructions.get("content", "")
            edited_content = original_content + content_to_add

        elif operation == "prepend":
            content_to_add = instructions.get("content", "")
            edited_content = content_to_add + original_content

        elif operation == "insert_line":
            line_number = instructions.get("line_number")
            content_to_insert = instructions.get("content", "")
            if line_number is None:
                return {
                    "success": False,
                    "error": "Missing 'line_number' for 'insert_line' operation.",
                }
            lines = original_content.splitlines(keepends=True)
            # Adjust for 1-based indexing and handle out-of-bounds
            insert_idx = max(0, min(line_number - 1, len(lines)))
            lines.insert(
                insert_idx,
                (
                    content_to_insert + "\n"
                    if not content_to_insert.endswith("\n")
                    else content_to_insert
                ),
            )
            edited_content = "".join(lines)

        elif operation == "replace_line":
            line_number = instructions.get("line_number")
            new_content = instructions.get("content", "")
            if line_number is None:
                return {
                    "success": False,
                    "error": "Missing 'line_number' for 'replace_line' operation.",
                }
            lines = original_content.splitlines(keepends=True)
            # Adjust for 1-based indexing and handle out-of-bounds
            if 0 <= line_number - 1 < len(lines):
                lines[line_number - 1] = (
                    new_content + "\n"
                    if not new_content.endswith("\n")
                    else new_content
                )
                edited_content = "".join(lines)
            else:
                return {
                    "success": False,
                    "error": f"Line number {line_number} out of bounds for 'replace_line'.",
                }

        elif operation == "delete_line":
            line_number = instructions.get("line_number")
            if line_number is None:
                return {
                    "success": False,
                    "error": "Missing 'line_number' for 'delete_line' operation.",
                }
            lines = original_content.splitlines(keepends=True)
            if 0 <= line_number - 1 < len(lines):
                del lines[line_number - 1]
                edited_content = "".join(lines)
            else:
                return {
                    "success": False,
                    "error": f"Line number {line_number} out of bounds for 'delete_line'.",
                }

        elif operation == "replace_regex":
            regex_pattern = instructions.get("regex")
            new_content = instructions.get("new_content", "")
            count = instructions.get("count", 0)  # 0 for all occurrences
            if regex_pattern is None:
                return {
                    "success": False,
                    "error": "Missing 'regex' for 'replace_regex' operation.",
                }
            try:
                edited_content = re.sub(
                    regex_pattern, new_content, original_content, count=count
                )
            except re.error as e:
                return {
                    "success": False,
                    "error": f"Invalid regex pattern: {e}, {edited_content}",
                }

        elif operation == "insert_html_body" and is_html:
            html_to_insert = instructions.get("html_content", "")
            if not original_content.strip():
                edited_content = f"<html><body>{html_to_insert}</body></html>"
            else:
                soup_original = BeautifulSoup(original_content, "html.parser")
                soup_new = BeautifulSoup(html_to_insert, "html.parser")
                body_orig = soup_original.find("body")
                if not body_orig:
                    # If no body in original, try to create one
                    new_body = soup_original.new_tag("body")
                    if soup_original.html:
                        soup_original.html.append(new_body)
                    else:  # Fallback if even an HTML tag is missing
                        soup_original.append(new_body)
                    body_orig = new_body

                for el in soup_new.contents:
                    body_orig.append(el)
                edited_content = str(soup_original)

        elif operation == "update_json_field" and is_json:
            path_str = instructions.get(
                "path"
            )  # e.g., "settings.api_key" or "data[0].name"
            value = instructions.get("value")
            if path_str is None:
                return {
                    "success": False,
                    "error": "Missing 'path' for 'update_json_field' operation.",
                }

            try:
                data = json.loads(original_content) if original_content.strip() else {}
                # Simple path parser (can be expanded for more complex JSONPath)
                parts = path_str.split(".")
                current = data
                for i, part in enumerate(parts):
                    if i == len(parts) - 1:
                        current[part] = value
                    else:
                        if part not in current or not isinstance(current[part], dict):
                            current[part] = {}
                        current = current[part]
                json.dumps(data, indent=2)
            except json.JSONDecodeError:
                return {"success": False, "error": "Invalid JSON content."}
            except TypeError as e:
                return {"success": False, "error": f"JSON path error: {e}"}

        else:
            return {
                "success": False,
                "error": f"Unsupported operation '{operation}' or file type for {target_file}.",
            }

        with open(file_path, "w", encoding="utf-8") as f:
            f.write(edited_content)

        action_word = "Updated" if file_exists else "Created"
        return {
            "success": True,
            "message": f"File {action_word}: "
                       f"{target_file} with operation '"
                       f"{operation}'. Explanation: {explanation}",
        }

    except RuntimeError as e:
        return {"success": False, "error": f"An unexpected error occurred: {e}"}
