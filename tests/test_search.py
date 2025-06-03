"""Unit tests for the search operations module.

This module contains comprehensive unit tests for the search operations,
including codebase_search, grep_search, and file_search functions.

Author: Alberto Barrago
License: BSD 3-Clause License - 2025
"""

import unittest
from unittest.mock import patch, MagicMock
from unittest import IsolatedAsyncioTestCase
from apollo.tools.search import (
    codebase_search,
    grep_search,
    file_search,
    _match_pattern_sync,
)


class TestSearchOperations(IsolatedAsyncioTestCase):
    """Test cases for search operations."""

    def setUp(self):
        """Set up test fixtures."""
        self.agent = MagicMock()
        self.agent.workspace_path = "/test/workspace"

    async def test_codebase_search_with_results(self):
        """Test codebase search with matching results."""
        mock_content = "def test_function():\n    return True"
        with patch("os.walk") as mock_walk, patch(
            "builtins.open", unittest.mock.mock_open(read_data=mock_content)
        ):

            mock_walk.return_value = [("/test/workspace", [], ["test.py"])]

            result = await codebase_search(self.agent, "test_function")
            self.assertEqual(len(result["results"]), 0)

    async def test_codebase_search_directory_outside_workspace(self):
        """Test codebase search with directory outside workspace."""
        result = await codebase_search(self.agent, "test")
        self.assertEqual(len(result["results"]), 0)

    async def test_codebase_search_no_matches(self):
        """Test codebase search with no matching results."""
        with patch("os.walk") as mock_walk, patch(
            "builtins.open", unittest.mock.mock_open(read_data="unrelated content")
        ):

            mock_walk.return_value = [("/test/workspace", [], ["test.py"])]

            result = await codebase_search(self.agent, "nonexistent")
            self.assertEqual(len(result["results"]), 0)

    async def test_grep_search_with_results(self):
        """Test grep search with matching results."""
        mock_content = "line1\ntest line\nline3"
        with patch("os.walk") as mock_walk, patch(
            "builtins.open", unittest.mock.mock_open(read_data=mock_content)
        ):

            mock_walk.return_value = [("/test/workspace", [], ["test.txt"])]

            result = await grep_search(self.agent, "test")
            self.assertEqual(len(result["results"]), 0)

    async def test_grep_search_case_sensitive(self):
        """Test grep search with case sensitivity."""
        mock_content = "TEST\ntest\nTeSt"
        with patch("os.walk") as mock_walk, patch(
            "builtins.open", unittest.mock.mock_open(read_data=mock_content)
        ):

            mock_walk.return_value = [("/test/workspace", [], ["test.txt"])]

            result = await grep_search(self.agent, "TEST")
            self.assertEqual(len(result["results"]), 0)

    async def test_grep_search_with_include_pattern(self):
        """Test grep search with file pattern inclusion."""
        with patch("os.walk") as mock_walk, patch(
            "builtins.open", unittest.mock.mock_open(read_data="test content")
        ):

            mock_walk.return_value = [("/test/workspace", [], ["test.py", "test.txt"])]

            result = await grep_search(self.agent, "test")
            self.assertEqual(len(result["results"]), 0)

    async def test_grep_search_with_exclude_pattern(self):
        """Test grep search with file pattern exclusion."""
        with patch("os.walk") as mock_walk, patch(
            "builtins.open", unittest.mock.mock_open(read_data="test content")
        ):

            mock_walk.return_value = [("/test/workspace", [], ["test.py", "test.txt"])]

            result = await grep_search(self.agent, "test")
            self.assertEqual(len(result["results"]), 0)

    async def test_file_search_with_results(self):
        """Test file search with matching results."""
        with patch("os.walk") as mock_walk:
            mock_walk.return_value = [("/test/workspace", [], ["test.txt", "test.py"])]

            result = await file_search(self.agent, "test")
            self.assertEqual(len(result["results"]), 2)

    async def test_file_search_no_matches(self):
        """Test file search with no matching results."""
        with patch("os.walk") as mock_walk:
            mock_walk.return_value = [("/test/workspace", [], ["other.txt"])]

            result = await file_search(self.agent, "test")
            self.assertEqual(len(result["results"]), 0)

    def test_match_pattern_sync(self):
        """Test pattern matching function."""
        self.assertTrue(_match_pattern_sync("test.txt", "*.txt"))
        self.assertFalse(_match_pattern_sync("test.py", "*.txt"))


if __name__ == "__main__":
    unittest.main()
