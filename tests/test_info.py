"""Unit tests for info.py

This module contains info about apollo for terminal use only.

Author: Alberto Barrago
License: BSD 3-Clause License - 2025
"""

import unittest
from unittest.mock import patch, call
import apollo.info


class TestGetVersionInfo(unittest.TestCase):
    """Tests for the get_version_info function."""

    @patch("apollo.info.__version__", "0.1.0-test")
    @patch("apollo.info.__title__", "TestApollo")
    @patch("apollo.info.__description__", "A test description.")
    @patch("apollo.info.__author__", "Test Author")
    @patch("apollo.info.__author_email__", "test@example.com")
    @patch("apollo.info.__license__", "Test License")
    @patch("apollo.info.__copyright__", "Copyright Test Year")
    @patch("apollo.info.__repository__", "http://test.repo")
    @patch("apollo.info.__keywords__", ["test", "mock"])
    @patch("apollo.info.__status__", "Testing")
    @patch("apollo.info.__requires__", ["mock_dep1", "mock_dep2"])
    @patch("apollo.info.__python_requires__", ">=3.0")
    def test_returns_correct_dictionary_structure_and_content(self):
        """
        Test that get_version_info returns a dictionary with all expected
        keys and correct (mocked) values.
        """
        expected_info = {
            "name": "TestApollo",
            "version": "0.1.0-test",
            "description": "A test description.",
            "author": "Test Author",
            "author_email": "test@example.com",
            "license": "Test License",
            "copyright": "Copyright Test Year",
            "repository": "http://test.repo",
            "keywords": ["test", "mock"],
            "status": "Testing",
            "dependencies": ["mock_dep1", "mock_dep2"],
            "python_requires": ">=3.0",
        }

        actual_info = apollo.info.get_version_info()

        self.assertIsInstance(actual_info, dict)
        self.assertEqual(actual_info, expected_info)


class TestPrintVersionInfo(unittest.TestCase):
    """Tests for the print_version_info function."""

    def setUp(self):
        """Prepare mock data that get_version_info would return."""
        self.mock_info_data = {
            "name": "SampleApp",
            "version": "1.0.0",
            "description": "This is a sample app.",
            "author": "Sample Author",
            "author_email": "sample@example.com",
            "license": "MIT",
            "status": "Stable",
            "repository": "sample/repo",
            "dependencies": ["depA", "depB"],
            "python_requires": ">=3.6",
            "copyright": "Copyright 2024 Sample Author",
            "keywords": ["sample", "app"],
        }

    @patch("apollo.info.get_version_info")
    @patch("builtins.print")
    def test_prints_standard_format_correctly(self, mock_print, mock_get_info):
        """Test the standard (non-JSON) output format."""
        mock_get_info.return_value = self.mock_info_data

        apollo.info.print_version_info(print_json=False)

        mock_get_info.assert_called_once()

        expected_print_calls = [
            call("SampleApp v1.0.0"),
            call("Description: This is a sample app."),
            call("Author: Sample Author <sample@example.com>"),
            call("License: MIT"),
            call("Status: Stable"),
            call("Repository: sample/repo"),
            call("\nDependencies:"),
            call("  - depA"),
            call("  - depB"),
            call("\nRequires Python >=3.6"),
        ]
        # This checks if all expected calls were made, in the exact order.
        self.assertEqual(mock_print.call_args_list, expected_print_calls)

    @patch("apollo.info.get_version_info")
    @patch("apollo.info.json.dumps")
    @patch("builtins.print")
    def test_prints_json_format_correctly(
        self, mock_print, mock_json_dumps, mock_get_info
    ):
        """Test the JSON output format."""
        mock_get_info.return_value = self.mock_info_data
        # Let json.dumps behave normally, but we can check its input
        # Or, to be more explicit about what print receives:
        mock_json_dumps.return_value = '{"mocked_json": true}'

        apollo.info.print_version_info(print_json=True)

        mock_get_info.assert_called_once()
        mock_json_dumps.assert_called_once_with(self.mock_info_data, indent=2)
        mock_print.assert_called_once_with('{"mocked_json": true}')


if __name__ == "__main__":
    unittest.main()
