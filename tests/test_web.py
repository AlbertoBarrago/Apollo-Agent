"""Unit tests for the web module.

This module contains comprehensive unit tests for the web search functionality,
including web search and wiki search operations.

Author: Alberto Barrago
License: BSD 3-Clause License - 2025
"""

import unittest
from unittest.mock import patch, MagicMock
from apollo.tools.web import web_search, wiki_search


class TestWebOperations(unittest.TestCase):
    """Test cases for web operations."""

    def setUp(self):
        """Set up test fixtures."""
        self.agent = MagicMock()

    @patch("requests.get")
    async def test_web_search_success(self, mock_get):
        """Test successful web search."""
        mock_response = MagicMock()
        mock_response.json.return_value = {
            "items": [
                {
                    "title": "Test Result",
                    "link": "https://test.com",
                    "snippet": "Test snippet",
                }
            ]
        }
        mock_get.return_value = mock_response

        result = await web_search(self.agent, "test query")

        self.assertTrue(result["success"])
        self.assertEqual(len(result["results"]), 1)
        self.assertEqual(result["results"][0]["title"], "Test Result")

    @patch("requests.get")
    async def test_web_search_no_results(self, mock_get):
        """Test web search with no results."""
        mock_response = MagicMock()
        mock_response.json.return_value = {"items": []}
        mock_get.return_value = mock_response

        result = await web_search(self.agent, "test query")

        self.assertTrue(result["success"])
        self.assertEqual(len(result["results"]), 0)

    @patch("requests.get")
    async def test_web_search_api_error(self, mock_get):
        """Test web search with API error."""
        mock_get.side_effect = Exception("API Error")

        result = await web_search(self.agent, "test query")

        self.assertFalse(result["success"])
        self.assertIn("error", result)

    @patch("requests.get")
    async def test_web_search_invalid_response(self, mock_get):
        """Test web search with invalid API response."""
        mock_response = MagicMock()
        mock_response.json.return_value = {"invalid": "response"}
        mock_get.return_value = mock_response

        result = await web_search(self.agent, "test query")

        self.assertFalse(result["success"])
        self.assertIn("error", result)

    @patch("wikipedia.search")
    @patch("wikipedia.summary")
    async def test_wiki_search_success(self, mock_summary, mock_search):
        """Test successful wiki search."""
        mock_search.return_value = ["Test Page"]
        mock_summary.return_value = "Test summary"

        result = await wiki_search(self.agent, "test query")

        self.assertTrue(result["success"])
        self.assertEqual(len(result["results"]), 1)
        self.assertEqual(result["results"][0]["title"], "Test Page")
        self.assertEqual(result["results"][0]["summary"], "Test summary")

    @patch("wikipedia.search")
    async def test_wiki_search_no_results(self, mock_search):
        """Test wiki search with no results."""
        mock_search.return_value = []

        result = await wiki_search(self.agent, "test query")

        self.assertTrue(result["success"])
        self.assertEqual(len(result["results"]), 0)

    @patch("wikipedia.search")
    async def test_wiki_search_error(self, mock_search):
        """Test wiki search with error."""
        mock_search.side_effect = Exception("Wiki Error")

        result = await wiki_search(self.agent, "test query")

        self.assertFalse(result["success"])
        self.assertIn("error", result)

    @patch("wikipedia.search")
    @patch("wikipedia.summary")
    async def test_wiki_search_summary_error(self, mock_summary, mock_search):
        """Test wiki search with summary fetch error."""
        mock_search.return_value = ["Test Page"]
        mock_summary.side_effect = Exception("Summary Error")

        result = await wiki_search(self.agent, "test query")

        self.assertTrue(result["success"])
        self.assertEqual(len(result["results"]), 1)
        self.assertEqual(result["results"][0]["title"], "Test Page")
        self.assertIn("error", result["results"][0]["summary"])


if __name__ == "__main__":
    unittest.main()
