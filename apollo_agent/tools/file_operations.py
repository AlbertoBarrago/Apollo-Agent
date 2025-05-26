"""
File operations for the ApolloAgent.

This module contains functions for file operations like listing directories,
deleting files, editing files, and reapplying edits.

Author: Alberto Barrago
License: BSD 3-Clause License - 2024
"""

import os
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

async def edit_file(agent, target_file: str, code_edit: str) -> Dict[str, Any]:
    """
    Edits an HTML file intelligently by merging new content into the <body>.
    Falls back to append or overwrite if a file is not HTML.
    """
    file_path = os.path.join(agent.workspace_path, target_file)
    absolute_file_path = os.path.abspath(file_path)
    absolute_workspace_path = os.path.abspath(agent.workspace_path)

    if not absolute_file_path.startswith(absolute_workspace_path):
        return {"success": False, "error": "Unsafe file path outside of workspace"}

    # print(f"The actual workspace is ${agent.workspace_path}")
    # print(f"Have right ACCESS to the folder ${os.access(absolute_workspace_path, os.W_OK)}")

    try:
        os.makedirs(os.path.dirname(absolute_file_path), exist_ok=True)

        original = ""
        if os.path.exists(absolute_file_path):
            with open(absolute_file_path, "r", encoding="utf-8") as f:
                original = f.read()

        # Simple check: is this an HTML file?
        is_html = target_file.lower().endswith(".html")

        if is_html and original.strip():
            soup_original = BeautifulSoup(original, "html.parser")
            soup_new = BeautifulSoup(code_edit, "html.parser")

            # Insert all body content from new into old <body>
            body_orig = soup_original.body
            body_new = soup_new.body

            if body_orig and body_new:
                for el in body_new.contents:
                    body_orig.append(el)
                merged = str(soup_original)
            else:
                # If <body> not found, just append raw content
                merged = original + "\n\n" + code_edit
        else:
            # Not HTML or no original content – append or create
            merged = original + "\n\n" + code_edit if original else code_edit

        with open(absolute_file_path, "w", encoding="utf-8") as f:
            f.write(merged)

        return {"success": True, "message": f"File updated: {target_file}"}

    except RuntimeError as e:
        return {"success": False, "error": str(e)}

async def reapply(agent, target_file: str) -> Dict[str, Any]:
    """
    Reapplies the last edit to the specified file.

    Args:
        agent: The ApolloAgent instance.
        target_file: The path to the file to reapply edit to, relative to the workspace root.

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

    return await edit_file(agent, target_file, agent.last_edit_content)
