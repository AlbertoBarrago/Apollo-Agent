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
    # Add only the user message to permanent chat history
    agent.permanent_history = agent.permanent_history if hasattr(agent, "permanent_history") else []
    agent.permanent_history.append({"role": "user", "content": text})

    agent.chat_history = agent.permanent_history.copy()

    # Save only the user messages
    save_user_history_to_json(agent)

    print("🤖 Give me a second, be patience and kind ", flush=True)

    try:
        # Maximum number of tool call iterations to prevent infinite loops
        max_iterations = 5
        iterations = 0

        while iterations < max_iterations:
            iterations += 1

            llm_response = ollama.chat(
                model="llama3.1",
                messages=agent.chat_history,
                tools=get_available_tools(),
                stream=False,
            )

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

            # Add assistant message to working chat history only
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

                tool_outputs = []
                for tool_call in tool_calls:
                    tool_result = await agent.execute_tool(tool_call)

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
                continue  # Continue to next iteration with updated chat history

            elif content is not None:
                return {"response": content}
            else:
                print("[WARNING] LLM response had neither tool_calls nor content.")
                return {
                    "response": "Completed processing, but received no final message content."
                }

        # If we've reached max iterations, return a timeout message
        return {"response": f"Reached maximum number of tool call iterations ({max_iterations})."}

    except RuntimeError as e:
        error_message = f"[ERROR] RuntimeError during chat processing: {e}"
        print(error_message)
        return {"error": error_message}
    except Exception as e:  # Catch all exceptions to avoid complete crashes
        error_message = f"[ERROR] An unexpected error occurred: {str(e)}"
        print(error_message)
        return {"error": error_message}

def save_user_history_to_json(agent, file_path="chat_history.json"):
    """
    Save only the user messages to a JSON file.

    Args:
        agent: Instance of ApolloAgent containing permanent_history.
        file_path: Path to save the JSON file. Defaults to 'chat_history.json'.
    """
    try:
        cleaned_history = []
        for message in agent.permanent_history:
            if message.get("role") == "user":
                clean_message = message.copy()

                content = clean_message.get("content", "")
                if isinstance(content, str):
                    content = content.strip()
                    content = " ".join(content.split())

                clean_message["content"] = extract_command(content)
                cleaned_history.append(clean_message)

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


def load_chat_history(agent, file_path="chat_history.json"):
    """
    Load only user messages from a JSON file into permanent_history.
    """
    try:
        with open(file_path, "r", encoding="utf-8") as file:
            agent.permanent_history = json.load(file)
            # Initialize chat_history with the permanent history
            agent.chat_history = agent.permanent_history.copy()
        print(f"Chat history successfully loaded from {file_path}")
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
