"""
Chat interaction logic and tool function definitions for ApolloAgent.

This module defines the core `chat()` coroutine, which handles LLM interactions,
including tool calls using Ollama's function calling API. It also provides the
`get_available_tools()` function, which returns the tool definitions available
to the model, enabling functionality such as file editing, searching, and listing
workspace directories.

Author: Alberto Barrago
License: BSD 3-Clause License - 2024
"""
import re

import ollama
import json

from typing import Any
from apollo_agent.tools.avaiable_tools import get_available_tools
from apollo_agent.encoder.json_encoder import ApolloJSONEncoder


async def chat(agent, text: str) -> None | dict[str, str] | dict[str, Any | None]:
    """
    Responds to the user's message, handling potential tool calls and multi-turn interactions.

    Args:
        agent: The ApolloAgent instance.
        text: The user's message.

    Returns:
        Response from the chat model or error information.
    """
    # Verifica se una chat è già in corso per evitare esecuzioni concorrenti
    if hasattr(agent, '_chat_in_progress') and agent._chat_in_progress:
        print("[WARNING] Chat already in progress, ignoring concurrent request")
        return {"error": "Chat already in progress, please wait for current request to complete"}

    # Imposta il flag di chat in corso
    agent._chat_in_progress = True

    try:
        # Inizializza il contesto di sessione se non esiste
        if not hasattr(agent, "session_id"):
            import uuid
            agent.session_id = str(uuid.uuid4())
            print(f"[INFO] New chat session initialized: {agent.session_id}")

        # Assicurati che la cronologia permanente esista
        agent.permanent_history = agent.permanent_history if hasattr(agent, "permanent_history") else []

        # Verifica se questo messaggio è già nella storia (previene duplicati)
        last_message = agent.permanent_history[-1] if agent.permanent_history else None
        if not last_message or last_message.get("role") != "user" or last_message.get("content") != text:
            agent.permanent_history.append({"role": "user", "content": text})
            agent.chat_history = agent.permanent_history.copy()
            # Salva solo i messaggi utente
            save_user_history_to_json(agent)
        else:
            agent.chat_history = agent.permanent_history.copy()

        # Elimina vecchi messaggi di sistema di iterazione precedenti
        agent.chat_history = [msg for msg in agent.chat_history
                              if not (msg.get("role") == "system" and
                                      "try to reach a conclusion soon" in msg.get("content", "").lower())]

        print("🤖 Give me a second, be patience and kind ", flush=True)

        # Maximum number of tool call iterations to prevent infinite loops
        max_iterations = 5
        iterations = 0
        # Memorizza le chiamate di strumenti per rilevare pattern ripetitivi
        recent_tool_calls = []

        while iterations < max_iterations:
            iterations += 1
            print(f"Starting iteration {iterations}/{max_iterations}")

            try:
                llm_response = ollama.chat(
                    model="llama3.1",
                    messages=agent.chat_history,
                    tools=get_available_tools(),
                    stream=False
                )
            except Exception as e:
                print(f"[ERROR] Exception during ollama.chat call: {str(e)}")
                return {"error": f"Failed to get response from language model: {str(e)}"}

            # Aggiungi il messaggio di sistema dopo il secondo giro
            if iterations > 2:
                agent.chat_history.append({
                    "role": "system",
                    "content": "Please try to reach a conclusion soon. Avoid using more tools unless absolutely necessary."
                })

            message = llm_response.get("message")
            if not message:
                print("[WARNING] LLM response missing 'message' field.")
                agent.chat_history.append(
                    {
                        "role": "assistant",
                        "content": "[Error: Empty message received from LLM]",
                    }
                )
                return {"response": "Received an empty message from the model."}

            if isinstance(message, dict):
                tool_calls = message.get("tool_calls")
                content = message.get("content")
            else:
                tool_calls = getattr(message, "tool_calls", None)
                content = getattr(message, "content", None)

            agent.chat_history.append(message)

            if tool_calls:
                if not isinstance(tool_calls, list):
                    print(
                        f"[ERROR] Received non-list 'tool_calls' from LLM Message. "
                        f"Type: {type(tool_calls)}. Value: {tool_calls}"
                    )
                    return {
                        "error": f"Received unexpected tool_calls format from LLM: {tool_calls}"
                    }

                # Rileva loop di chiamate a tool
                current_tool_calls = []
                for tool_call in tool_calls:
                    # Estrai il nome della funzione in modo sicuro
                    if hasattr(tool_call, "function"):
                        func_name = getattr(tool_call.function, "name", "unknown")
                    elif isinstance(tool_call, dict) and "function" in tool_call:
                        func_name = tool_call["function"].get("name", "unknown")
                    else:
                        func_name = "unknown"
                    current_tool_calls.append(func_name)

                # Verifica se c'è un pattern ripetitivo di chiamate agli strumenti
                if iterations > 1 and current_tool_calls == recent_tool_calls:
                    print("[WARNING] Detected repeated tool call pattern, breaking loop")
                    loop_detected_msg = "I noticed a potential loop in my processing. Let me summarize what I've found so far."
                    agent.permanent_history.append({"role": "assistant", "content": loop_detected_msg})
                    return {
                        "response": loop_detected_msg
                    }

                # Aggiorna l'elenco delle chiamate recenti
                recent_tool_calls = current_tool_calls

                tool_outputs = []
                for tool_call in tool_calls:
                    try:
                        tool_result = await agent.execute_tool(tool_call)

                        # Log dell'errore se lo strumento fallisce
                        if isinstance(tool_result, str) and "[ERROR]" in str(tool_result):
                            print(f"[WARNING] Tool execution failed: {tool_result}")
                    except Exception as e:
                        tool_result = f"[ERROR] Exception during tool execution: {str(e)}"
                        print(tool_result)

                    tool_outputs.append(
                        {
                            "role": "tool",
                            "tool_call_id": getattr(
                                tool_call, "id", tool_call.get("id", "N/A")
                            ),
                            "content": str(tool_result),
                        }
                    )

                agent.chat_history.extend(tool_outputs)

            elif content is not None:
                # Aggiungi questa risposta alla cronologia permanente prima di restituirla
                agent.permanent_history.append({"role": "assistant", "content": content})
                return {"response": content}
            else:
                print("[WARNING] LLM response had neither tool_calls nor content.")
                return {
                    "response": "Completed processing, but received no final message content."
                }

        # If we've reached max iterations, return a timeout message
        timeout_message = f"Reached maximum number of tool call iterations ({max_iterations}). Let me summarize what I've found so far."
        agent.permanent_history.append({"role": "assistant", "content": timeout_message})
        return {"response": timeout_message}

    except RuntimeError as e:
        error_message = f"[ERROR] RuntimeError during chat processing: {e}"
        print(error_message)
        return {"error": error_message}
    except Exception as e:  # Catch all exceptions to avoid complete crashes
        error_message = f"[ERROR] An unexpected error occurred: {str(e)}"
        print(error_message)
        return {"error": error_message}
    finally:
        # Assicurati di reimpostare il flag di chat in corso, anche in caso di errore
        agent._chat_in_progress = False

