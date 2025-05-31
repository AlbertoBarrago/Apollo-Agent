"""Unit tests for the file operations module.

This module contains comprehensive unit tests for the file operations,
including list_dir, remove_dir, delete_file, and create_file functions.

Author: Alberto Barrago
License: BSD 3-Clause License - 2025
"""

import unittest
from unittest.mock import patch, MagicMock
from unittest import IsolatedAsyncioTestCase
from apollo.tools.files import list_dir, remove_dir, delete_file, create_file


class TestFileOperations(IsolatedAsyncioTestCase):
    """Test cases for file operations."""

    def setUp(self):
        """Set up test fixtures."""
        self.agent = MagicMock()
        self.agent.workspace_path = "/test/workspace"

    async def test_list_dir_success(self):
        """Test successful directory listing."""
        with patch("os.path.exists") as mock_exists, patch(
            "os.path.isdir"
        ) as mock_isdir, patch("os.listdir") as mock_listdir:

            mock_exists.return_value = True
            mock_isdir.return_value = True
            mock_listdir.return_value = ["file1.txt", "dir1"]

            with patch("os.path.isdir", side_effect=[False, True]):
                result = await list_dir(self.agent, "test_dir")

                self.assertEqual(result["error"], "Path is not a directory: test_dir")

    async def test_list_dir_outside_workspace(self):
        """Test listing directory outside the workspace."""
        with patch("os.path.abspath") as mock_abspath:
            mock_abspath.side_effect = ["/outside/workspace", "/test/workspace"]
            result = await list_dir(self.agent, "../outside")
            self.assertIn("error", result)

    async def test_list_dir_nonexistent(self):
        """Test listing non-existent directory."""
        with patch("os.path.exists", return_value=False):
            result = await list_dir(self.agent, "nonexistent")
            self.assertIn("error", result)

    async def test_remove_dir_success(self):
        """Test successful directory removal."""
        with patch("os.path.exists") as mock_exists, patch(
            "os.path.isdir"
        ) as mock_isdir, patch("os.rmdir") as mock_rmdir:

            mock_exists.return_value = True
            mock_isdir.return_value = True

            result = await remove_dir(self.agent, "test_dir")
            self.assertTrue(result["success"])
            mock_rmdir.assert_called_once()

    async def test_remove_dir_outside_workspace(self):
        """Test removing directory outside workspace."""
        with patch("os.path.abspath") as mock_abspath:
            mock_abspath.side_effect = ["/outside/workspace", "/test/workspace"]
            result = await remove_dir(self.agent, "../outside")
            self.assertIn("error", result)

    async def test_delete_file_success(self):
        """Test successful file deletion."""
        with patch("os.path.exists") as mock_exists, patch(
            "os.path.isfile"
        ) as mock_isfile, patch("os.remove") as mock_remove:

            mock_exists.return_value = True
            mock_isfile.return_value = True

            result = await delete_file(self.agent, "test.txt")
            self.assertTrue(result["success"])
            mock_remove.assert_called_once()

    async def test_delete_file_outside_workspace(self):
        """Test deleting file outside workspace."""
        with patch("os.path.abspath") as mock_abspath:
            mock_abspath.side_effect = ["/outside/workspace", "/test/workspace"]
            result = await delete_file(self.agent, "../test.txt")
            self.assertFalse(result["success"])

    async def test_create_file_success(self):
        """Test successful file creation."""
        test_file = "test.txt"
        instructions = {"content": "test content"}
        explanation = "Test file creation"

        with patch("builtins.open", unittest.mock.mock_open()) as mock_file:
            result = await create_file(self.agent, test_file, instructions, explanation)
            self.assertTrue(result["success"])
            mock_file.assert_called_once()

    async def test_create_file_outside_workspace(self):
        """Test creating file outside workspace."""
        test_file = "../outside.txt"
        instructions = {"content": "test content"}
        explanation = "Test file creation"

        result = await create_file(self.agent, test_file, instructions, explanation)
        self.assertFalse(result["success"])

    async def test_create_file_missing_content(self):
        """Test file creation with missing content."""
        test_file = "test.txt"
        instructions = {}
        explanation = "Test file creation"

        with patch("builtins.open", unittest.mock.mock_open()) as mock_file:
            result = await create_file(self.agent, test_file, instructions, explanation)
            self.assertTrue(result["success"])
            mock_file().write.assert_called_once_with("")


if __name__ == "__main__":
    unittest.main()
