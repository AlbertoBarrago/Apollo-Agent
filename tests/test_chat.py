"""Unit tests for the ApolloAgentChat class.

This module contains comprehensive unit tests for the ApolloAgentChat class,
focusing on message processing, tool calls handling, and error scenarios.

Author: Alberto Barrago
License: BSD 3-Clause License - 2025
"""

import unittest
from unittest.mock import AsyncMock, patch, MagicMock
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

    async def test_process_llm_response_empty_message(self):
        """Test processing LLM response with empty message."""
        llm_response = {}
        message, tool_calls, content, duration = await self.chat._process_llm_response(llm_response)
        self.assertIsNone(message)
        self.assertIsNone(tool_calls)
        self.assertIsNone(content)
        self.assertIsNone(duration)

    async def test_process_llm_response_with_content(self):
        """Test processing LLM response with content."""
        llm_response = {
            "message": {
                "content": "Test content",
                "role": "assistant"
            },
            "total_duration": 1000
        }
        message, tool_calls, content, duration = await self.chat._process_llm_response(llm_response)
        self.assertEqual(content, "Test content")
        self.assertEqual(duration, 1000)

    async def test_handle_tool_calls_invalid_format(self):
        """Test handling tool calls with invalid format."""
        tool_calls = "invalid"
        result, current_calls = await self.chat._handle_tool_calls(tool_calls, 1, [])
        self.assertIn("error", result)
        self.assertIsNone(current_calls)

    async def test_handle_tool_calls_loop_detection(self):
        """Test loop detection in tool calls."""
        tool_calls = [{
            "id": "test_id",
            "function": {"name": "test_func", "arguments": {}}
        }]
        recent_tool_calls = ["test_func"]
        result, current_calls = await self.chat._handle_tool_calls(
            tool_calls, 
            Constant.max_chat_iterations + 1, 
            recent_tool_calls
        )
        self.assertIn("response", result)
        self.assertEqual(current_calls, ["test_func"])

    @patch('ollama.chat')
    async def test_get_llm_response_from_ollama(self, mock_ollama_chat):
        """Test getting LLM response from Ollama."""
        mock_response = {
            "message": {
                "content": "Test response",
                "tool_calls": [{
                    "function": {
                        "name": "test_func",
                        "arguments": {"arg": "value"}
                    }
                }]
            }
        }
        mock_ollama_chat.return_value = mock_response
        response = await self.chat._get_llm_response_from_ollama()
        self.assertEqual(response, mock_response)

    async def test_handle_request_concurrent_request(self):
        """Test handling concurrent requests."""
        self.chat._chat_in_progress = True
        result = await self.chat.handle_request("test")
        self.assertIn("error", result)
        self.assertEqual(result["error"], Constant.error_chat_in_progress)

if __name__ == '__main__':
    unittest.main()