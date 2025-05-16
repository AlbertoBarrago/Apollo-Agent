"""
File operations for the ApolloAgent.

This module contains functions for file operations like listing directories,
deleting files, editing files, and reapplying edits.

Author: Alberto Barrago
License: MIT - 2025
"""

import os
from typing import Dict, Any


async def list_dir(workspace_path: str, relative_workspace_path: str) -> Dict[str, Any]:
    """
    List the contents of a directory relative to the workspace root.

    Args:
        workspace_path: The root path of the workspace.
        relative_workspace_path: Path relative to the workspace root.

    Returns:
        Dictionary with directory contents information.
    """
    target_path = os.path.join(workspace_path, relative_workspace_path)
    absolute_target_path = os.path.abspath(target_path)

    if not absolute_target_path.startswith(os.path.abspath(workspace_path)):
        error_msg = (
            f"Attempted to list directory outside workspace: {relative_workspace_path}"
        )
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


async def delete_file(workspace_path: str, target_file: str) -> Dict[str, Any]:
    """
    Deletes a file at the specified path relative to the workspace root.

    Args:
        workspace_path: The root path of the workspace.
        target_file: The path to the file to delete, relative to the workspace root.

    Returns:
        Dictionary with success status and message or error.
    """
    file_path = os.path.join(workspace_path, target_file)
    absolute_file_path = os.path.abspath(file_path)

    if not absolute_file_path.startswith(os.path.abspath(workspace_path)):
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

async def edit_file(workspace_path: str, target_file: str, code_edit: str) -> Dict[str, Any]:
    """
    Edit or create a file at the specified path within the workspace.
    If `// ... existing code ...` is found in `code_edit`, it will be replaced with the file's original content.

    Args:
        workspace_path: Root of the workspace
        target_file: File to create or modify, relative to the workspace root
        code_edit: New content or template, possibly including a placeholder

    Returns:
        Dict with success or error details.
    """
    import os

    file_path = os.path.join(workspace_path, target_file)
    absolute_file_path = os.path.abspath(file_path)
    absolute_workspace_path = os.path.abspath(workspace_path)

    if not absolute_file_path.startswith(absolute_workspace_path):
        error_msg = f"Attempted to access outside workspace: {target_file}"
        print(f"[ERROR] {error_msg}")
        return {"success": False, "error": error_msg}

    try:
        os.makedirs(os.path.dirname(absolute_file_path), exist_ok=True)

        original = ""
        if os.path.exists(absolute_file_path):
            with open(absolute_file_path, "r", encoding="utf-8") as f:
                original = f.read()

        if "// ... existing code ..." in code_edit:
            merged = code_edit.replace("// ... existing code ...", original)
        else:
            merged = code_edit

        with open(absolute_file_path, "w", encoding="utf-8") as f:
            f.write(merged)

        return {"success": True, "message": f"File edited/created: {target_file}"}

    except OSError as e:
        error_msg = f"Failed to edit/create file {target_file}: {str(e)}"
        print(f"[ERROR] {error_msg}")
        return {"success": False, "error": error_msg}

async def reapply(agent, target_file: str) -> Dict[str, Any]:
    """
    Reapplies the last edit to the specified file.

    Args:
        agent: The ApolloAgent instance.
        target_file: The path to the file to reapply edits to, relative to the workspace root.

    Returns:
        Dictionary with success status and message or error.
    """
    if agent.last_edit_file != target_file or agent.last_edit_content is None:
        error_msg = "No previous edit found for this file or edit content is missing."
        print(f"[WARNING] {error_msg}")
        return {
            "success": False,
            "error": error_msg,
        }

    return await agent.edit_file(target_file, agent.last_edit_content)
