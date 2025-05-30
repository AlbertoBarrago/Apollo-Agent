import json
import os
import time

from apollo.config.const import Constant
from apollo.encoder.json_encoder import ApolloJSONEncoder


def get_session_filename(base_dir: str):
    """Generates a unique filename for a new chat session."""
    timestamp = time.strftime("%Y%m%d_%H%M%S")
    return os.path.join(base_dir, f"chat_history_{timestamp}.json")


def save_user_history_to_json(
    message: str, role: str, current_session_file: str = None
):
    """
    Save a single new message to a JSON file, maintaining a session-based history
    and trimming old messages to a maximum limit. All messages (system, user, assistant)
    are saved as dictionaries with 'role' and 'content' keys.

    Args:
       message: The content of the new message to save.
       role: The role of the sender in the message (e.g., "user", "assistant").
       current_session_file: The path to the current session file. If None, a new session is started.
    """
    session_dir = Constant.chat_history_dir
    max_messages = Constant.max_history_messages

    if not isinstance(message, str) or not role:
        print("[WARNING] Invalid message content or role provided. Skipping save.")
        return

    # Ensure the session directory exists
    os.makedirs(session_dir, exist_ok=True)

    file_path = (
        current_session_file  # Initialize with the current session file if provided
    )

    # Determine if a new session needs to be started
    is_new_session_needed = False
    current_history = []

    if file_path and os.path.exists(file_path):
        try:
            with open(file_path, "r", encoding="utf-8") as file:
                existing_data = json.load(file)
                if isinstance(existing_data, list):
                    current_history = existing_data
                else:
                    print(
                        f"[WARNING] Existing chat history file '{file_path}' "
                        f"is not a list. Starting new history."
                    )
                    is_new_session_needed = (
                        True  # File exists but is malformed, treat as new session
                    )
        except json.JSONDecodeError:
            print(
                f"[WARNING] Chat history file '{file_path}' corrupted. Starting new history."
            )
        except (
            FileNotFoundError
        ):  # Should not happen if file_path exists, but good for robustness
            is_new_session_needed = True
    else:
        is_new_session_needed = True  # No file path provided or file exists

    # Check for system marker if history was loaded successfully
    if not is_new_session_needed and current_history:
        is_system_marker_present_at_start = (
            isinstance(current_history[0], dict)
            and current_history[0].get("role") == "system"
            and Constant.system_new_session.split("{")[0]
            in current_history[0].get("content", "")
        )
        if not is_system_marker_present_at_start:
            is_new_session_needed = True

    if is_new_session_needed:
        file_path = get_session_filename(session_dir)
        # Clear history if a new session starts
        current_history = []
        session_marker = {
            "role": "system",
            "content": Constant.system_new_session.format(
                timestamp=time.strftime("%Y-%m-%d %H:%M:%S")
            ),
        }
        current_history.append(session_marker)
        print(f"Starting new chat session and saving to '{file_path}'")
    else:
        print(f"Continuing existing session in '{file_path}'")

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
                chat_messages = current_history[1:]
                trimmed_history.extend(chat_messages[-max_messages:])
            else:
                trimmed_history = current_history[-max_messages:]
        else:
            trimmed_history = []

        with open(file_path, "w", encoding="utf-8") as file:
            json.dump(trimmed_history, file, indent=4, cls=ApolloJSONEncoder)
            # print(f"Chat history successfully saved to '{file_path}'")

    except OSError as e:
        print(f"[ERROR] Failed to read/write file '{file_path}': {e}")
    except TypeError as e:
        print(f"[ERROR] JSON serialization error: {e}")
        print(
            "Not saving chat history due to serialization error. Please check message structure."
        )

    return file_path  # Return the file path for future reference if needed(for saving to a database or file system).
