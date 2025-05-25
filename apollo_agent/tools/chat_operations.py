"""
In this file, we define the class for handling chat
interactions and tool function definitions for ApolloAgent.

Author: Alberto Barrago
License: BSD 3-Clause License - 2024
"""

import re
import json
import uuid
import time
import ollama
from typing import Any

from apollo_agent.config.avaiable_tools import get_available_tools
from apollo_agent.encoder.json_encoder import ApolloJSONEncoder
from apollo_agent.config.const import Constant


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
        self.tool_executor = None

    async def _process_llm_response(self, llm_response):
        """
        Process the response from the LLM, extracting message, tool calls, and content.

        Args:
            llm_response: The response from the LLM.

        Returns:
            A tuple of (a message, tool_calls, content).
        """
        message = llm_response.get("message")
        if not message:
            print("[WARNING] LLM response missing 'message' field.")
            self.chat_history.append(
                {
                    "role": "assistant",
                    "content": "[Error: Empty message received from LLM]",
                }
            )
            return None, None, None

        if isinstance(message, dict):
            tool_calls = message.get("tool_calls")
            content = message.get("content")
        else:
            tool_calls = getattr(message, "tool_calls", None)
            content = getattr(message, "content", None)

        self.chat_history.append(message)
        return message, tool_calls, content

    async def _handle_tool_calls(self, tool_calls, iterations, recent_tool_calls):
        """
        Handle tool calls from the LLM.

        Args:
            tool_calls: The tool calls from the LLM.
            iterations: The current iteration-count.
            recent_tool_calls: The recent tool calls for loop detection.

        Returns:
            A tuple of (results, current_tool_calls) where
            results is a response dict if a loop is detected,
            or None if processing should continue,
            and current_tool_calls is a list of function names.
        """
        if not isinstance(tool_calls, list):
            print(
                f"[ERROR] Received non-list 'tool_calls' from LLM Message. "
                f"Type: {type(tool_calls)}. Value: {tool_calls}"
            )
            return {
                "error": f"Received unexpected tool_calls format from LLM: {tool_calls}"
            }, None

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
            loop_detected_msg = Constant.ERROR_LOOP_DETECTED
            self.permanent_history.append(
                {"role": "assistant", "content": loop_detected_msg}
            )
            return {"response": loop_detected_msg}, current_tool_calls

        tool_outputs = []
        for tool_call in tool_calls:
            try:
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
        return None, current_tool_calls

    async def _get_llm_response_from_ollama(self, iterations: int):
        """
        Fetches the LLM response from Ollama, adding a system message if needed.
        """
        try:
            # Add a system message to encourage concluding after a few iterations
            if iterations > 2:
                self.chat_history.append(
                    {"role": "system", "content": Constant.SYSTEM_CONCLUDE_SOON}
                )

            llm_response = ollama.chat(
                model=Constant.LLM_MODEL,
                messages=self.chat_history,
                tools=get_available_tools(),
                stream=False,
            )
            # Extract and print the reasoning
            message = llm_response.get("message", {})
            content = (
                message.get("content", "")
                if isinstance(message, dict)
                else getattr(message, "content", "")
            )
            tool_calls = (
                message.get("tool_calls", [])
                if isinstance(message, dict)
                else getattr(message, "tool_calls", [])
            )

            print(f"\n{'=' * 50}")
            print(f"[ITERATION {iterations} - REASONING]")
            if content:
                print(f"\nThinking: {content}\n")

            if tool_calls:
                print("Planning to use tools:")
                for i, tool in enumerate(tool_calls):
                    if isinstance(tool, dict) and "function" in tool:
                        func_name = tool["function"].get("name", "unknown")
                        func_args = tool["function"].get("arguments", {})
                    else:
                        func_name = (
                            getattr(tool.function, "name", "unknown")
                            if hasattr(tool, "function")
                            else "unknown"
                        )
                        func_args = (
                            getattr(tool.function, "arguments", {})
                            if hasattr(tool, "function")
                            else {}
                        )

                    print(f"  {i + 1}. {func_name}({json.dumps(func_args, indent=2)})")
            print(f"{'=' * 50}\n")

            return llm_response
        except RuntimeError as e:
            print(f"[ERROR] Exception during ollama.chat call: {str(e)}")
            raise

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
            return {"error": Constant.ERROR_CHAT_IN_PROGRESS}

        self._chat_in_progress = True

        try:
            self._initialize_chat_session(text)

            print("🤖 Give me a second, be patience and kind ", flush=True)

            iterations = 0
            recent_tool_calls = []

            return await self.start_iterations(iterations, recent_tool_calls)

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

    async def start_iterations(self, iterations, recent_tool_calls):
        """
        Executes several iterations of interaction with a language model (LLM) and processes
        the result, showing the reasoning process at each step.
        """
        while iterations < Constant.MAX_CHAT_ITERATIONS:
            iterations += 1
            print(f"\n[STARTING ITERATION {iterations}/{Constant.MAX_CHAT_ITERATIONS}]")

            try:
                llm_response = await self._get_llm_response_from_ollama(iterations)
            except RuntimeError as e:
                return {
                    "error": f"Failed to get response from language model: {str(e)}"
                }

            message, tool_calls, content = await self._process_llm_response(
                llm_response
            )
            if message is None:
                return {"response": Constant.ERROR_EMPTY_LLM_MESSAGE}

            if tool_calls:
                result, current_tool_calls = await self._handle_tool_calls(
                    tool_calls, iterations, recent_tool_calls
                )
                print(f"[EXECUTING TOOLS], ${current_tool_calls}")
                if result:
                    print("[LOOP DETECTED - FINISHING]")
                    return result
                recent_tool_calls = current_tool_calls
                print("[TOOLS EXECUTED - CONTINUING REASONING]")
            elif content is not None:
                print("[FINAL RESPONSE READY]")
                self.permanent_history.append({"role": "assistant", "content": content})
                return {"response": content}
            else:
                print("[WARNING] LLM response had neither tool_calls nor content.")
                return {
                    "response": "Completed processing, but received no final message content."
                }
        # Handle reaching maximum iterations
        timeout_message = Constant.ERROR_MAX_ITERATIONS.format(
            max_iterations=Constant.MAX_CHAT_ITERATIONS
        )
        self.permanent_history.append({"role": "assistant", "content": timeout_message})
        return {"response": timeout_message}

    def _initialize_chat_session(self, text: str):
        """Initializes the session and updates chat history."""
        if not self.session_id:
            self.session_id = str(uuid.uuid4())
            print(f"[INFO] New chat session initialized: {self.session_id}")

        last_message = self.permanent_history[-1] if self.permanent_history else None
        if (
            not last_message
            or last_message.get("role") != "user"
            or last_message.get("content") != text
        ):
            self.permanent_history.append({"role": "user", "content": text})
            self.chat_history = self.permanent_history.copy()
            # self._save_user_history_to_json()
        else:
            self.chat_history = self.permanent_history.copy()

        # Remove any "conclude soon" messages from previous iterations
        self.chat_history = [
            msg
            for msg in self.chat_history
            if not (
                msg.get("role") == "system"
                and "try to reach a conclusion soon" in msg.get("content", "").lower()
            )
        ]

    def _save_user_history_to_json(self, file_path=None, max_messages=None):
        """
        Save only the recent user messages to a JSON file, maintaining a session-based history.

        Args:
            file_path: Path to save the JSON file.
            Default to Constant.CHAT_HISTORY_FILE.
            max_messages: Maximum number of user messages to keep in history.
            Default to Constant.MAX_HISTORY_MESSAGES.
        """
        file_path = file_path or Constant.CHAT_HISTORY_FILE
        max_messages = max_messages or Constant.MAX_HISTORY_MESSAGES
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
                            "content": Constant.SYSTEM_NEW_SESSION.format(
                                timestamp=time.strftime("%Y-%m-%d %H:%M:%S")
                            ),
                        }
                        cleaned_history.insert(0, session_marker)
            except (FileNotFoundError, json.JSONDecodeError):
                session_marker = {
                    "role": "system",
                    "content": Constant.SYSTEM_NEW_SESSION.format(
                        timestamp=time.strftime("%Y-%m-%d %H:%M:%S")
                    ),
                }
                cleaned_history.insert(0, session_marker)

            with open(file_path, "w", encoding="utf-8") as file:
                json.dump(cleaned_history, file, indent=4, cls=ApolloJSONEncoder)
            # print(f"Chat history successfully saved to {file_path}")
        except FileNotFoundError:
            print(
                f"[WARNING] {file_path} not found. Starting with an empty chat history."
            )
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

    def load_chat_history(self, file_path=None, max_session_messages=None):
        """
        Load only the most recent session messages from a JSON file into permanent_history.

        Args:
            file_path: Path to the JSON file containing chat history.
            Default to Constant.CHAT_HISTORY_FILE.
            max_session_messages: Maximum number of messages to load from the last session.
            Default to Constant.MAX_SESSION_MESSAGES.
        """
        file_path = file_path or Constant.CHAT_HISTORY_FILE
        max_session_messages = max_session_messages or Constant.MAX_SESSION_MESSAGES
        try:
            with open(file_path, "r", encoding="utf-8") as file:
                all_history = json.load(file)

                if not all_history:
                    self.permanent_history = []
                    self.chat_history = []
                    return

                session_indices = [
                    i
                    for i, msg in enumerate(all_history)
                    if msg.get("role") == "system"
                    and "New session started at" in msg.get("content", "")
                ]

                if not session_indices:
                    self.permanent_history = (
                        all_history[-max_session_messages:] if all_history else []
                    )
                else:
                    last_session_start = session_indices[-1]
                    self.permanent_history = all_history[last_session_start:]

                self.chat_history = self.permanent_history.copy()

            print(
                f"Chat history successfully loaded from {file_path} (last session only)"
            )
        except FileNotFoundError:
            print(
                f"[WARNING] {file_path} not found. Starting with an empty chat history."
            )
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

    def set_tool_executor(self, tool_executor):
        """Associate this chat instance with a ToolExecutor instance."""
        self.tool_executor = tool_executor

    async def _execute_tool(self, tool_call: dict) -> Any:
        """Execute a tool call using the associated tool executor's execute_tool method."""
        if not self.tool_executor:
            return Constant.ERROR_NO_AGENT

        try:
            return await self.tool_executor.execute_tool(tool_call)
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
