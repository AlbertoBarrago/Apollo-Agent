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
import aiofiles


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

    # Security check: Ensure the path is within the workspace
    if not absolute_target_path.startswith(os.path.abspath(agent.workspace_path)):
        error_msg = f"Attempted to list directory outside workspace: {target_file} (resolved to {absolute_target_path})"
        print(f"[ERROR] {error_msg}")
        return {"error": error_msg}

    if not os.path.exists(absolute_target_path):
        error_msg = f"Path does not exist: {target_file} (resolved to {absolute_target_path})"
        print(f"[ERROR] {error_msg}")
        return {"error": error_msg}

    if not os.path.isdir(absolute_target_path):
        error_msg = f"Path is not a directory: {target_file} (resolved to {absolute_target_path})"
        print(f"[ERROR] {error_msg}")
        return {"error": error_msg}

    try:
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
    except OSError as e:
        error_msg = f"Error listing directory {target_file}: {str(e)}"
        print(f"[ERROR] {error_msg}")
        return {"error": error_msg}


async def remove_dir(agent, target_file: str, explanation: str = None) -> Dict[
    str, Any]:  # Added explanation to match schema
    """
    Remove dir from the workspace when a user asks for it
    :param agent:
    :param target_file:
    :param explanation: Optional explanation for the removal.
    :return:
    """
    target_path = os.path.join(agent.workspace_path, target_file)
    absolute_target_path = os.path.abspath(target_path)

    if not absolute_target_path.startswith(os.path.abspath(agent.workspace_path)):
        error_msg = f"Attempted to remove directory outside workspace: {target_file} (resolved to {absolute_target_path})"
        print(f"[ERROR] {error_msg}")
        return {"error": error_msg}
    if not os.path.exists(absolute_target_path):
        error_msg = f"Path does not exist: {target_file} (resolved to {absolute_target_path})"
        print(f"[ERROR] {error_msg}")
        return {"error": error_msg}
    if not os.path.isdir(absolute_target_path):
        error_msg = f"Path is not a directory: {target_file} (resolved to {absolute_target_path})"
        print(f"[ERROR] {error_msg}")
        return {"error": error_msg}
    try:
        os.rmdir(absolute_target_path)
        return {"success": True, "message": f"Directory removed: {target_file}", "explanation": explanation}
    except OSError as e:
        error_msg = f"Failed to remove directory {target_file}: {str(e)}"
        print(f"[ERROR] {error_msg}")
        return {"success": False, "error": error_msg}


async def delete_file(agent, target_file: str, explanation: str = None) -> Dict[str, Any]:  # Added explanation
    """
    Deletes a file at the specified path relative to the workspace root.

    Args:
        agent: The ApolloAgent instance.
        target_file: The path to the file to delete, relative to the workspace root.
        explanation: Optional explanation for the deletion.

    Returns:
        Dictionary with success status and message or error.
    """
    file_path = os.path.join(agent.workspace_path, target_file)
    absolute_file_path = os.path.abspath(file_path)

    if not absolute_file_path.startswith(os.path.abspath(agent.workspace_path)):
        error_msg = f"Attempted to delete file outside workspace: {target_file} (resolved to {absolute_file_path})"
        print(f"[ERROR] {error_msg}")
        return {"success": False, "error": error_msg}

    if not os.path.exists(absolute_file_path):
        error_msg = f"File does not exist: {target_file} (resolved to {absolute_file_path})"
        print(f"[ERROR] {error_msg}")
        return {"success": False, "error": error_msg}

    if not os.path.isfile(absolute_file_path):
        error_msg = f"Path is not a file: {target_file} (resolved to {absolute_file_path})"
        print(f"[ERROR] {error_msg}")
        return {"success": False, "error": error_msg}

    try:
        os.remove(absolute_file_path)
        return {"success": True, "message": f"File deleted: {target_file}", "explanation": explanation}
    except OSError as e:
        error_msg = f"Failed to delete file {target_file}: {str(e)}"
        print(f"[ERROR] {error_msg}")
        return {"success": False, "error": error_msg}


