"""Unit tests for the ApolloAgent class.

This module contains comprehensive unit tests for the ApolloAgent class,
focusing on initialization, tool execution, and chat functionality.

Author: Alberto Barrago
License: BSD 3-Clause License - 2025
"""

import unittest
import os
from unittest.mock import patch, MagicMock, AsyncMock
from apollo.agent import ApolloAgent
from apollo.config.const import Constant

class TestApolloAgent(unittest.TestCase):
    """Test cases for the ApolloAgent class."""

    def setUp(self):
        """Set up test fixtures."""
        self.test_workspace = "/test/workspace"
        self.agent = ApolloAgent(workspace_path=self.test_workspace)

    def test_init_with_workspace(self):
        """Test initialization with workspace path."""
        agent = ApolloAgent(workspace_path=self.test_workspace)
        self.assertEqual(agent.workspace_path, self.test_workspace)
        self.assertIsNotNone(agent.tool_executor)
        self.assertIsNotNone(agent.chat_agent)

    def test_init_without_workspace(self):
        """Test initialization without workspace path."""
        with patch('os.getcwd', return_value=self.test_workspace):
            agent = ApolloAgent()
            self.assertEqual(agent.workspace_path, self.test_workspace)

    def test_tool_registration(self):
        """Test tool registration during initialization."""
        # Verify that all required tools are registered
        registered_functions = self.agent.tool_executor.available_functions
        
        expected_tools = [
            'create_file', 'edit_file', 'list_dir', 'delete_file',
            'remove_dir', 'file_search', 'grep_search', 'codebase_search',
            'web_search', 'wiki_search'
        ]
        
        for tool in expected_tools:
            self.assertIn(tool, registered_functions)

    async def test_execute_tool(self):
        """Test tool execution."""
        test_tool_call = {
            "function": {
                "name": "list_dir",
                "arguments": {"target_file": "."}
            }
        }

        # Mock the tool executor's execute_tool method
        self.agent.tool_executor.execute_tool = AsyncMock(
            return_value={"success": True, "files": ["test.txt"]}
        )

        result = await self.agent.execute_tool(test_tool_call)
        self.assertTrue(result["success"])
        self.agent.tool_executor.execute_tool.assert_called_once_with(test_tool_call)

    @patch('builtins.print')
    @patch('builtins.input', side_effect=['test input', 'exit'])
    async def test_chat_terminal(self, mock_print):
        """Test chat terminal functionality."""
        # Mock the necessary components
        with patch('os.path.exists', return_value=True), \
             patch('apollo.service.save_history.save_user_history_to_json') as mock_save_history, \
             patch.object(self.agent.chat_agent, 'handle_request') as mock_handle_request:

            mock_handle_request.return_value = {"response": "Test response"}
            
            await ApolloAgent.chat_terminal()

            # Verify the welcome message was printed
            mock_print.assert_any_call(Constant.apollo_welcome)
            
            # Verify history was saved
            mock_save_history.assert_called_with(message='test input', role='user')
            
            # Verify a chat request was handled
            mock_handle_request.assert_called_once()

    @patch('builtins.print')
    @patch('builtins.input', side_effect=KeyboardInterrupt)
    async def test_chat_terminal_keyboard_interrupt(self, mock_print):
        """Test chat terminal keyboard interrupt handling."""
        await ApolloAgent.chat_terminal()
        mock_print.assert_any_call("\nExiting chat.")

    @patch('builtins.print')
    @patch('builtins.input', side_effect=EOFError)
    async def test_chat_terminal_eof(self, mock_print):
        """Test chat terminal EOF handling."""
        await ApolloAgent.chat_terminal()
        mock_print.assert_any_call("\nExiting chat.")

    @patch('os.path.exists')
    @patch('os.makedirs')
    async def test_chat_terminal_workspace_creation(self, mock_makedirs, mock_exists):
        """Test workspace directory creation in the chat terminal."""
        mock_exists.return_value = False
        with patch('builtins.input', side_effect=['exit']):
            await ApolloAgent.chat_terminal()
            mock_makedirs.assert_called_once_with(Constant.workspace_cabled)

    async def test_chat_terminal_exit_workspace(self):
        """Test chat terminal with exit workspace."""
        original_workspace = Constant.workspace_cabled
        Constant.workspace_cabled = "exit"
        
        try:
            result = await ApolloAgent.chat_terminal()
            self.assertIsNone(result)
        finally:
            Constant.workspace_cabled = original_workspace

if __name__ == '__main__':
    unittest.main()