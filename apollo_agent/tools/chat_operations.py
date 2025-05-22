import re
import ollama
import json
import uuid
import time
from typing import Any

from apollo_agent.tools.avaiable_tools import get_available_tools
from apollo_agent.encoder.json_encoder import ApolloJSONEncoder


class ApolloAgentChat:
    """
    Handles chat interactions and tool function definitions for ApolloAgent.

    This class encapsulates the core chat logic, including LLM interactions,
    tool calls using Ollama's function calling API, and managing chat history.
    """

    def __init__(self):
        """
        Initializes the ApolloAgentChat instance.
        """
        self.session_id: str | None = None
        self.permanent_history: list[dict] = []
        self.chat_history: list[dict] = []
        self._chat_in_progress: bool = False
        self.agent = None

    async def chat(self, text: str) -> None | dict[str, str] | dict[str, Any | None]:
        """
        Responds to the user's message, handling potential tool calls and multi-turn interactions.

        Args:
            text: The user's message.

        Returns:
            Response from the chat model or error information.
        """
        if self._chat_in_progress:
            print("[WARNING] Chat already in progress, ignoring concurrent request")
            return {"error": "Chat already in progress, please wait for current request to complete"}

        self._chat_in_progress = True

        try:
            if not self.session_id:
                self.session_id = str(uuid.uuid4())
                print(f"[INFO] New chat session initialized: {self.session_id}")

            last_message = self.permanent_history[-1] if self.permanent_history else None
            if not last_message or last_message.get("role") != "user" or last_message.get("content") != text:
                self.permanent_history.append({"role": "user", "content": text})
                self.chat_history = self.permanent_history.copy()
                self._save_user_history_to_json()
            else:
                self.chat_history = self.permanent_history.copy()

            self.chat_history = [msg for msg in self.chat_history
                                 if not (msg.get("role") == "system" and
                                         "try to reach a conclusion soon"
                                         in msg.get("content", "").lower())]

            print("🤖 Give me a second, be patience and kind ", flush=True)

            max_iterations = 5
            iterations = 0
            recent_tool_calls = []

            while iterations < max_iterations:
                iterations += 1
                print(f"Starting iteration {iterations}/{max_iterations}")

                try:
                    llm_response = ollama.chat(
                        model="llama3.1",
                        messages=self.chat_history,
                        tools=get_available_tools(),
                        stream=False
                    )
                except RuntimeError as e:
                    print(f"[ERROR] Exception during ollama.chat call: {str(e)}")
                    return {"error": f"Failed to get response from language model: {str(e)}"}

                if iterations > 2:
                    self.chat_history.append({
                        "role": "system",
                        "content": "Please try to reach a conclusion soon. "
                                   "Avoid using more tools unless absolutely necessary."
                    })

                message = llm_response.get("message")
                if not message:
                    print("[WARNING] LLM response missing 'message' field.")
                    self.chat_history.append(
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

                self.chat_history.append(message)

                if tool_calls:
                    if not isinstance(tool_calls, list):
                        print(
                            f"[ERROR] Received non-list 'tool_calls' from LLM Message. "
                            f"Type: {type(tool_calls)}. Value: {tool_calls}"
                        )
                        return {
                            "error": f"Received unexpected tool_calls format from LLM: {tool_calls}"
                        }

                    current_tool_calls = []
                    for tool_call in tool_calls:
                        if hasattr(tool_call, "function"):
                            func_name = getattr(tool_call.function, "name", "unknown")
                        elif isinstance(tool_call, dict) and "function" in tool_call:
                            func_name = tool_call["function"].get("name", "unknown")
                        else:
                            func_name = "unknown"
                        current_tool_calls.append(func_name)

                    if iterations > 1 and current_tool_calls == recent_tool_calls:
                        print("[WARNING] Detected repeated tool call pattern, breaking loop")
                        loop_detected_msg = "I noticed a potential loop in my processing. Let me summarize what I've found so far."
                        self.permanent_history.append({"role": "assistant", "content": loop_detected_msg})
                        return {
                            "response": loop_detected_msg
                        }

                    recent_tool_calls = current_tool_calls

                    tool_outputs = []
                    for tool_call in tool_calls:
                        try:
                            # Assuming execute_tool is a method of the agent passed to chat
                            # If it's not, you'll need to adjust how tools are executed.
                            tool_result = await self._execute_tool(tool_call)

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

                    self.chat_history.extend(tool_outputs)

                elif content is not None:
                    self.permanent_history.append({"role": "assistant", "content": content})
                    return {"response": content}
                else:
                    print("[WARNING] LLM response had neither tool_calls nor content.")
                    return {
                        "response": "Completed processing, but received no final message content."
                    }

            timeout_message = f"Reached maximum number of tool call iterations ({max_iterations}). Let me summarize what I've found so far."
            self.permanent_history.append({"role": "assistant", "content": timeout_message})
            return {"response": timeout_message}

        except RuntimeError as e:
            error_message = f"[ERROR] RuntimeError during chat processing: {e}"
            print(error_message)
            return {"error": error_message}
        except Exception as e:
            error_message = f"[ERROR] An unexpected error occurred: {str(e)}"
            print(error_message)
            return {"error": error_message}
        finally:
            self._chat_in_progress = False

    def _save_user_history_to_json(self, file_path="chat_history.json", max_messages=10):
        """
        Save only the recent user messages to a JSON file, maintaining a session-based history.

        Args:
            file_path: Path to save the JSON file. Defaults to 'chat_history.json'.
            max_messages: Maximum number of user messages to keep in history.
        """
        try:
            user_messages = []

            for message in self.permanent_history:
                if message.get("role") == "user":
                    clean_message = message.copy()
                    content = clean_message.get("content", "")

                    if isinstance(content, str):
                        content = content.strip()
                        content = " ".join(content.split())

                    clean_message["content"] = self._extract_command(content)
                    user_messages.append(clean_message)

            cleaned_history = user_messages[-max_messages:] if user_messages else []

            try:
                with open(file_path, "r", encoding="utf-8") as file:
                    existing_data = json.load(file)
                    if not existing_data or not cleaned_history:
                        session_marker = {
                            "role": "system",
                            "content": f"New session started at "
                                       f"{time.strftime('%Y-%m-%d %H:%M:%S')}"
                        }
                        cleaned_history.insert(0, session_marker)
            except (FileNotFoundError, json.JSONDecodeError):
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
            self.permanent_history = []
        except json.JSONDecodeError as jde:
            print(f"[ERROR] Failed to decode JSON from file {file_path}: {jde}")
            self.permanent_history = []
        except OSError as e:
            print(f"[ERROR] Failed to read/write file {file_path}: {e}")
        except TypeError as e:
            print(f"[ERROR] JSON serialization error: {e}")
            print("Resetting chat history due to serialization error")
            self.permanent_history = []

    def load_chat_history(self, file_path="chat_history.json", max_session_messages=5):
        """
        Load only the most recent session messages from a JSON file into permanent_history.

        Args:
            file_path: Path to the JSON file containing chat history.
            max_session_messages: Maximum number of messages to load from the last session.
        """
        try:
            with open(file_path, "r", encoding="utf-8") as file:
                all_history = json.load(file)

                if not all_history:
                    self.permanent_history = []
                    self.chat_history = []
                    return

                session_indices = [
                    i for i, msg in enumerate(all_history)
                    if msg.get("role") == "system" and "New session started at" in msg.get("content", "")
                ]

                if not session_indices:
                    self.permanent_history = all_history[-max_session_messages:] if all_history else []
                else:
                    last_session_start = session_indices[-1]
                    self.permanent_history = all_history[last_session_start:]

                self.chat_history = self.permanent_history.copy()

            print(f"Chat history successfully loaded from {file_path} (last session only)")
        except FileNotFoundError:
            print(f"[WARNING] {file_path} not found. Starting with an empty chat history.")
            self.permanent_history = []
            self.chat_history = []
        except json.JSONDecodeError as jde:
            print(f"[ERROR] Failed to decode JSON from file {file_path}: {jde}")
            self.permanent_history = []
            self.chat_history = []
        except OSError as e:
            print(f"[ERROR] Failed to read file {file_path}: {e}")
            self.permanent_history = []
            self.chat_history = []

    def set_agent(self, agent):
        """Associate this chat instance with an ApolloAgent instance."""
        self.agent = agent

    async def _execute_tool(self, tool_call: dict) -> Any:
        """Execute a tool call using the associated agent's execute_tool method."""
        if not self.agent:
            return "[ERROR] No agent associated with this chat instance"

        try:
            return await self.agent.execute_tool(tool_call)
        except Exception as e:
            return f"[ERROR] Exception during tool execution: {str(e)}"

    @staticmethod
    def _extract_command(content: str) -> str:
        """
        Extracts a command from user input if present.

        Args:
            content: The user's message content.

        Returns:
            The extracted command or the original content if no command is found.
        """
        if not isinstance(content, str):
            return content

        command_pattern = r"The command is \$(.*?)(?:$|[.?!])"
        match = re.search(command_pattern, content)

        if match:
            command = match.group(1).strip()
            return command

        return content
