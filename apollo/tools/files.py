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
from typing import Dict, Any, Tuple, Optional
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

async def edit_file_or_create(agent, target_file: str, instructions: Dict[str, Any], explanation: str) -> Dict[str, Any]:
    """
    Edit or create a new File
    :param agent:
    :param target_file:
    :param instructions:
    :param explanation:
    :return:
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
            print(f"[INFO] Created directory: {os.path.relpath(directory, absolute_workspace_path)}")
        except OSError as e:
            return {"success": False, "error": f"Failed to create directory: {e}"}

    file_exists = os.path.exists(file_path)
    original_content = ""
    if file_exists:
        with open(file_path, "r", encoding="utf-8") as f:
            original_content = f.read()

    try:
        edited_content, error = apply_edit_operation(target_file, original_content, instructions)
        if error:
            return {"success": False, "error": error}

        with open(file_path, "w", encoding="utf-8") as f:
            f.write(edited_content)

        action_word = "Updated" if file_exists else "Created"
        return {
            "success": True,
            "message": f"File {action_word}: {target_file} with operation '{instructions.get('operation')}'. Explanation: {explanation}",
        }

    except RuntimeError as e:
        return {"success": False, "error": f"An unexpected error occurred: {e}"}

def apply_edit_operation(target_file: str, original_content: str, instructions: Dict[str, Any]) -> Tuple[str, Optional[str]]:
    """
    Apply edit operation to file
    :param target_file:
    :param original_content:
    :param instructions:
    :return:
    """
    operation = instructions.get("operation")
    if not operation:
        return original_content, "Missing 'operation' in instructions."

    mime_type, _ = mimetypes.guess_type(target_file)
    is_html = target_file.lower().endswith(".html") or (mime_type and "html" in mime_type)
    is_json = target_file.lower().endswith(".json") or (mime_type and "json" in mime_type)

    try:
        if operation == "replace_file_content":
            return instructions.get("content", "") or "", None

        if operation == "append":
            return original_content + instructions.get("content", ""), None

        if operation == "prepend":
            return instructions.get("content", "") + original_content, None

        if operation == "insert_line":
            line_number = instructions.get("line_number")
            if line_number is None:
                return original_content, "Missing 'line_number' for 'insert_line'."
            lines = original_content.splitlines(keepends=True)
            idx = max(0, min(line_number - 1, len(lines)))
            content = instructions.get("content", "")
            lines.insert(idx, content if content.endswith("\n") else content + "\n")
            return "".join(lines), None

        if operation == "replace_line":
            line_number = instructions.get("line_number")
            if line_number is None:
                return original_content, "Missing 'line_number' for 'replace_line'."
            lines = original_content.splitlines(keepends=True)
            if 0 <= line_number - 1 < len(lines):
                lines[line_number - 1] = instructions.get("content", "") + "\n"
                return "".join(lines), None
            return original_content, f"Line {line_number} out of bounds."

        if operation == "delete_line":
            line_number = instructions.get("line_number")
            if line_number is None:
                return original_content, "Missing 'line_number' for 'delete_line'."
            lines = original_content.splitlines(keepends=True)
            if 0 <= line_number - 1 < len(lines):
                del lines[line_number - 1]
                return "".join(lines), None
            return original_content, f"Line {line_number} out of bounds."

        if operation == "replace_regex":
            regex = instructions.get("regex")
            if regex is None:
                return original_content, "Missing 'regex' for 'replace_regex'."
            try:
                new_content = instructions.get("new_content", "")
                count = instructions.get("count", 0)
                return re.sub(regex, new_content, original_content, count=count), None
            except re.error as e:
                return original_content, f"Regex error: {e}"

        if operation == "insert_html_body" and is_html:
            html_content = instructions.get("html_content", "")
            if not original_content.strip():
                return f"<html><body>{html_content}</body></html>", None
            soup = BeautifulSoup(original_content, "html.parser")
            body = soup.find("body")
            if not body:
                body = soup.new_tag("body")
                (soup.html or soup).append(body)
            new_soup = BeautifulSoup(html_content, "html.parser")
            for el in new_soup.contents:
                body.append(el)
            return str(soup), None

        if operation == "update_json_field" and is_json:
            path_str = instructions.get("path")
            if path_str is None:
                return original_content, "Missing 'path' for 'update_json_field'."
            value = instructions.get("value")
            data = json.loads(original_content) if original_content.strip() else {}
            keys = path_str.split(".")
            current = data
            for i, key in enumerate(keys):
                if i == len(keys) - 1:
                    current[key] = value
                else:
                    current = current.setdefault(key, {})
            return json.dumps(data, indent=2), None

    except RuntimeError as e:
        return original_content, str(e)

    return original_content, f"Unsupported operation '{operation}' or invalid file type."
