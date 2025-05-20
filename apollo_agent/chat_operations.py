"""
Chat interaction logic and tool function definitions for ApolloAgent.

This module defines the core `chat()` coroutine, which handles LLM interactions,
including tool calls using Ollama's function calling API. It also provides the
`get_available_tools()` function, which returns the tool definitions available
to the model, enabling functionality such as file editing, searching, and listing
workspace directories.

Author: Alberto Barrago
License: MIT - 2025
"""

import ollama
from typing import List, Dict, Any

from apollo_agent.avaiable_tools import get_available_tools


async def chat(agent, text: str) -> None | dict[str, str] | dict[str, Any | None]:
    """
    Responds to the user's message, handling potential tool calls and multi-turn interactions.

    Args:
        agent: The ApolloAgent instance.
        text: The user's message.

    Returns:
        Response from the chat model or error information.
    """

    agent.chat_history.append({"role": "user", "content": text})

    print("🤖 Give me a second, be patience and kind ", flush=True)

    try:
        while True:
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

            if tool_calls:
                if not isinstance(tool_calls, list):
                    print(
                        f"[ERROR] Received non-list 'tool_calls' from LLM Message. "
                        f"Type: {type(tool_calls)}. Value: {tool_calls}"
                    )
                    agent.chat_history.append(
                        {
                            "role": "assistant",
                            "content": f"[Error: Received non-list tool_calls: {tool_calls}]",
                        }
                    )
                    return {
                        "error": f"Received unexpected tool_calls format from LLM: {tool_calls}"
                    }

                agent.chat_history.append(message)

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

            elif content is not None:
                agent.chat_history.append(message)
                return {"response": content}

            else:
                print("[WARNING] LLM response had neither tool_calls nor content.")
                agent.chat_history.append(message)
                return {
                    "response": "Completed processing, but received no final message content."
                }

    except RuntimeError as e:
        error_message = f"[ERROR] RuntimeError during chat processing: {e}"
        print(error_message)
        return {"error": error_message}
    except SystemError as e:
        error_message = (
            f"[ERROR] An unexpected error occurred during chat processing: {e}"
        )
        print(error_message)
        return {"error": error_message}
