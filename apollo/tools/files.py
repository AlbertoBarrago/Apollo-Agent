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


async def create_file(
    agent, target_file: str, instructions: Dict[str, Any], explanation: str
) -> Dict[str, Any]:
    """
    Create a new file with the specified content
    :param agent:
    :param target_file:
    :param instructions:
    :param explanation:
    :return:
    """
    if not target_file:
        return {"success": False, "error": "Missing target file"}

    # Normalize the target file path and ensure it's relative
    target_file = os.path.normpath(target_file).lstrip(os.sep)

    # Get the workspace path from the agent (which could be ToolExecutor or ApolloAgent)
    workspace_path = getattr(agent, "workspace_path", os.getcwd())
    absolute_workspace_path = os.path.abspath(workspace_path)

    # Construct the full file path
    file_path = os.path.abspath(os.path.join(absolute_workspace_path, target_file))

    print(f"[INFO] Creating file: {target_file}")
    print(f"[INFO] Instructions: {instructions}")
    print(f"[INFO] Explanation: {explanation}")
    print(f"[INFO] Absolute workspace path: {absolute_workspace_path}")
    print(f"[INFO] Full file path: {file_path}")

    # Ensure the file path is within the workspace
    if not file_path.startswith(absolute_workspace_path):
        return {"success": False, "error": "Unsafe file path outside of workspace"}

    # Get the content from instructions
    content = instructions.get("content", "")

    # Actually write the file to disk
    try:
        with open(file_path, "w", encoding="utf-8") as f:
            f.write(content)

        file_exists = True
        print(f"[INFO] File created successfully: {target_file}")

        return {
            "success": True,
            "message": f"File created: {target_file}",
            "file_path": file_path,
            "file_exists": file_exists,
            "explanation": explanation,
        }
    except (OSError, IOError, RuntimeError) as e:
        error_msg = f"Failed to write file {target_file}: {str(e)}"
        print(f"[ERROR] {error_msg}")
        return {"success": False, "error": error_msg}
    except Exception as e:
        error_msg = f"Unexpected error creating file {target_file}: {str(e)}"
        print(f"[ERROR] {error_msg}")
        return {"success": False, "error": error_msg}


async def _apply_edit(
    target_file: str, original_content: str, instructions: Dict[str, Any]
) -> Tuple[str, Optional[str]]:
    """
    Apply edit operations on file content
    :param target_file: File path for context (used for mime type detection)
    :param original_content: Original content of the file
    :param instructions: Edit instructions
    :return: Tuple of (new_content, error_message)
    """
    operation = instructions.get("operation")
    if not operation:
        return original_content, "Missing 'operation' in instructions."

    mime_type, _ = mimetypes.guess_type(target_file)
    is_html = target_file.lower().endswith(".html") or (
        mime_type and "html" in mime_type
    )
    is_json = target_file.lower().endswith(".json") or (
        mime_type and "json" in mime_type
    )

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

    except (OSError, IOError, RuntimeError) as e:
        return original_content, f"Error applying edit: {str(e)}"
    except re.error as e:
        return original_content, f"Regex error: {str(e)}"
    except json.JSONDecodeError as e:
        return original_content, f"JSON parsing error: {str(e)}"
    except Exception as e:
        return original_content, f"Unexpected error applying edit: {str(e)}"

    return (
        original_content,
        f"Unsupported operation '{operation}' or invalid file type.",
    )


async def edit_file(
    agent, target_file: str, instructions: Dict[str, Any], explanation: str
) -> Dict[str, Any]:
    """
    Edit an existing file with the specified instructions
    :param agent: The agent instance (could be ToolExecutor or ApolloAgent)
    :param target_file: Path to the file to edit, relative to workspace
    :param instructions: Edit instructions
    :param explanation: Explanation for the edit
    :return: Dictionary with success/error information
    """
    if not target_file:
        return {"success": False, "error": "Missing target file"}

    # Normalize the target file path and ensure it's relative
    target_file = os.path.normpath(target_file).lstrip(os.sep)

    # Get the workspace path from the agent (which could be ToolExecutor or ApolloAgent)
    workspace_path = getattr(agent, "workspace_path", os.getcwd())
    absolute_workspace_path = os.path.abspath(workspace_path)

    # Construct the full file path
    file_path = os.path.abspath(os.path.join(absolute_workspace_path, target_file))

    # print(f"[INFO] Editing file: {target_file}")
    # print(f"[INFO] Instructions: {instructions}")
    # print(f"[INFO] Explanation: {explanation}")
    # print(f"[INFO] Absolute workspace path: {absolute_workspace_path}")
    # print(f"[INFO] Full file path: {file_path}")

    # Ensure the file path is within the workspace
    if not file_path.startswith(absolute_workspace_path):
        return {"success": False, "error": "Unsafe file path outside of workspace"}

    # Check if the file exists
    if not os.path.exists(file_path):
        return {"success": False, "error": f"File does not exist: {target_file}"}

    if not os.path.isfile(file_path):
        return {"success": False, "error": f"Path is not a file: {target_file}"}

    # Read the original content
    try:
        with open(file_path, "r", encoding="utf-8") as f:
            original_content = f.read()
    except (OSError, IOError) as e:
        error_msg = f"Failed to read file {target_file}: {str(e)}"
        print(f"[ERROR] {error_msg}")
        return {"success": False, "error": error_msg}
    except Exception as e:
        error_msg = f"Unexpected error reading file {target_file}: {str(e)}"
        print(f"[ERROR] {error_msg}")
        return {"success": False, "error": error_msg}

    try:
        new_content, error = await _apply_edit(
            target_file, original_content, instructions
        )
        if error:
            return {"success": False, "error": error}

        # Write the new content
        with open(file_path, "w", encoding="utf-8") as f:
            f.write(new_content)

        print(f"[INFO] File edited successfully: {target_file}")
        return {
            "success": True,
            "message": f"File edited: {target_file}",
            "file_path": file_path,
            "explanation": explanation,
        }
    except (OSError, IOError) as e:
        error_msg = f"Failed to write file {target_file}: {str(e)}"
        print(f"[ERROR] {error_msg}")
        return {"success": False, "error": error_msg}
    except Exception as e:
        error_msg = f"Unexpected error editing file {target_file}: {str(e)}"
        print(f"[ERROR] {error_msg}")
        return {"success": False, "error": error_msg}