def save_user_history_to_json(agent, file_path="chat_history.json", max_messages=10):
    """
    Save only the recent user messages to a JSON file, maintaining a session-based history.

    Args:
        agent: Instance of ApolloAgent containing permanent_history.
        file_path: Path to save the JSON file. Defaults to 'chat_history.json'.
        max_messages: Maximum number of user messages to keep in history.
    """
    try:
        cleaned_history = []
        user_messages = []

        # Estrai solo i messaggi utente dalla cronologia permanente
        for message in agent.permanent_history:
            if message.get("role") == "user":
                clean_message = message.copy()
                content = clean_message.get("content", "")

                if isinstance(content, str):
                    content = content.strip()
                    content = " ".join(content.split())

                clean_message["content"] = extract_command(content)
                user_messages.append(clean_message)

        # Mantieni solo gli ultimi max_messages messaggi dell'utente
        cleaned_history = user_messages[-max_messages:] if user_messages else []

        # Aggiungi un timestamp di sessione se si tratta di un nuovo file o se è vuoto
        try:
            with open(file_path, "r", encoding="utf-8") as file:
                existing_data = json.load(file)
                if not existing_data or not cleaned_history:
                    import time
                    session_marker = {
                        "role": "system",
                        "content": f"New session started at {time.strftime('%Y-%m-%d %H:%M:%S')}"
                    }
                    cleaned_history.insert(0, session_marker)
        except (FileNotFoundError, json.JSONDecodeError):
            import time
            session_marker = {
                "role": "system",
                "content": f"New session started at {time.strftime('%Y-%m-%d %H:%M:%S')}"
            }
            cleaned_history.insert(0, session_marker)

        with open(file_path, "w", encoding="utf-8") as file:
            json.dump(cleaned_history, file, indent=4, cls=ApolloJSONEncoder)
        print(f"Chat history successfully saved to {file_path}")
    except FileNotFoundError:
        print(f"[WARNING] {file_path} not found. Starting with an empty chat history.")
        agent.permanent_history = []
    except json.JSONDecodeError as jde:
        print(f"[ERROR] Failed to decode JSON from file {file_path}: {jde}")
        agent.permanent_history = []
    except OSError as e:
        print(f"[ERROR] Failed to read/write file {file_path}: {e}")
    except TypeError as e:
        print(f"[ERROR] JSON serialization error: {e}")
        print("Resetting chat history due to serialization error")
        agent.permanent_history = []

