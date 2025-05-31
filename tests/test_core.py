# /Users/albz/PycharmProjects/ApolloAgent/tests/test_core.py
"""Unit tests for the ApolloAgentChat class.

This module contains comprehensive unit tests for the ApolloAgentChat class,
focusing on message processing, tool calls handling, and error scenarios.

Author: Alberto Barrago
License: BSD 3-Clause License - 2025
"""

import unittest
from unittest.mock import patch
from unittest import IsolatedAsyncioTestCase
from apollo.tools.core import ApolloCore
from apollo.service.tool.executor import ToolExecutor
from apollo.config.const import Constant


class TestApolloAgentChat(IsolatedAsyncioTestCase):
    """Test cases for the ApolloAgentChat class."""

    def setUp(self):
        """Set up test fixtures."""
        self.core = ApolloCore()
        self.tool_executor = ToolExecutor(workspace_path="/test/workspace")
        self.core.set_tool_executor(self.tool_executor)

    async def test_process_llm_response_empty_message(self):
        """Test processing LLM response with an empty message field in llm_response."""
        llm_response = {}
        (
            returned_message_obj,
            returned_tool_calls,
            returned_content_str,
            returned_duration,
        ) = await self.core.process_llm_response(llm_response)

        self.assertIsNone(returned_message_obj)
        self.assertIsNone(returned_tool_calls)
        self.assertIsNone(returned_content_str)
        self.assertIsNone(returned_duration)

    async def test_process_llm_response_with_content(self):
        """Test processing LLM response with content and no tool calls."""
        expected_message_dict = {"content": "Test content", "role": "assistant"}
        llm_response = {
            "message": expected_message_dict,
            "total_duration": 1000,
        }
        (
            returned_message_obj,
            returned_tool_calls,
            returned_content_str,
            returned_duration,
        ) = await self.core.process_llm_response(llm_response)

        self.assertEqual(returned_message_obj, expected_message_dict)
        self.assertIsNone(returned_tool_calls)  # No tool_calls in the message
        self.assertEqual(returned_content_str, "Test content")
        self.assertEqual(returned_duration, 1000)

    async def test_handle_tool_calls_invalid_format(self):
        """Test handling tool calls with invalid format."""
        tool_calls = "invalid"
        result, current_calls = await self.core._handle_tool_calls(tool_calls, 1, [])
        self.assertIn("error", result)
        self.assertIsNone(current_calls)

    async def test_handle_tool_calls_loop_detection(self):
        """Test loop detection in tool calls."""
        tool_calls = [
            {"id": "test_id", "function": {"name": "test_func", "arguments": {}}}
        ]
        recent_tool_calls = ["test_func"]
        result, current_calls = await self.core._handle_tool_calls(
            tool_calls, Constant.max_chat_iterations + 1, recent_tool_calls
        )
        self.assertIn("response", result)
        self.assertEqual(current_calls, ["test_func"])

    @patch("ollama.chat")
    async def test_get_llm_response_from_ollama(self, mock_ollama_chat):
        """Test getting LLM response from Ollama."""
        mock_response = {
            "message": {
                "content": "Test response",
                "tool_calls": [
                    {"function": {"name": "test_func", "arguments": {"arg": "value"}}}
                ],
            }
        }
        mock_ollama_chat.return_value = mock_response
        response = await self.core._get_llm_response_from_ollama()
        self.assertEqual(response, mock_response)
        # If this method is not supposed to return a value (as per the DeprecationWarning
        # you mentioned earlier), ensure it returns None or has no return statement.
        # For now, assuming it's intended to return the response.

    async def test_handle_request_concurrent_request(self):
        """Test handling concurrent requests."""
        self.core._chat_in_progress = True
        result = await self.core.handle_request("test")
        self.assertIn("error", result)
        self.assertEqual(result["error"], Constant.error_chat_in_progress)


if __name__ == "__main__":
    unittest.main()