async def create_file(
        agent, target_file: str, instructions: Dict[str, Any], explanation: str
) -> Dict[str, Any]:
    """
    Create a new file with the specified content or apply other file operations.
    :param agent: The agent instance.
    :param target_file: The relative path to the file.
    :param instructions: A dictionary specifying the operation and content.
    :param explanation: Justification for the file modification.
    :return: Dictionary with success/error information.
    """
    if not target_file:
        return {"success": False, "error": "Missing target file"}

    target_file = os.path.normpath(target_file).lstrip(os.sep)
    workspace_path = getattr(agent, "workspace_path", os.getcwd())
    absolute_workspace_path = os.path.abspath(workspace_path)
    file_path = os.path.abspath(os.path.join(absolute_workspace_path, target_file))

    print(f"[INFO] Operation: create_file, Target: {target_file}")
    # print(f"[DEBUG] Raw instructions received: {instructions}") # For deeper debugging

    actual_instructions = instructions
    if isinstance(instructions, str):
        try:
            actual_instructions = json.loads(instructions)
        except json.JSONDecodeError:
            # If it's a string but not valid JSON, it's an error for the 'instructions' object.
            print(f"[ERROR] Instructions parameter is a string but not valid JSON: '{instructions}'")
            return {"success": False, "error": "Instructions parameter is a string but not valid JSON."}

    if not isinstance(actual_instructions, dict):
        print(f"[ERROR] Instructions parameter is not a dictionary after parsing: {type(actual_instructions)}")
        return {"success": False, "error": "Instructions parameter must be a JSON object (dictionary)."}

    # print(f"[DEBUG] Parsed instructions: {actual_instructions}") # For deeper debugging
    # print(f"[INFO] Explanation: {explanation}")
    # print(f"[INFO] Absolute workspace path: {absolute_workspace_path}")
    # print(f"[INFO] Full file path: {file_path}")

    if not file_path.startswith(absolute_workspace_path):
        error_msg = f"Unsafe file path outside of workspace: {target_file} (resolved to {file_path})"
        print(f"[ERROR] {error_msg}")
        return {"success": False, "error": error_msg}

    # Ensure parent directory exists
    parent_dir = os.path.dirname(file_path)
    if not os.path.exists(parent_dir):
        try:
            os.makedirs(parent_dir, exist_ok=True)
            print(f"[INFO] Created parent directory: {parent_dir}")
        except OSError as e:
            error_msg = f"Failed to create parent directory {parent_dir} for {target_file}: {str(e)}"
            print(f"[ERROR] {error_msg}")
            return {"success": False, "error": error_msg}
    elif not os.path.isdir(parent_dir):
        error_msg = f"Cannot create file; parent path {parent_dir} exists but is not a directory."
        print(f"[ERROR] {error_msg}")
        return {"success": False, "error": error_msg}

    # --- Handle different instructions based on your tool's capabilities ---
    # This example focuses on the 'content' key as per the original error.
    # You'll need to expand this logic for 'overwrite', 'append_content', 'insert_content_at_line' etc.

    file_exists = os.path.exists(file_path)
    overwrite = actual_instructions.get("overwrite", False)
    content_to_write = actual_instructions.get("content")  # Can be None if not provided

    # Default mode is 'w' (write/create/truncate)
    mode = "w"
    operation_description = "created/updated"

    if actual_instructions.get("append_content") is not None:
        content_to_write = actual_instructions.get("append_content")
        mode = "a"
        operation_description = "appended to"
    elif actual_instructions.get("insert_content_at_line") is not None:
        # This is more complex and requires reading, modifying, then writing.
        # For now, let's return an error if this is the only instruction and content is not primary.
        # You would implement the read-modify-write logic here.
        print(
            f"[WARNING] 'insert_content_at_line' not fully implemented in this simplified example, requires read-modify-write.")
        return {"success": False,
                "error": "'insert_content_at_line' requires more complex handling not shown in this fix."}

    if file_exists and not overwrite and mode == "w" and content_to_write is not None:
        # If trying to write new content (mode 'w') to an existing file without overwrite flag
        error_msg = f"File '{target_file}' already exists and overwrite is not permitted by current instructions."
        print(f"[ERROR] {error_msg}")
        return {"success": False, "error": error_msg}

    if content_to_write is None and mode == "w":  # If no content for 'w' mode, write empty string
        content_to_write = ""
    elif content_to_write is None and mode == "a":  # If no content for 'a' mode, it's a no-op or error
        print(f"[INFO] No content provided for append operation on file: {target_file}")
        return {"success": True, "message": f"File '{target_file}' touched (append with no content).",
                "explanation": explanation}

    try:
        async with aiofiles.open(file_path, mode, encoding="utf-8") as f:
            await f.write(str(content_to_write))  # Ensure content is string

        print(f"[INFO] File {operation_description} successfully: {target_file}")
        return {
            "success": True,
            "message": f"File '{target_file}' {operation_description} successfully.",
            "file_path": file_path,  # Return absolute path
            "explanation": explanation,
        }
    except (OSError, IOError) as e:
        error_msg = f"Failed to write to file {target_file}: {str(e)}"
        print(f"[ERROR] {error_msg}")
        return {"success": False, "error": error_msg}
    except Exception as e:
        error_msg = f"Unexpected error during file operation on {target_file}: {str(e)}"
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
    # Defensive parsing for instructions, similar to create_file
    actual_instructions = instructions
    if isinstance(instructions, str):
        try:
            actual_instructions = json.loads(instructions)
        except json.JSONDecodeError:
            return original_content, "Instructions parameter for _apply_edit is a string but not valid JSON."
    if not isinstance(actual_instructions, dict):
        return original_content, "Instructions parameter for _apply_edit must be a JSON object (dictionary)."

    operation = actual_instructions.get("operation")
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
            return actual_instructions.get("content", "") or "", None

        if operation == "append":
            return original_content + str(actual_instructions.get("content", "")), None  # Ensure content is string

        if operation == "prepend":
            return str(actual_instructions.get("content", "")) + original_content, None  # Ensure content is string

        if operation == "insert_line":
            line_number = actual_instructions.get("line_number")
            if not isinstance(line_number, int) or line_number <= 0:
                return original_content, "Invalid or missing 'line_number' (must be a positive integer) for 'insert_line'."
            lines = original_content.splitlines(keepends=True)
            idx = max(0, min(line_number - 1, len(lines)))  # 0-indexed
            content = str(actual_instructions.get("content", ""))  # Ensure content is string
            lines.insert(idx, content if content.endswith("\n") else content + "\n")
            return "".join(lines), None

        if operation == "replace_line":
            line_number = actual_instructions.get("line_number")
            if not isinstance(line_number, int) or line_number <= 0:
                return original_content, "Invalid or missing 'line_number' (must be a positive integer) for 'replace_line'."
            lines = original_content.splitlines(keepends=True)
            if 0 <= line_number - 1 < len(lines):  # 0-indexed
                lines[line_number - 1] = str(actual_instructions.get("content", "")) + "\n"  # Ensure content is string
                return "".join(lines), None
            return original_content, f"Line {line_number} out of bounds (1 to {len(lines)})."

        if operation == "delete_line":
            line_number = actual_instructions.get("line_number")
            if not isinstance(line_number, int) or line_number <= 0:
                return original_content, "Invalid or missing 'line_number' (must be a positive integer) for 'delete_line'."
            lines = original_content.splitlines(keepends=True)
            if 0 <= line_number - 1 < len(lines):  # 0-indexed
                del lines[line_number - 1]
                return "".join(lines), None
            return original_content, f"Line {line_number} out of bounds (1 to {len(lines)})."

        if operation == "replace_regex":
            regex = actual_instructions.get("regex")
            if regex is None:
                return original_content, "Missing 'regex' for 'replace_regex'."
            try:
                new_content_str = str(actual_instructions.get("new_content", ""))  # Ensure content is string
                count = actual_instructions.get("count", 0)
                if not isinstance(count, int): count = 0  # Default to 0 if invalid
                return re.sub(regex, new_content_str, original_content, count=count), None
            except re.error as e:
                return original_content, f"Regex error: {e}"

        if operation == "insert_html_body" and is_html:
            html_content_to_insert = str(actual_instructions.get("html_content", ""))  # Ensure content is string
            if not original_content.strip():  # If original is empty, create basic structure
                return f"<html><head><title>New Page</title></head><body>{html_content_to_insert}</body></html>", None

            soup = BeautifulSoup(original_content, "html.parser")
            body = soup.find("body")
            if not body:  # If no body tag, try to append to html or root
                body = soup.new_tag("body")
                if soup.html:
                    soup.html.append(body)
                else:  # No html tag, append to root
                    soup.append(body)

            new_elements_soup = BeautifulSoup(html_content_to_insert, "html.parser")
            for el in new_elements_soup.contents:  # Append children of the parsed new content
                body.append(el.extract() if el.name else el)  # el.extract() to move it
            return str(soup), None

        if operation == "update_json_field" and is_json:
            path_str = actual_instructions.get("path")
            if path_str is None or not isinstance(path_str, str) or not path_str.strip():
                return original_content, "Missing or invalid 'path' (must be a non-empty string) for 'update_json_field'."
            value_to_set = actual_instructions.get("value")  # Value can be any JSON-serializable type
            try:
                data = json.loads(original_content) if original_content.strip() else {}
            except json.JSONDecodeError:
                return original_content, "Original content is not valid JSON for 'update_json_field'."

            keys = path_str.split(".")
            current = data
            for i, key in enumerate(keys):
                if not key: return original_content, f"Invalid key (empty string) in path '{path_str}'."
                if i == len(keys) - 1:
                    current[key] = value_to_set
                else:
                    if not isinstance(current.get(key), dict):
                        current[key] = {}  # Create intermediate dicts if they don't exist or are not dicts
                    current = current[key]
            return json.dumps(data, indent=2), None

    except json.JSONDecodeError as e:  # Catch if original_content for JSON op is bad
        return original_content, f"JSON parsing error: {str(e)}"
    except re.error as e:
        return original_content, f"Regex error: {str(e)}"
    except Exception as e:  # Catch-all for unexpected issues within _apply_edit
        print(f"[ERROR] Unexpected error in _apply_edit: {str(e)}")
        return original_content, f"Unexpected error applying edit: {str(e)}"

    return (
        original_content,
        f"Unsupported operation '{operation}' or invalid file type for the operation.",
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

    target_file = os.path.normpath(target_file).lstrip(os.sep)
    workspace_path = getattr(agent, "workspace_path", os.getcwd())
    absolute_workspace_path = os.path.abspath(workspace_path)
    file_path = os.path.abspath(os.path.join(absolute_workspace_path, target_file))

    # print(f"[INFO] Operation: edit_file, Target: {target_file}")
    # print(f"[DEBUG] Raw instructions received for edit: {instructions}")
    # print(f"[INFO] Explanation: {explanation}")

    if not file_path.startswith(absolute_workspace_path):
        error_msg = f"Unsafe file path outside of workspace: {target_file} (resolved to {file_path})"
        print(f"[ERROR] {error_msg}")
        return {"success": False, "error": error_msg}

    if not os.path.exists(file_path):
        error_msg = f"File does not exist: {target_file} (resolved to {file_path})"
        print(f"[ERROR] {error_msg}")
        return {"success": False, "error": error_msg}

    if not os.path.isfile(file_path):
        error_msg = f"Path is not a file: {target_file} (resolved to {file_path})"
        print(f"[ERROR] {error_msg}")
        return {"success": False, "error": error_msg}

    original_content = ""
    try:
        async with aiofiles.open(file_path, "r", encoding="utf-8") as f:  # Use aiofiles
            original_content = await f.read()
    except (OSError, IOError) as e:
        error_msg = f"Failed to read file {target_file} for editing: {str(e)}"
        print(f"[ERROR] {error_msg}")
        return {"success": False, "error": error_msg}
    except Exception as e:
        error_msg = f"Unexpected error reading file {target_file} for editing: {str(e)}"
        print(f"[ERROR] {error_msg}")
        return {"success": False, "error": error_msg}

    try:
        new_content, error = await _apply_edit(
            target_file, original_content, instructions  # instructions should be a dict here
        )
        if error:
            print(f"[ERROR] Failed to apply edit to {target_file}: {error}")
            return {"success": False, "error": error}

        async with aiofiles.open(file_path, "w", encoding="utf-8") as f:  # Use aiofiles
            await f.write(new_content)

        print(f"[INFO] File edited successfully: {target_file}")
        return {
            "success": True,
            "message": f"File edited: {target_file}",
            "file_path": file_path,  # Return absolute path
            "explanation": explanation,
        }
    except (OSError, IOError) as e:
        error_msg = f"Failed to write edited file {target_file}: {str(e)}"
        print(f"[ERROR] {error_msg}")
        return {"success": False, "error": error_msg}
    except Exception as e:
        error_msg = f"Unexpected error editing file {target_file}: {str(e)}"
        print(f"[ERROR] {error_msg}")
        return {"success": False, "error": error_msg}