def load_chat_history(agent, file_path="chat_history.json", max_session_messages=5):
    """
    Load only the most recent session messages from a JSON file into permanent_history.

    Args:
        agent: The ApolloAgent instance.
        file_path: Path to the JSON file containing chat history.
        max_session_messages: Maximum number of messages to load from the last session.
    """
    try:
        with open(file_path, "r", encoding="utf-8") as file:
            all_history = json.load(file)

            # Se la cronologia è vuota, inizia con array vuoto
            if not all_history:
                agent.permanent_history = []
                agent.chat_history = []
                return

            # Trova l'ultimo marcatore di sessione
            session_indices = [
                i for i, msg in enumerate(all_history)
                if msg.get("role") == "system" and "New session started at" in msg.get("content", "")
            ]

            # Se non ci sono marcatori di sessione, prendi solo gli ultimi messaggi
            if not session_indices:
                agent.permanent_history = all_history[-max_session_messages:] if all_history else []
            else:
                # Prendi i messaggi dall'ultima sessione
                last_session_start = session_indices[-1]
                agent.permanent_history = all_history[last_session_start:]

            # Initialize chat_history with the permanent history
            agent.chat_history = agent.permanent_history.copy()

        print(f"Chat history successfully loaded from {file_path} (last session only)")
    except FileNotFoundError:
        print(f"[WARNING] {file_path} not found. Starting with an empty chat history.")
        agent.permanent_history = []
        agent.chat_history = []
    except json.JSONDecodeError as jde:
        print(f"[ERROR] Failed to decode JSON from file {file_path}: {jde}")
        agent.permanent_history = []
        agent.chat_history = []
    except OSError as e:
        print(f"[ERROR] Failed to read file {file_path}: {e}")
        agent.permanent_history = []
        agent.chat_history = []

def extract_command(content):
        """Extract the command from user input"""
        if not isinstance(content, str):
            return content

        command_pattern = r"The command is \$(.*?)(?:$|[.?!])"
        match = re.search(command_pattern, content)

        if match:
            command = match.group(1).strip()
            return command

        return content
