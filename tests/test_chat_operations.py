"""
Unit tests for the ApolloAgentChat class.

This module contains unit tests for the ApolloAgentChat class,
which is responsible for handling chat interactions and tool function definitions.

Author: Alberto Barrago
License: BSD 3-Clause License - 2024
"""

import unittest
from unittest.mock import AsyncMock, patch, mock_open

from apollo_agent.tools.chat import ApolloAgentChat
from apollo_agent.tools._executor import ToolExecutor
from apollo_agent.config.const import Constant


class TestApolloAgentChat(unittest.TestCase):
    """Test cases for the ApolloAgentChat class."""

    def setUp(self):
        """Set up test fixtures."""
        self.chat = ApolloAgentChat()
        self.tool_executor = ToolExecutor(workspace_path="/test/workspace")
        self.chat.set_tool_executor(self.tool_executor)

    @patch("apollo_agent.tools.chat_operations.ollama.chat")
    async def test_chat_with_content_response(self, mock_ollama_chat):
        """Test a chat method with a content response."""
        # Mock the ollama.chat response
        mock_ollama_chat.return_value = {
            "message": {"content": "This is a test response", "role": "assistant"}
        }

        # Call the chat method
        result = await self.chat.chat("Hello, how are you?")

        # Verify the result
        self.assertIn("response", result)
        self.assertEqual(result["response"], "This is a test response")

        # Verify that ollama.chat was called with the correct arguments
        mock_ollama_chat.assert_called_once()
        args, kwargs = mock_ollama_chat.call_args
        self.assertEqual(kwargs["model"], Constant.LLM_MODEL)
        self.assertIn(
            {"role": "user", "content": "Hello, how are you?"}, kwargs["messages"]
        )

    @patch("apollo_agent.tools.chat_operations.ollama.chat")
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

    @patch("apollo_agent.tools.chat_operations.ollama.chat")
    async def test_chat_with_empty_message(self, mock_ollama_chat):
        """Test a chat method with an empty message."""
        # Mock the ollama.chat response
        mock_ollama_chat.return_value = {}

        # Call the chat method
        result = await self.chat.chat("Hello")

        # Verify the result
        self.assertIn("response", result)
        self.assertEqual(result["response"], Constant.ERROR_EMPTY_LLM_MESSAGE)

    @patch("apollo_agent.tools.chat_operations.ollama.chat")
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
                return {"response": Constant.ERROR_LOOP_DETECTED}, ["test_func"]
            return None, ["test_func"]

        self.chat._handle_tool_calls = mock_handle_tool_calls

        # Call the chat method
        result = await self.chat.chat("Use a tool repeatedly")

        # Verify the result
        self.assertIn("response", result)
        self.assertEqual(result["response"], Constant.ERROR_LOOP_DETECTED)

    @patch("builtins.open", new_callable=mock_open, read_data="[]")
    @patch("apollo_agent.tools.chat_operations.json.dump")
    def test_save_user_history_to_json(self, mock_json_dump, mock_file):
        """Test _save_user_history_to_json method."""
        # Set up test data
        self.chat.permanent_history = [
            {"role": "user", "content": "Hello"},
            {"role": "assistant", "content": "Hi there"},
            {"role": "user", "content": "How are you?"},
        ]

        self.chat._save_user_history_to_json()

        # Verify that open was called with the correct arguments
        mock_file.assert_called_with(Constant.CHAT_HISTORY_FILE, "w", encoding="utf-8")

        # Verify that json.dump was called
        mock_json_dump.assert_called_once()

    @patch(
        "builtins.open",
        new_callable=mock_open,
        read_data='[{"role": "user", "content": "Hello"}]',
    )
    @patch("apollo_agent.tools.chat_operations.json.load")
    def test_load_chat_history(self, mock_json_load, mock_file):
        """Test load_chat_history method."""
        # Set up test data
        mock_json_load.return_value = [{"role": "user", "content": "Hello"}]

        # Call the method
        self.chat.load_chat_history()

        # Verify that open was called with the correct arguments
        mock_file.assert_called_with(Constant.CHAT_HISTORY_FILE, "r", encoding="utf-8")

        # Verify that the chat history was loaded
        self.assertEqual(len(self.chat.permanent_history), 1)
        self.assertEqual(self.chat.permanent_history[0]["content"], "Hello")

    def test_extract_command(self):
        """Test _extract_command method."""
        # Test with a command
        content = "The command is $ls -la"
        result = self.chat._extract_command(content)
        self.assertEqual(result, "ls -la")

        # Test with no command
        content = "Hello, how are you?"
        result = self.chat._extract_command(content)
        self.assertEqual(result, content)

        # Test with non-string input
        content = 123
        result = self.chat._extract_command(content)
        self.assertEqual(result, content)


if __name__ == "__main__":
    unittest.main()
