# /Users/albz/PycharmProjects/ApolloAgent/apollo/tools/web.py
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
            title_tag = result.select_one(".result__title")
            snippet_tag = result.select_one(".result__snippet")
            link_tag = result.select_one(".result__url")

            if title_tag and link_tag:
                results.append(
                    {
                        "title": title_tag.get_text(strip=True),
                        "url": link_tag.get("href"),
                        "snippet": (
                            snippet_tag.get_text(strip=True)
                            if snippet_tag
                            else "No snippet available."
                        ),
                    }
                )
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
        # Iterate over each search result a heading element
        for heading_element in soup.select(".mw-search-result-heading"):
            # The title and link are usually within an 'a' tag inside the heading
            link_anchor_tag = heading_element.select_one("a.mw-search-result-title")
            if not link_anchor_tag:  # Fallback if class is directly on 'a'
                link_anchor_tag = heading_element.select_one("a")

            if not link_anchor_tag:  # If still no anchor tag, skip this result
                continue

            title_text = link_anchor_tag.get_text(strip=True)
            link_url = link_anchor_tag.get("href")

            # The snippet is typically in a sibling div with class 'searchresult',
            # which then contains a 'p' tag with class 'mw-search-result-snippet'.
            snippet_to_store = "No snippet available."
            snippet_container_div = heading_element.find_next_sibling(
                "div", class_="searchresult"
            )
            if snippet_container_div:
                snippet_p_element = snippet_container_div.select_one(
                    "p.mw-search-result-snippet"
                )
                if snippet_p_element:  # This 'if' condition is what line 94 was about
                    snippet_to_store = snippet_p_element.get_text(strip=True)
                # Optional: Fallback if p.mw-search-result-snippet is not found, but div.searchresult is
                # elif snippet_container_div.get_text(strip=True):
                #     snippet_to_store = snippet_container_div.get_text(strip=True)

            results.append(
                {
                    "title": title_text,
                    "url": link_url,
                    "snippet": snippet_to_store,
                }
            )
        return results
