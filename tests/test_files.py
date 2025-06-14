import unittest
from unittest.mock import patch, MagicMock, AsyncMock
from unittest import IsolatedAsyncioTestCase
import os

from apollo.tools.files import list_dir, remove_dir, delete_file, create_file

def mock_aiofiles_open_factory(read_data=""):
    """
    Creates a factory for mocking aiofiles.open.
    The factory returns a mock that, when called, returns an async context manager.
    The context manager's __aenter__ returns a mock file object.
    The mock file object is also attached to the main open mock for easy access.
    """
    mock_file_object = AsyncMock()

    async def async_iterator_lines(data_lines_iterable):
        for line in data_lines_iterable:
            yield line

    if isinstance(read_data, list):
        mock_file_object.read.return_value = "".join(read_data)
        mock_file_object.__aiter__.return_value = async_iterator_lines(read_data)
    else:
        mock_file_object.read.return_value = read_data
        mock_file_object.__aiter__.return_value = async_iterator_lines(read_data.splitlines(True))

    mock_file_object.write = AsyncMock()
    mock_file_object.writelines = AsyncMock()
    mock_file_object.close = AsyncMock()

    mock_context_manager = AsyncMock()
    mock_context_manager.__aenter__.return_value = mock_file_object
    mock_context_manager.__aexit__ = AsyncMock(return_value=None)

    open_function_mock = AsyncMock(return_value=mock_context_manager)
    open_function_mock.mock_file_object = mock_file_object
    return open_function_mock


class TestFileOperations(IsolatedAsyncioTestCase):
    """Test cases for file operations."""

    def setUp(self):
        """Set up test fixtures."""
        self.agent = MagicMock()
        self.agent.workspace_path = "/test/workspace"
        self.full_path = lambda p: os.path.join(self.agent.workspace_path, p.lstrip(os.sep))

    # --- Add this new test method ---
    async def test_create_file_logged_error_parent_path_is_file(self):
        """
        Tests the specific error from logs: Cannot create file; parent path /test/workspace/test/workspace
        exists but is not a directory.
        This occurs if target_file is e.g., "workspace/some_file.txt" and the
        calculated parent "/test/workspace/workspace" is mocked as a file.
        """
        # This target_file will result in parent_dir being /test/workspace/workspace
        target_file_argument = "workspace/another_file.txt"

        # This is the parent directory that create_file will calculate and check
        calculated_parent_dir = os.path.join(self.agent.workspace_path, "workspace")
        # self.agent.workspace_path is /test/workspace
        # So, calculated_parent_dir is /test/workspace/workspace

        instructions = {"content": "test content for this specific error case"}
        explanation = "Test specific parent-is-file error from logs"

        # More robust abspath mock:
        def robust_abspath_side_effect(path_arg):
            if path_arg == self.agent.workspace_path: # Call for workspace_path itself
                return self.agent.workspace_path
            # Call for an already joined path like /test/workspace/workspace/another_file.txt
            if path_arg.startswith(self.agent.workspace_path):
                return path_arg
            # Should not be reached if create_file calls abspath as expected
            return os.path.join(self.agent.workspace_path, path_arg.lstrip(os.sep))

        mock_exists_patch = patch("os.path.exists", side_effect=lambda
            p: True if p == calculated_parent_dir else False)
        mock_isdir_patch = patch("os.path.isdir", side_effect=lambda
            p: False if p == calculated_parent_dir else True)

        with patch("os.path.abspath", side_effect=robust_abspath_side_effect), \
             mock_exists_patch as mock_exists, \
             mock_isdir_patch as mock_isdir, \
             patch("os.makedirs") as mock_makedirs: # makedirs should not be called

            result = await create_file(self.agent, target_file_argument, instructions, explanation)

            # Assert that the checks were made on the calculated parent directory
            mock_exists.assert_any_call(calculated_parent_dir)
            mock_isdir.assert_any_call(calculated_parent_dir) # This call will use the side_effect

            mock_makedirs.assert_not_called() # Because parent exists (even if it's a file)

            self.assertIn("error", result)
            expected_error_message = f"Cannot create file; parent path {calculated_parent_dir} exists but is not a directory."
            self.assertIn(expected_error_message, result["error"])
            self.assertFalse(result["success"])

    async def test_create_file_parent_dir_is_file(self):
        """Test create_file when a parent path exists but is a file."""
        test_file = "parent_is_a_file/new.txt"
        # This is the parent dir that will be calculated by create_file
        # and is intended to be mocked as a file.
        parent_dir_that_is_a_file = self.full_path("parent_is_a_file") # /test/workspace/parent_is_a_file
        instructions = {"content": "test"}
        explanation = "Test parent is file"

        def robust_abspath_side_effect(path_arg):
            if path_arg == self.agent.workspace_path: return self.agent.workspace_path
            if path_arg.startswith(self.agent.workspace_path): return path_arg
            return os.path.join(self.agent.workspace_path, path_arg.lstrip(os.sep))

        # Mock os.path.exists: parent_dir_that_is_a_file exists, the new file does not.
        mock_exists_patch = patch("os.path.exists",
                                  side_effect=lambda p: True if p == parent_dir_that_is_a_file else False)
        # Mock os.path.isdir: parent_dir_that_is_a_file is NOT a dir. Workspace root IS a dir.
        mock_isdir_patch = patch("os.path.isdir",
                                 side_effect=lambda p: False if p == parent_dir_that_is_a_file else (True if p == self.agent.workspace_path else True))

        with patch("os.path.abspath", side_effect=robust_abspath_side_effect), \
             mock_exists_patch as mock_exists, \
             mock_isdir_patch as mock_isdir, \
             patch("os.makedirs") as mock_makedirs:

            result = await create_file(self.agent, test_file, instructions, explanation)

            mock_exists.assert_any_call(parent_dir_that_is_a_file)
            mock_isdir.assert_any_call(parent_dir_that_is_a_file)
            mock_makedirs.assert_not_called()
            self.assertIn("error", result)
            self.assertIn(f"Cannot create file; parent path {parent_dir_that_is_a_file} exists but is not a directory.", result["error"])


if __name__ == "__main__":
    unittest.main()