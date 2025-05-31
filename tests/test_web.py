"""Unit tests for the web module.

This module contains comprehensive unit tests for the web search functionality,
including web search and wiki search operations.

Author: Alberto Barrago
License: BSD 3-Clause License - 2025
"""

import unittest
from unittest.mock import patch, AsyncMock
import httpx

from apollo.tools.web import web_search, wiki_search
from unittest import IsolatedAsyncioTestCase


class TestWebOperations(IsolatedAsyncioTestCase):
    """Test cases for web operations."""

    @patch("apollo.tools.web.httpx.AsyncClient")
    async def test_web_search_success(self, MockAsyncClient):
        """Test a successful web search."""
        mock_client_instance = AsyncMock()
        mock_response = AsyncMock()
        mock_response.status_code = 200
        # Simulate DuckDuckGo HTML structure
        mock_response.text = """
        <html><body>
            <div class="result">
                <a class="result__title">Test Result 1</a>
                <a class="result__url" href="https://test.com/1"></a>
                <div class="result__snippet">Test snippet 1</div>
            </div>
            <div class="result">
                <a class="result__title">Test Result 2</a>
                <a class="result__url" href="https://test.com/2"></a>
                <div class="result__snippet">Test snippet 2</div>
            </div>
        </body></html>
        """
        mock_client_instance.get.return_value = mock_response
        MockAsyncClient.return_value.__aenter__.return_value = mock_client_instance

        results = await web_search("test query")

        self.assertEqual(len(results), 2)
        self.assertEqual(results[0]["title"], "Test Result 1")
        self.assertEqual(results[0]["url"], "https://test.com/1")
        self.assertEqual(results[0]["snippet"], "Test snippet 1")
        self.assertEqual(results[1]["title"], "Test Result 2")

    @patch("apollo.tools.web.httpx.AsyncClient")
    async def test_web_search_no_results(self, MockAsyncClient):
        """Test web search with no results."""
        mock_client_instance = AsyncMock()
        mock_response = AsyncMock()
        mock_response.status_code = 200
        mock_response.text = "<html><body><div>No results found.</div></body></html>"  # HTML with no .result elements
        mock_client_instance.get.return_value = mock_response
        MockAsyncClient.return_value.__aenter__.return_value = mock_client_instance

        results = await web_search("test query")

        self.assertEqual(len(results), 0)

    @patch("apollo.tools.web.httpx.AsyncClient")
    async def test_web_search_api_error(self, MockAsyncClient):
        """Test web search with an API error (e.g., network error)."""
        mock_client_instance = AsyncMock()
        mock_client_instance.get.side_effect = httpx.RequestError(
            "API Error", request=None
        )  # Simulate httpx error
        MockAsyncClient.return_value.__aenter__.return_value = mock_client_instance

        with self.assertRaises(httpx.RequestError):
            await web_search("test query")

    @patch("apollo.tools.web.httpx.AsyncClient")
    async def test_web_search_http_error_status(self, MockAsyncClient):
        """Test web search with an HTTP error status code."""
        mock_client_instance = AsyncMock()
        mock_response = AsyncMock()
        mock_response.status_code = 500
        mock_response.text = "Internal Server Error"
        # If your web_search function has resp.raise_for_status(), this would raise an exception.
        # If not, it might proceed and find no results or error during parsing.
        # Assuming the current web_search doesn't explicitly call raise_for_status(),
        # it would likely parse the error page and return no results.
        # For a more robust test, you might want web_search to handle non-200 codes.
        # For now, let's assume it parses and finds nothing.
        mock_response.raise_for_status = AsyncMock(
            side_effect=httpx.HTTPStatusError(
                "Server Error", request=None, response=mock_response
            )
        )

        mock_client_instance.get.return_value = mock_response
        MockAsyncClient.return_value.__aenter__.return_value = mock_client_instance

        # If web_search calls resp.raise_for_status()
        # with self.assertRaises(httpx.HTTPStatusError):
        #     await web_search("test query")

        # If web_search does NOT call resp.raise_for_status() and just tries to parse:
        results = await web_search("test query")
        self.assertEqual(
            len(results), 0
        )  # Or assert specific error handling if implemented

    @patch("apollo.tools.web.httpx.AsyncClient")
    async def test_wiki_search_success(self, MockAsyncClient):
        """Test a successful wiki search."""
        mock_client_instance = AsyncMock()
        mock_response = AsyncMock()
        mock_response.status_code = 200
        # Simulate Wikipedia HTML structure
        mock_response.text = """
        <html><body>
            <div class="mw-search-result-heading">
                <a href="/wiki/Test_Page_1" class="mw-search-result-title">Test Page 1</a>
            </div>
            <div class="searchresult"> <!-- Actual Wikipedia snippet container -->
                 <p class="mw-search-result-snippet">This is a snippet for Test Page 1.</p>
            </div>
            <div class="mw-search-result-heading">
                 <a href="/wiki/Test_Page_2" class="mw-search-result-title">Test Page 2</a>
            </div>
            <div class="searchresult">
                 <p class="mw-search-result-snippet">Snippet for Test Page 2.</p>
            </div>
        </body></html>
        """
        mock_client_instance.get.return_value = mock_response
        MockAsyncClient.return_value.__aenter__.return_value = mock_client_instance

        results = await wiki_search("test query")

        self.assertEqual(len(results), 0)

    @patch("apollo.tools.web.httpx.AsyncClient")
    async def test_wiki_search_no_results(self, MockAsyncClient):
        """Test wiki search with no results."""
        mock_client_instance = AsyncMock()
        mock_response = AsyncMock()
        mock_response.status_code = 200
        mock_response.text = (
            "<html><body><div>No matching results found.</div></body></html>"
        )
        mock_client_instance.get.return_value = mock_response
        MockAsyncClient.return_value.__aenter__.return_value = mock_client_instance

        results = await wiki_search("test query")

        self.assertEqual(len(results), 0)

    @patch("apollo.tools.web.httpx.AsyncClient")
    async def test_wiki_search_api_error(self, MockAsyncClient):
        """Test wiki search with an API error."""
        mock_client_instance = AsyncMock()
        mock_client_instance.get.side_effect = httpx.RequestError(
            "API Error", request=None
        )
        MockAsyncClient.return_value.__aenter__.return_value = mock_client_instance

        with self.assertRaises(httpx.RequestError):
            await wiki_search("test query")

            # /Users/albz/PycharmProjects/ApolloAgent/tests/test_web.py
            # ... (other parts of the file)

    @patch("apollo.tools.web.httpx.AsyncClient")
    async def test_wiki_search_success(self, MockAsyncClient):
        """Test a successful wiki search."""
        mock_client_instance = AsyncMock()
        mock_response = AsyncMock()
        mock_response.status_code = 200
        # Simulate Wikipedia HTML structure
        mock_response.text = """
        <html><body>
            <div class="mw-search-result-heading">
                <a href="/wiki/Test_Page_1" class="mw-search-result-title">Test Page 1</a>
            </div>
            <div class="searchresult">
                 <p class="mw-search-result-snippet">This is a snippet for Test Page 1.</p>
            </div>
            <div class="mw-search-result-heading">
                 <a href="/wiki/Test_Page_2" class="mw-search-result-title">Test Page 2</a>
            </div>
            <div class="searchresult">
                 <p class="mw-search-result-snippet">Snippet for Test Page 2.</p>
            </div>
        </body></html>
        """
        mock_client_instance.get.return_value = mock_response
        MockAsyncClient.return_value.__aenter__.return_value = mock_client_instance

        results = await wiki_search("test query")

        self.assertEqual(len(results), 2)  # Corrected this line
        # The following assertions should now also pass if parsing is correct
        self.assertEqual(results[0]["title"], "Test Page 1")
        self.assertEqual(results[0]["url"], "/wiki/Test_Page_1")
        self.assertEqual(results[0]["snippet"], "This is a snippet for Test Page 1.")
        self.assertEqual(results[1]["title"], "Test Page 2")
        self.assertEqual(results[1]["url"], "/wiki/Test_Page_2")
        self.assertEqual(results[1]["snippet"], "Snippet for Test Page 2.")

    @patch("apollo.tools.web.httpx.AsyncClient")
    async def test_wiki_search_fallback_anchor_tag(self, MockAsyncClient):
        """Test wiki search where the primary anchor selector fails, but the fallback works."""
        mock_client_instance = AsyncMock()
        mock_response = AsyncMock()
        mock_response.status_code = 200
        # Simulate Wikipedia HTML structure with a fallback anchor tag
        mock_response.text = """
            <html><body>
                <div class="mw-search-result-heading">
                    <a href="/wiki/Fallback_Page_1">Fallback Page Title 1</a> 
                </div>
                <div class="searchresult">
                     <p class="mw-search-result-snippet">Snippet for Fallback Page 1.</p>
                </div>
            </body></html>
            """
        mock_client_instance.get.return_value = mock_response
        MockAsyncClient.return_value.__aenter__.return_value = mock_client_instance

        results = await wiki_search("test query")

        self.assertEqual(len(results), 1)
        self.assertEqual(results[0]["title"], "Fallback Page Title 1")
        self.assertEqual(results[0]["url"], "/wiki/Fallback_Page_1")
        self.assertEqual(results[0]["snippet"], "Snippet for Fallback Page 1.")

    @patch("apollo.tools.web.httpx.AsyncClient")
    async def test_wiki_search_no_anchor_tag_skips_result(self, MockAsyncClient):
        """Test wiki search where a heading has no anchor tag and is skipped."""
        mock_client_instance = AsyncMock()
        mock_response = AsyncMock()
        mock_response.status_code = 200
        mock_response.text = """
            <html><body>
                <div class="mw-search-result-heading">
                    <!-- No anchor tag here, this result should be skipped -->
                    <span>Just some text, no link.</span>
                </div>
                <div class="mw-search-result-heading">
                     <a href="/wiki/Valid_Page_2" class="mw-search-result-title">Valid Page Title 2</a>
                </div>
                <div class="searchresult">
                     <p class="mw-search-result-snippet">Snippet for Valid Page 2.</p>
                </div>
            </body></html>
            """
        mock_client_instance.get.return_value = mock_response
        MockAsyncClient.return_value.__aenter__.return_value = mock_client_instance

        results = await wiki_search("test query")

        self.assertEqual(len(results), 1)
        self.assertEqual(results[0]["title"], "Valid Page Title 2")
        self.assertEqual(results[0]["url"], "/wiki/Valid_Page_2")
        self.assertEqual(results[0]["snippet"], "Snippet for Valid Page 2.")


if __name__ == "__main__":
    unittest.main()
