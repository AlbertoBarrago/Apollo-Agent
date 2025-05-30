"""
Unit tests for the ApolloAgentChat class.

This module contains unit tests for the ApolloAgentChat class,
which is responsible for handling chat interactions and tool function definitions.

Author: Alberto Barrago
License: BSD 3-Clause License - 2025
"""

import unittest
from unittest.mock import AsyncMock, patch

from apollo.tools.chat import ApolloAgentChat
from apollo.tools.executor import ToolExecutor
from apollo.config.const import Constant


class TestApolloAgentChat(unittest.TestCase):
    """Test cases for the ApolloAgentChat class."""

    def setUp(self):
        """Set up test fixtures."""
        self.chat = ApolloAgentChat()
        self.tool_executor = ToolExecutor(workspace_path="/test/workspace")
        self.chat.set_tool_executor(self.tool_executor)

    @patch("apollo.tools.chat_operations.ollama.chat")
    async def test_chat_with_content_response(self, mock_ollama_chat):
        """Test a chat method with a content response."""
        # Mock the ollama.chat response
        mock_ollama_chat.return_value = {
            "message": {"content": "This is a test response", "role": "assistant"}
        }

        # Call the chat method
        result = await self.chat.handle_request("Hello, how are you?")

        # Verify the result
        self.assertIn("response", result)
        self.assertEqual(result["response"], "This is a test response")

        # Verify that ollama.chat was called with the correct arguments
        mock_ollama_chat.assert_called_once()
        args, kwargs = mock_ollama_chat.call_args
        self.assertEqual(kwargs["model"], Constant.llm_model)
        self.assertIn(
            {"role": "user", "content": "Hello, how are you?"}, kwargs["messages"]
        )

    @patch("apollo.tools.chat_operations.ollama.chat")
    async def test_chat_with_tool_calls(self, mock_ollama_chat):
        """Test chat method with tool calls."""
        # Mock the ollama.chat response
        mock_ollama_chat.return_value = {
            "message": {
                "role": "assistant",
                "tool_calls": [
                    {
                        "id": "call_123",
                        "function": {
                            "name": "test_func",
                            "arguments": {"arg1": "value1"},
                        },
                    }
                ],
            }
        }

        # Mock the _execute_tool method
        self.chat._execute_tool = AsyncMock(return_value="Tool execution result")

        # Verify that _execute_tool was called with the correct arguments
        self.chat._execute_tool.assert_called_once()
        args, _ = self.chat._execute_tool.call_args
        self.assertEqual(args[0]["id"], "call_123")
        self.assertEqual(args[0]["function"]["name"], "test_func")

    @patch("apollo.tools.chat_operations.ollama.chat")
    async def test_chat_with_empty_message(self, mock_ollama_chat):
        """Test a chat method with an empty message."""
        # Mock the ollama.chat response
        mock_ollama_chat.return_value = {}

        # Call the chat method
        result = await self.chat.handle_request("Hello")

        # Verify the result
        self.assertIn("response", result)
        self.assertEqual(result["response"], Constant.error_empty_llm_message)

    @patch("apollo.tools.chat_operations.ollama.chat")
    async def test_chat_with_loop_detection(self, mock_ollama_chat):
        """Test a chat method with loop detection."""
        # Mock the ollama.chat response to return the same tool calls twice
        mock_ollama_chat.return_value = {
            "message": {
                "role": "assistant",
                "tool_calls": [
                    {
                        "id": "call_123",
                        "function": {
                            "name": "test_func",
                            "arguments": {"arg1": "value1"},
                        },
                    }
                ],
            }
        }

        # Mock the _handle_tool_calls method to simulate a loop
        async def mock_handle_tool_calls(iterations, recent_tool_calls):
            if iterations > 1 and recent_tool_calls == ["test_func"]:
                return {"response": Constant.error_loop_detected}, ["test_func"]
            return None, ["test_func"]

        self.chat._handle_tool_calls = mock_handle_tool_calls

        # Call the chat method
        result = await self.chat.handle_request("Use a tool repeatedly")

        # Verify the result
        self.assertIn("response", result)
        self.assertEqual(result["response"], Constant.error_loop_detected)


if __name__ == "__main__":
    unittest.main()
