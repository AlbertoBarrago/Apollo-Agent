"""Unit tests for the version module information

This module contains version informations and metadata about ApolloAgent,


Author: Alberto Barrago
License: BSD 3-Clause License - 2025
"""

import unittest
from apollo import version


class TestVersion(unittest.TestCase):
    """Test cases for version information"""

    def test_case_string_exist_and_is_string(self):
        self.assertTrue(hasattr(version, "__version__"))
        self.assertIsInstance(version.__version__, str)

    def test_title_exist_and_is_string(self):
        self.assertTrue(hasattr(version, "__title__"))
        self.assertIsInstance(version.__title__, str)

    def test_description_exists_and_is_string(self):
        self.assertTrue(hasattr(version, "__description__"))
        self.assertIsInstance(version.__description__, str)
        self.assertEqual(
            version.__description__,
            "A custom AI agent that implements various functions for code assistance",
        )

    def test_author_exists_and_is_string(self):
        """Test that __author__ exists and is a string."""
        self.assertTrue(hasattr(version, "__author__"))
        self.assertIsInstance(version.__author__, str)
        self.assertEqual(version.__author__, "Alberto Barrago")

    def test_author_email_exists_and_is_string(self):
        """Test that __author_email__ exists and is a string."""
        self.assertTrue(hasattr(version, "__author_email__"))
        self.assertIsInstance(version.__author_email__, str)
        self.assertEqual(version.__author_email__, "albertobarrago@gmail.com")

    def test_license_exists_and_is_string(self):
        """Test that __license__ exists and is a string."""
        self.assertTrue(hasattr(version, "__license__"))
        self.assertIsInstance(version.__license__, str)
        self.assertEqual(version.__license__, "BSD 3-Clause License")

    def test_copyright_exists_and_is_string(self):
        """Test that __copyright__ exists and is a string."""
        self.assertTrue(hasattr(version, "__copyright__"))
        self.assertIsInstance(version.__copyright__, str)
        self.assertEqual(version.__copyright__, "Copyright 2025 Alberto Barrago")

    def test_repository_exists_and_is_string(self):
        """Test that __repository__ exists and is a string."""
        self.assertTrue(hasattr(version, "__repository__"))
        self.assertIsInstance(version.__repository__, str)
        self.assertEqual(
            version.__repository__, "https://github.com/AlbertoBarrago/Apollo-Agent"
        )

    def test_keywords_exists_and_is_list_of_strings(self):
        """Test that __keywords__ exists, is a list, and contains strings."""
        self.assertTrue(hasattr(version, "__keywords__"))
        self.assertIsInstance(version.__keywords__, list)
        self.assertGreater(
            len(version.__keywords__), 0, "Keywords list should not be empty"
        )
        for keyword in version.__keywords__:
            self.assertIsInstance(keyword, str)
        self.assertEqual(
            version.__keywords__,
            ["ai", "agent", "code-assistant", "llm", "ollama"],
        )

    def test_status_exists_and_is_string(self):
        """Test that __status__ exists and is a string."""
        self.assertTrue(hasattr(version, "__status__"))
        self.assertIsInstance(version.__status__, str)
        self.assertEqual(version.__status__, "Development")

    def test_requires_exists_and_is_list_of_strings(self):
        """Test that __requires__ exists, is a list, and contains strings."""
        self.assertTrue(hasattr(version, "__requires__"))
        self.assertIsInstance(version.__requires__, list)
        self.assertGreater(
            len(version.__requires__), 0, "Requires list should not be empty"
        )
        for req in version.__requires__:
            self.assertIsInstance(req, str)
        # Note: The duplicate "requests" in your original list is preserved here.
        # You might want to remove the duplicate from apollo/version.py.
        self.assertEqual(
            version.__requires__,
            [
                "requests",
                "ollama",
                "beautifulsoup4",
                "requests",  # Duplicate
                "python-dotenv",
                "httpx",
                "setuptools",
            ],
        )

    def test_python_requires_exists_and_is_string(self):
        """Test that __python_requires__ exists and is a string."""
        self.assertTrue(hasattr(version, "__python_requires__"))
        self.assertIsInstance(version.__python_requires__, str)
        self.assertEqual(version.__python_requires__, ">=3.8")

    if __name__ == "__main__":
        unittest.main()
