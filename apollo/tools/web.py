"""
Web Search operations for the ApolloAgent.

This module contains functions for web search operations like web scraping,
search by keyword, and advanced search.

Author: Alberto Barrago
License: BSD 3-Clause License - 2025
"""

import random
from typing import Dict, List
from urllib.parse import quote_plus

import httpx
from bs4 import BeautifulSoup

from apollo.config.const import Constant


async def web_search(query: str) -> List[Dict[str, str]]:
    """
    Fetches search results from DuckDuckGo using its HTML search page.

    This asynchronous function performs a search query on DuckDuckGo and parses the
    returned HTML for search results. Each search result includes the title of the
    result, its URL, and a snippet (if available). The function returns a list of
    such results structured as dictionaries.

    :param query: Str - Search query string to be sent to DuckDuckGo.
    :return: A list of dictionaries, where each dictionary contains 'title', 'url',
        and 'snippet' representing a search result.
    :rtype: List[Dict[str, str]]
    """
    url = f"https://html.duckduckgo.com/html/?q={quote_plus(query)}"
    headers = {
        "User-Agent": random.choice(Constant.user_agents),
    }

    async with httpx.AsyncClient(headers=headers, timeout=20.0) as client:
        resp = await client.get(url)
        soup = BeautifulSoup(resp.text, "html.parser")
        results = []

        for result in soup.select(".result"):
            title = result.select_one(".result__title")
            snippet = result.select_one(".result__snippet")
            link_tag = result.select_one(".result__url")

            if title and link_tag:
                results.append(
                    {
                        "title": title.get_text(strip=True),
                        "url": link_tag.get("href"),
                        "snippet": (
                            snippet.get_text(strip=True)
                            if snippet
                            else "No snippet available."
                        ),
                    }
                )
                # print(f"Result from web {results}")
        return results


async def wiki_search(query: str) -> List[Dict[str, str]]:
    """
    Fetches search results from Wikipedia for a given query string asynchronously.

    This function sends an HTTP GET request to the Wikipedia search page using the provided
    search query.
    It parses the HTML response to extract search result titles, URLs,
    and snippets.
    The extracted data is returned as a list of dictionaries, each containing
    the title, URL, and snippet of a result.

    :param query: Str - The query string to search for on Wikipedia.
    :return: A list of dictionaries containing titles, URLs, and snippets of the search results.
    :rtype: List[Dict[str, str]]
    """
    url = f"https://en.wikipedia.org/w/index.php?search={quote_plus(query)}"
    headers = {
        "User-Agent": random.choice(Constant.user_agents),
    }
    async with httpx.AsyncClient(headers=headers, timeout=20.0) as client:
        resp = await client.get(url)
        soup = BeautifulSoup(resp.text, "html.parser")
        results = []
        for result in soup.select(".mw-search-result-heading"):
            title = result.select_one(".mw-search-result-heading")
            snippet = result.select_one(".mw-search-result-snippet")
            link_tag = result.select_one(".mw-search-result-title a")
            if title and link_tag:
                results.append(
                    {
                        "title": title.get_text(strip=True),
                        "url": link_tag.get("href"),
                        "snippet": (
                            snippet.get_text(strip=True)
                            if snippet
                            else "No snippet available."
                        ),
                    }
                )
                # print(f"Result from web {results}")
        return results
