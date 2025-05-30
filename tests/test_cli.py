"""Unit tests for the CLI module.

This module contains comprehensive unit tests for the command-line interface functionality,
focusing on argument parsing and command execution.

Author: Alberto Barrago
License: BSD 3-Clause License - 2025
"""

import unittest
from unittest.mock import patch, AsyncMock
import argparse
from apollo.cli import main, parse_args, run_apollo
from apollo.config.const import Constant


class TestCLI(unittest.TestCase):
    """Test cases for CLI functionality."""

    def test_parse_args_default(self):
        """Test argument parsing with default values."""
        with patch("sys.argv", ["apollo"]):
            args = parse_args()
            self.assertEqual(args.workspace, None)
            self.assertEqual(args.mode, "chat")

    def test_parse_args_workspace(self):
        """Test argument parsing with workspace specified."""
        with patch("sys.argv", ["apollo", "--workspace", "/test/workspace"]):
            args = parse_args()
            self.assertEqual(args.workspace, "/test/workspace")
            self.assertEqual(args.mode, "chat")

    def test_parse_args_mode(self):
        """Test argument parsing with mode specified."""
        with patch("sys.argv", ["apollo", "--mode", "execute"]):
            args = parse_args()
            self.assertEqual(args.workspace, None)
            self.assertEqual(args.mode, "execute")

    def test_parse_args_invalid_mode(self):
        """Test argument parsing with invalid mode."""
        with patch("sys.argv", ["apollo", "--mode", "invalid"]):
            with self.assertRaises(SystemExit):
                parse_args()

    @patch("apollo.cli.run_apollo")
    def test_main_success(self, mock_run_apollo):
        """Test main function with successful execution."""
        with patch("sys.argv", ["apollo"]):
            main()
            mock_run_apollo.assert_called_once()

    @patch("apollo.cli.run_apollo")
    def test_main_keyboard_interrupt(self, mock_run_apollo):
        """Test main function with keyboard interrupt."""
        mock_run_apollo.side_effect = KeyboardInterrupt
        with patch("sys.argv", ["apollo"]):
            with self.assertRaises(SystemExit):
                main()

    @patch("apollo.agent.ApolloAgent")
    async def test_run_apollo_chat_mode(self, mock_agent_class):
        """Test running Apollo in chat mode."""
        mock_agent = AsyncMock()
        mock_agent_class.return_value = mock_agent
        mock_agent.chat_terminal = AsyncMock()

        args = argparse.Namespace(mode="chat", workspace=None)
        await run_apollo(args)

        mock_agent.chat_terminal.assert_called_once()

    @patch("apollo.agent.ApolloAgent")
    async def test_run_apollo_execute_mode(self, mock_agent_class):
        """Test running Apollo in execute mode."""
        mock_agent = AsyncMock()
        mock_agent_class.return_value = mock_agent
        mock_agent.execute_tool = AsyncMock()

        args = argparse.Namespace(mode="execute", workspace=None)
        await run_apollo(args)

        mock_agent.execute_tool.assert_called_once()

    @patch("apollo.agent.ApolloAgent")
    async def test_run_apollo_with_workspace(self, mock_agent_class):
        """Test running Apollo with custom workspace."""
        mock_agent = AsyncMock()
        mock_agent_class.return_value = mock_agent
        mock_agent.chat_terminal = AsyncMock()

        test_workspace = "/test/workspace"
        args = argparse.Namespace(mode="chat", workspace=test_workspace)
        await run_apollo(args)

        mock_agent_class.assert_called_once_with(workspace_path=test_workspace)

    @patch("apollo.agent.ApolloAgent")
    async def test_run_apollo_error_handling(self, mock_agent_class):
        """Test error handling in run_apollo function."""
        mock_agent = AsyncMock()
        mock_agent_class.return_value = mock_agent
        mock_agent.chat_terminal.side_effect = Exception("Test error")

        args = argparse.Namespace(mode="chat", workspace=None)
        with self.assertRaises(Exception):
            await run_apollo(args)

    def test_constant_values(self):
        """Test constant values used in CLI."""
        self.assertIsInstance(Constant.apollo_welcome, str)
        self.assertIsInstance(Constant.workspace_cabled, str)
        self.assertIsInstance(Constant.llm_model, str)


if __name__ == "__main__":
    unittest.main()
