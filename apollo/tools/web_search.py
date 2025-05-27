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


async def web_search(search_query: str) -> List[Dict[str, str]]:
    """
    Fetches search results from DuckDuckGo using its HTML search page.

    This asynchronous function performs a search query on DuckDuckGo and parses the
    returned HTML for search results. Each search result includes the title of the
    result, its URL, and a snippet (if available). The function returns a list of
    such results structured as dictionaries.

    :param search_query: Search query string to be sent to DuckDuckGo.
    :type search_query: Str
    :return: A list of dictionaries, where each dictionary contains 'title', 'url',
        and 'snippet' representing a search result.
    :rtype: List[Dict[str, str]]
    """
    url = f"https://html.duckduckgo.com/html/?q={quote_plus(search_query)}"
    headers = {
        "User-Agent": random.choice(Constant.USER_AGENTS),
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
                results.append({
                    "title": title.get_text(strip=True),
                    "url": link_tag.get("href"),
                    "snippet": snippet.get_text(strip=True) if snippet else "No snippet available."
                })
        return results


