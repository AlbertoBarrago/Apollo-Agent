"""Unit tests for the ApolloAgent class.

This module contains comprehensive unit tests for the ApolloAgent class,
focusing on initialization, tool execution, and chat functionality.

Author: Alberto Barrago
License: BSD 3-Clause License - 2025
"""

import unittest
from unittest.mock import patch, AsyncMock
from unittest import IsolatedAsyncioTestCase
from apollo.agent import ApolloAgent
from apollo.config.const import Constant


class TestApolloAgent(IsolatedAsyncioTestCase):
    """Test cases for the ApolloAgent class."""

    def setUp(self):
        """Set up test fixtures."""
        self.test_workspace = "/test/workspace"
        self.agent = ApolloAgent(workspace_path=self.test_workspace)

    def test_init_with_workspace(self):
        """Test initialization with the workspace path."""
        agent = ApolloAgent(workspace_path=self.test_workspace)
        self.assertEqual(agent.workspace_path, self.test_workspace)
        self.assertIsNotNone(agent.tool_executor)
        self.assertIsNotNone(agent.chat_agent)

    def test_init_without_workspace(self):
        """Test initialization without the workspace path."""
        with patch("os.getcwd", return_value=self.test_workspace):
            agent = ApolloAgent()
            self.assertEqual(agent.workspace_path, self.test_workspace)

    def test_tool_registration(self):
        """Test tool registration during initialization."""
        # Verify that all required tools are registered
        registered_functions = self.agent.tool_executor.available_functions

        expected_tools = [
            "create_file",
            "edit_file",
            "list_dir",
            "delete_file",
            "remove_dir",
            "file_search",
            "grep_search",
            "codebase_search",
            "web_search",
            "wiki_search",
        ]

        for tool in expected_tools:
            self.assertIn(tool, registered_functions)

    async def test_execute_tool(self):
        """Test tool execution."""
        test_tool_call = {
            "function": {"name": "list_dir", "arguments": {"target_file": "."}}
        }

        # Mock the executor's execute_tool method
        self.agent.tool_executor.execute_tool = AsyncMock(
            return_value={"success": True, "files": ["test.txt"]}
        )

        result = await self.agent.execute_tool(test_tool_call)
        self.assertTrue(result["success"])
        self.agent.tool_executor.execute_tool.assert_called_once_with(test_tool_call)

    @patch("builtins.print")
    @patch("builtins.input", side_effect=KeyboardInterrupt)
    async def test_chat_terminal_keyboard_interrupt(
        self, _, mock_print
    ):  # Corrected mock order
        """Test chat terminal keyboard interrupt handling."""
        await ApolloAgent.chat_terminal()
        mock_print.assert_any_call("\nExiting chat.")

    @patch("builtins.print")
    @patch("builtins.input", side_effect=EOFError)
    async def test_chat_terminal_eof(self, _, mock_print):  # Corrected mock order
        """Test chat terminal EOF handling."""
        await ApolloAgent.chat_terminal()
        mock_print.assert_any_call("\nExiting chat.")

    @patch("os.path.exists")
    @patch("os.makedirs")
    async def test_chat_terminal_workspace_creation(self, mock_makedirs, mock_exists):
        """Test workspace directory creation in the chat terminal."""
        mock_exists.return_value = False
        # Patch input for this specific test run
        with patch("builtins.input", side_effect=["exit"]):
            await ApolloAgent.chat_terminal()
        mock_makedirs.assert_called_once_with(Constant.workspace_cabled)

    async def test_chat_terminal_exit_workspace(self):
        """Test chat terminal with exit workspace."""
        original_workspace = Constant.workspace_cabled
        Constant.workspace_cabled = "exit"

        try:
            # Patch input for this specific test run if chat_terminal expects input
            with patch("builtins.input", side_effect=["some_input_if_needed", "exit"]):
                result = await ApolloAgent.chat_terminal()
            self.assertIsNone(result)
        finally:
            Constant.workspace_cabled = original_workspace


if __name__ == "__main__":
    unittest.main()
