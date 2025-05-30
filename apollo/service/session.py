"""
In this file, we define functions for saving user chat history to a JSON file.
The file will be saved in the workspace's chat history
and will be named 'chat_history_YYYYMMDD.json'.

Author: Alberto Barrago
License: BSD 3-Clause License - 2025
"""

import datetime
import json
import os
import time

from apollo.config.const import Constant


def get_daily_session_filename(base_dir: str):
    """
    Generates a filename for a daily chat session.
    The filename will be 'chat_history_YYYYMMDD.json'.
    """
    today_date_str = datetime.date.today().strftime("%Y%m%d")
    return os.path.join(base_dir, f"chat_history_{today_date_str}.json")


def save_user_history_to_json(message: str, role: str):
    """
    Save a single new message to a JSON file, maintaining a daily session-based history
    and trimming old messages to a maximum limit. All messages (system, user, assistant)
    are saved as dictionaries with 'role' and 'content' keys.

    Args:
       message: The content of the new message to save.
       role: The role of the sender in the message (e.g., "user", "assistant").
    """
    session_dir = Constant.chat_history_dir
    max_messages = Constant.max_history_messages

    if not isinstance(message, str) or not role:
        print("[WARNING] Invalid message content or role provided. Skipping save.")
        return None

    # Ensure the session directory exists
    os.makedirs(session_dir, exist_ok=True)

    # Determine the file path for today's session
    file_path = get_daily_session_filename(session_dir)

    current_history = []
    is_new_session_for_today = False

    if os.path.exists(file_path):
        try:
            with open(file_path, "r", encoding="utf-8") as file:
                existing_data = json.load(file)
                if isinstance(existing_data, list):
                    current_history = existing_data
                else:
                    print(
                        f"[WARNING] Existing chat history file '{file_path}' "
                        f"is not a list. Starting new history for today."
                    )
                    is_new_session_for_today = True  # File exists but is malformed
        except json.JSONDecodeError:
            print(
                f"[WARNING] Chat history file '{file_path}' corrupted. Starting new history for today."
            )
            is_new_session_for_today = True
        except FileNotFoundError:  # Should not happen if os.path.exists() was true
            is_new_session_for_today = True  # Fallback, though unlikely

        # After loading, check if a system marker is present (first message)
        if not is_new_session_for_today and current_history:
            is_system_marker_present_at_start = (
                isinstance(current_history[0], dict)
                and current_history[0].get("role") == "system"
                and Constant.system_new_session.split("{", maxsplit=1)[0]
                in current_history[0].get("content", "")
            )
            if not is_system_marker_present_at_start:
                # If no system marker or it's not the correct one, treat as new session for today
                print(
                    f"[INFO] System marker missing or malformed in '{file_path}'. Re-initializing session for today."
                )
                is_new_session_for_today = True
    else:
        is_new_session_for_today = True

    if is_new_session_for_today:
        current_history = []  # Start fresh
        session_marker = {
            "role": "system",
            "content": Constant.system_new_session.format(
                timestamp=time.strftime("%Y-%m-%d %H:%M:%S")
            ),
        }
        current_history.append(session_marker)

    try:
        cleaned_message_content = message.strip()
        cleaned_message_content = " ".join(cleaned_message_content.split())

        formatted_new_message = {"role": role, "content": cleaned_message_content}
        current_history.append(formatted_new_message)

        trimmed_history = []
        if current_history:
            if (
                isinstance(current_history[0], dict)
                and current_history[0].get("role") == "system"
            ):
                trimmed_history.append(current_history[0])
                chat_messages = current_history[1:]  # Actual chat messages
                trimmed_history.extend(chat_messages[-max_messages:])
            else:
                trimmed_history = current_history[-max_messages:]

        with open(file_path, "w", encoding="utf-8") as file:
            json.dump(trimmed_history, file, indent=4)
            # print(f"Chat history successfully saved to '{file_path}'")

    except OSError as e:
        print(f"[ERROR] Failed to read/write file '{file_path}': {e}")
    except TypeError as e:
        print(f"[ERROR] JSON serialization error: {e}")
        print(
            "Not saving chat history due to serialization error. Please check message structure."
        )

    return file_path  # Return the file path for future reference if needed
