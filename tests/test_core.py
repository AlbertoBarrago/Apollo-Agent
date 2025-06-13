"""Unit tests for the ApolloCore class.

This module contains comprehensive unit tests for the ApolloCore class,
focusing on message processing, tool calls handling, and error scenarios.

Author: Alberto Barrago
License: BSD 3-Clause License - 2025
"""

import unittest
from unittest import IsolatedAsyncioTestCase
from unittest.mock import patch, MagicMock, AsyncMock

from apollo.tools.core import ApolloCore
from apollo.service.tool.executor import ToolExecutor
from apollo.config.const import Constant
from apollo.config.instructions import get_available_tools


async def mock_async_iterator(items):
    for item in items:
        yield item

class TestApolloCore(IsolatedAsyncioTestCase): # Renamed for clarity
    """Test cases for the ApolloCore class."""

    def setUp(self):
        """Set up test fixtures."""
        self.core = ApolloCore()
        self.tool_executor = ToolExecutor(workspace_path="/test/workspace")
        self.core.set_tool_executor(self.tool_executor)
        # Mock external dependencies that are not the focus of ApolloCore logic
        self.mock_ollama_client_chat = AsyncMock()
        self.core.ollama_client.chat = self.mock_ollama_client_chat


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
        self.assertIsNone(returned_tool_calls)
        self.assertEqual(returned_content_str, "Test content")
        self.assertEqual(returned_duration, 1000)

    async def test_process_llm_response_with_tool_calls(self):
        """Test processing LLM response with tool calls."""
        expected_tool_calls = [{"id": "call1", "function": {"name": "tool_A", "arguments": "{}"}}]
        expected_message_dict = {"tool_calls": expected_tool_calls, "role": "assistant", "content": None}
        llm_response = {
            "message": expected_message_dict,
            "total_duration": 1200,
        }
        (
            returned_message_obj,
            returned_tool_calls,
            returned_content_str,
            returned_duration,
        ) = await self.core.process_llm_response(llm_response)

        self.assertEqual(returned_message_obj, expected_message_dict)
        self.assertEqual(returned_tool_calls, expected_tool_calls)
        self.assertIsNone(returned_content_str)
        self.assertEqual(returned_duration, 1200)

    async def test_process_llm_response_message_as_object(self):
        """Test processing LLM response where message is an object, not a dict."""
        mock_message_obj = MagicMock()
        mock_message_obj.content = "Object content"
        mock_message_obj.tool_calls = None
        mock_message_obj.role = "assistant" # Assuming the object might have a role

        llm_response = {
            "message": mock_message_obj,
            "total_duration": 1500,
        }
        (
            returned_message_obj,
            returned_tool_calls,
            returned_content_str,
            returned_duration,
        ) = await self.core.process_llm_response(llm_response)

        self.assertEqual(returned_message_obj, mock_message_obj)
        self.assertIsNone(returned_tool_calls)
        self.assertEqual(returned_content_str, "Object content")
        self.assertEqual(returned_duration, 1500)
        self.assertIn(mock_message_obj, self.core.chat_history)


    async def test_handle_tool_calls_invalid_format(self):
        """Test handling tool calls with invalid format (not a list)."""
        tool_calls = "invalid_string_format" # Not a list
        result, current_calls = await self.core._handle_tool_calls(tool_calls, 1, [])
        self.assertIn("error", result)
        self.assertIn("Received unexpected tool_calls format", result["error"])
        self.assertIsNone(current_calls)

    async def test_handle_tool_calls_loop_detection(self):
        """Test loop detection in tool calls."""
        tool_calls = [
            {"id": "test_id", "function": {"name": "test_func", "arguments": {}}}
        ]
        recent_tool_calls = ["test_func"] # Same as current
        # Iterations > max_chat_iterations and current_tool_calls == recent_tool_calls
        result, current_calls = await self.core._handle_tool_calls(
            tool_calls, Constant.max_chat_iterations + 1, recent_tool_calls
        )
        self.assertIn("response", result)
        self.assertEqual(result["response"], Constant.error_loop_detected)
        self.assertEqual(current_calls, ["test_func"])
        self.assertEqual(self.core.permanent_history[-1]["content"], Constant.error_loop_detected)


    async def test_handle_tool_calls_execution_and_error(self):
        """Test tool execution success and runtime error within _handle_tool_calls."""
        tool_call_success = {"id": "call_ok", "function": {"name": "success_tool", "arguments": "{}"}}
        tool_call_fail = {"id": "call_fail", "function": {"name": "fail_tool", "arguments": "{}"}}

        async def mock_execute_side_effect(tool_call_arg):
            if tool_call_arg["function"]["name"] == "success_tool":
                return "success_output"
            elif tool_call_arg["function"]["name"] == "fail_tool":
                raise RuntimeError("Tool failed!")
            return "default_output"

        with patch.object(self.core, '_execute_tool', side_effect=mock_execute_side_effect) as mock_execute:
            result, _ = await self.core._handle_tool_calls([tool_call_success, tool_call_fail], 1, [])

        self.assertIsNone(result) # No loop detection or error from _handle_tool_calls itself
        self.assertEqual(len(self.core.chat_history), 2) # Two tool outputs
        self.assertEqual(self.core.chat_history[0]["role"], "tool")
        self.assertEqual(self.core.chat_history[0]["tool_call_id"], "call_ok")
        self.assertEqual(self.core.chat_history[0]["content"], "success_output")
        self.assertEqual(self.core.chat_history[1]["role"], "tool")
        self.assertEqual(self.core.chat_history[1]["tool_call_id"], "call_fail")
        self.assertIn("[ERROR] Exception during tool execution: Tool failed!", self.core.chat_history[1]["content"])


    async def test_get_llm_response_from_ollama(self):
        """Test _get_llm_response_from_ollama calls the client correctly."""
        self.core.chat_history = [{"role": "user", "content": "test query"}]
        expected_stream_result = MagicMock()
        self.mock_ollama_client_chat.return_value = expected_stream_result

        stream = await self.core._get_llm_response_from_ollama()

        self.mock_ollama_client_chat.assert_called_once_with(
            model=Constant.llm_model,
            messages=self.core.chat_history,
            tools=get_available_tools(), # from apollo.config.instructions
            stream=True,
            options={},
        )
        self.assertEqual(stream, expected_stream_result)

    @patch('apollo.tools.core.ApolloCore._initialize_chat_session')
    @patch('apollo.tools.core.ApolloCore.start_iterations', new_callable=AsyncMock)
    async def test_handle_request_successful_path(self, mock_start_iterations, mock_init_session):
        """Test the successful path of handle_request."""
        expected_response = {"response": "LLM says hi"}
        mock_start_iterations.return_value = expected_response
        self.core._chat_in_progress = False # Ensure it starts false

        response = await self.core.handle_request("user input")

        mock_init_session.assert_called_once_with("user input")
        mock_start_iterations.assert_called_once_with(0, [])
        self.assertEqual(response, expected_response)
        self.assertFalse(self.core._chat_in_progress) # Check finally block

    @patch('apollo.tools.core.ApolloCore._initialize_chat_session')
    @patch('apollo.tools.core.ApolloCore.start_iterations', new_callable=AsyncMock)
    async def test_handle_request_runtime_error(self, mock_start_iterations, mock_init_session):
        """Test handle_request when start_iterations raises RuntimeError."""
        mock_start_iterations.side_effect = RuntimeError("Core processing failed")
        self.core._chat_in_progress = False

        response = await self.core.handle_request("user input")

        self.assertIn("error", response)
        self.assertIn("Core processing failed", response["error"])
        self.assertFalse(self.core._chat_in_progress) # Check finally block

    @patch('apollo.tools.core.ApolloCore._initialize_chat_session')
    @patch('apollo.tools.core.ApolloCore.start_iterations', new_callable=AsyncMock)
    async def test_handle_request_io_error(self, mock_start_iterations, mock_init_session):
        """Test handle_request when start_iterations raises IOError."""
        mock_start_iterations.side_effect = IOError("Disk full")
        self.core._chat_in_progress = False

        response = await self.core.handle_request("user input")

        self.assertIn("error", response)
        self.assertIn("Disk full", response["error"])
        self.assertFalse(self.core._chat_in_progress) # Check finally block


    async def test_handle_request_concurrent_request(self):
        """Test handling concurrent requests (existing test)."""
        self.core._chat_in_progress = True # Set flag to simulate ongoing request
        result = await self.core.handle_request("test concurrent")
        self.assertIn("error", result)
        self.assertEqual(result["error"], Constant.error_chat_in_progress)
        self.core._chat_in_progress = False # Reset for other tests


    @patch('apollo.tools.core.ApolloCore._get_llm_response_from_ollama', new_callable=AsyncMock)
    async def test_start_iterations_get_llm_response_error(self, mock_get_llm_response):
        """Test start_iterations when _get_llm_response_from_ollama raises RuntimeError."""
        mock_get_llm_response.side_effect = RuntimeError("Ollama connection failed")
        response = await self.core.start_iterations(0, [])
        self.assertIn("error", response)
        self.assertIn("Ollama connection failed", response["error"])



    @patch('apollo.tools.core.ApolloCore._get_llm_response_from_ollama', new_callable=AsyncMock)
    async def test_start_iterations_no_content_no_tools_fallback(self, mock_get_llm):
        """Test start_iterations fallback when LLM gives an empty message (no content, no tools)."""
        empty_llm_chunks = [
            {"message": {"role": "assistant", "content": None, "tool_calls": None}}, # Empty but valid structure
            {"done": True, "total_duration": 300, "message": {"role": "assistant", "content": None, "tool_calls": None}},
        ]
        mock_get_llm.return_value = mock_async_iterator(empty_llm_chunks)

        response = await self.core.start_iterations(0, [])
        self.assertIn("No content or tools were provided", response["response"])


    async def test_execute_tool_no_executor(self):
        """Test _execute_tool when tool_executor is None."""
        self.core.tool_executor = None
        result = await self.core._execute_tool({"function": {"name": "any_tool"}})
        self.assertEqual(result, Constant.error_no_agent)

    async def test_execute_tool_success_and_runtime_error(self):
        """Test _execute_tool for success and RuntimeError from executor."""
        mock_executor = AsyncMock(spec=ToolExecutor)
        self.core.set_tool_executor(mock_executor)

        tool_call_success = {"function": {"name": "good_tool"}}
        tool_call_fail = {"function": {"name": "bad_tool"}}

        mock_executor.execute_tool.side_effect = [
            "tool_success_result",
            RuntimeError("Executor failed")
        ]

        result_success = await self.core._execute_tool(tool_call_success)
        self.assertEqual(result_success, "tool_success_result")

        result_fail = await self.core._execute_tool(tool_call_fail)
        self.assertIn("[ERROR] Exception during tool execution: Executor failed", result_fail)
        self.assertEqual(mock_executor.execute_tool.call_count, 2)


    def test_set_tool_executor(self):
        """Test set_tool_executor method."""
        new_executor = ToolExecutor(workspace_path="/new_ws")
        self.core.set_tool_executor(new_executor)
        self.assertIs(self.core.tool_executor, new_executor)

    @patch('apollo.tools.core.uuid.uuid4')
    @patch('apollo.tools.core.print') # Mock print to avoid console output during tests
    async def test_initialize_chat_session_new_session(self, mock_print, mock_uuid):
        """Test _initialize_chat_session for a new session."""
        mock_uuid.return_value = "test-session-id"
        self.core.session_id = None # Ensure it's a new session
        self.core.permanent_history = []

        self.core._initialize_chat_session("First message")

        self.assertEqual(self.core.session_id, "test-session-id")
        mock_print.assert_any_call("[INFO] New chat session: test-session-id")
        self.assertEqual(len(self.core.permanent_history), 1)
        self.assertEqual(self.core.permanent_history[0], {"role": "user", "content": "First message"})
        self.assertEqual(self.core.chat_history, self.core.permanent_history)

    @patch('apollo.tools.core.print')
    async def test_initialize_chat_session_existing_session_new_message(self, mock_print):
        """Test _initialize_chat_session with an existing session and new message."""
        self.core.session_id = "existing-id"
        self.core.permanent_history = [{"role": "user", "content": "Old message"}]

        self.core._initialize_chat_session("New message")

        self.assertEqual(len(self.core.permanent_history), 2)
        self.assertEqual(self.core.permanent_history[1], {"role": "user", "content": "New message"})
        self.assertEqual(self.core.chat_history, self.core.permanent_history)
        mock_print.assert_not_called() # No "New chat session" print

    @patch('apollo.tools.core.print')
    async def test_initialize_chat_session_existing_session_same_message(self, mock_print):
        """Test _initialize_chat_session with an existing session and same last message."""
        self.core.session_id = "existing-id"
        self.core.permanent_history = [{"role": "user", "content": "Same message"}]

        self.core._initialize_chat_session("Same message") # Input text is the same as last history

        self.assertEqual(len(self.core.permanent_history), 1) # History should not grow
        self.assertEqual(self.core.chat_history, self.core.permanent_history)
        # The print(f"Chat History {self.chat_history}") should be called in this case
        mock_print.assert_called_once_with(f"Chat History {self.core.chat_history}")


if __name__ == "__main__":
    unittest.main()