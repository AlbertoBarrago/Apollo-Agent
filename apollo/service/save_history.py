import json
import time

from apollo.config.const import Constant
from apollo.encoder.json_encoder import ApolloJSONEncoder


def save_user_history_to_json(message: str, role: str):
    """
    Save a single new message to a JSON file, maintaining a session-based history
    and trimming old messages to a maximum limit. All messages (system, user, assistant)
    are saved as dictionaries with 'role' and 'content' keys.

    Args:
       message (str): The content of the new message to save.
       role (str): The role of the sender of the message (e.g., "user", "assistant").
    """
    file_path = Constant.chat_history_file_path
    max_messages = Constant.max_history_messages

    if not isinstance(message, str) or not role:
        print("[WARNING] Invalid message content or role provided. Skipping save.")
        return

    try:
        current_history = []
        try:
            with open(file_path, "r", encoding="utf-8") as file:
                existing_data = json.load(file)
                if isinstance(existing_data, list):
                    current_history = existing_data
                else:
                    print(f"[WARNING] Existing chat history file '{file_path}' is not a list. Starting new history.")
        except (FileNotFoundError, json.JSONDecodeError):
            print(f"[WARNING] Chat history file '{file_path}' not found or corrupted. Starting new history.")

        is_system_marker_present_at_start = (
            current_history and
            isinstance(current_history[0], dict) and
            current_history[0].get("role") == "system" and
            Constant.system_new_session.split('{')[0] in current_history[0].get("content", "")
        )

        if not is_system_marker_present_at_start:
            session_marker = {
                "role": "system",
                "content": Constant.system_new_session.format(
                    timestamp=time.strftime("%Y-%m-%d %H:%M:%S")
                ),
            }
            if not current_history:
                current_history.append(session_marker)
            else:
                current_history.insert(0, session_marker)

        cleaned_message_content = message.strip()
        cleaned_message_content = " ".join(cleaned_message_content.split())

        formatted_new_message = {
            "role": role,
            "content": cleaned_message_content
        }
        current_history.append(formatted_new_message)

        trimmed_history = []
        if current_history:
            if isinstance(current_history[0], dict) and current_history[0].get("role") == "system":
                trimmed_history.append(current_history[0])
                chat_messages = current_history[1:]
                trimmed_history.extend(chat_messages[-max_messages:])
            else:
                trimmed_history = current_history[-max_messages:]
        else:
            trimmed_history = []

        with open(file_path, "w", encoding="utf-8") as file:
            json.dump(trimmed_history, file, indent=4, cls=ApolloJSONEncoder)
            #print(f"Chat history successfully saved to '{file_path}'")

    except OSError as e:
        print(f"[ERROR] Failed to read/write file '{file_path}': {e}")
    except TypeError as e:
        print(f"[ERROR] JSON serialization error: {e}")
        print("Not saving chat history due to serialization error. Please check message structure.")
