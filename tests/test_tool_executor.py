"""
Unit tests for the ToolExecutor class.

This module contains unit tests for the ToolExecutor class,
which is responsible for executing tools and handling tool calls from the LLM.

Author: Alberto Barrago
License: BSD 3-Clause License - 2025
"""

import unittest
import asyncio
from unittest.mock import AsyncMock

from apollo.service.tool.executor import ToolExecutor


class TestToolExecutor(unittest.TestCase):
    """Test cases for the ToolExecutor class."""

    def setUp(self):
        """Set up test fixtures."""
        self.tool_executor = ToolExecutor(workspace_path="/test/workspace")

        # Register a test function
        self.test_func = AsyncMock(return_value="test_result")
        self.tool_executor.register_function("test_func", self.test_func)

    def test_register_function(self):
        """Test registering a function."""
        func = AsyncMock()
        self.tool_executor.register_function("new_func", func)
        self.assertIn("new_func", self.tool_executor.available_functions)
        self.assertEqual(self.tool_executor.available_functions["new_func"], func)

    def test_register_functions(self):
        """Test registering multiple functions."""
        func1 = AsyncMock()
        func2 = AsyncMock()
        self.tool_executor.register_functions({"func1": func1, "func2": func2})
        self.assertIn("func1", self.tool_executor.available_functions)
        self.assertIn("func2", self.tool_executor.available_functions)
        self.assertEqual(self.tool_executor.available_functions["func1"], func1)
        self.assertEqual(self.tool_executor.available_functions["func2"], func2)

    def test_execute_tool_with_invalid_function(self):
        """Test executing a tool with an invalid function."""
        tool_call = {
            "function": {"name": "invalid_func", "arguments": {"arg1": "value1"}}
        }

        result = asyncio.run(self.tool_executor.execute_tool(tool_call))

        self.assertIn("[ERROR]", result)
        self.assertIn("Function 'invalid_func' not found", result)


if __name__ == "__main__":
    unittest.main()
