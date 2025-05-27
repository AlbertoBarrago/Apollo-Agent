"""
Web Search operations for the ApolloAgent.

This module contains functions for web search operations like web scraping,
search by keyword, and advanced search.

Author: Alberto Barrago
License: BSD 3-Clause License - 2025
"""

import requests
import time
import random
from bs4 import BeautifulSoup
from urllib.parse import quote_plus
from typing import Dict, Any

from apollo.config.const import Constant


async def web_search(search_query: str) -> Dict[str, Any]:
    """
    Performs a more robust web search for real-time information,
    using flexible selectors and rotating user-agents.

    Args:
        search_query (str): The search term.

    Returns:
        dict: A dictionary with the search results or an error message.
    """
    print(f"Starting search for: '{search_query}'")

    encoded_search_term = quote_plus(search_query)
    search_url = f"https://www.google.com/search?q={encoded_search_term}&num=10&hl=en"

    headers = {
        "User-Agent": random.choice(Constant.USER_AGENTS),
        "Accept": "text/html,application/xhtml+xml,application"
        "/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8",
        "Accept-Language": "en-US,en;q=0.9,it;q=0.8",
        "Referer": "https://www.google.com/",
        "DNT": "1",
        "Connection": "keep-alive",
        "Upgrade-Insecure-Requests": "1",
    }

    try:
        # Pause to avoid overwhelming the server
        time.sleep(random.uniform(1.0, 2.5))
        response = requests.get(search_url, headers=headers, timeout=15.0)
        response.raise_for_status()
        print(f"response -> {response}")
        soup = BeautifulSoup(response.text, "html.parser")
        results_list = []
        found_blocks = []

        # Try each block selector until it finds results.
        for selector in Constant.SEARCH_BLOCK_SELECTORS:
            found_blocks = soup.select(selector)
            if found_blocks:
                print(
                    f"Found {len(found_blocks)} blocks with the selector '{selector}'"
                )
                break

        if not found_blocks:
            message = (
                "No search blocks found. Google's HTML structure might have changed, "
                "or the page contains no organic results (e.g., only ads or maps)."
            )
            print(message)
            return {"query": search_query, "results": [], "message": message}

        for block in found_blocks:
            title_tag = block.select_one(Constant.TITLE_SELECTOR)
            link_tag = block.select_one(Constant.LINK_SELECTOR)

            # Try to extract the snippet with different selectors
            snippet_text = ""
            for snip_selector in Constant.SNIPPET_SELECTORS:
                snippet_tag = block.select_one(snip_selector)
                if snippet_tag and snippet_tag.text:
                    # Sometimes the snippet also contains the title; we clean it if necessary.
                    potential_snippet = snippet_tag.text.strip()
                    if title_tag and title_tag.text.strip() in potential_snippet:
                        potential_snippet = potential_snippet.replace(
                            title_tag.text.strip(), ""
                        ).strip()

                    if len(potential_snippet) > 10:
                        snippet_text = potential_snippet
                        break

            if not snippet_text:
                snippet_text = "No snippet available."

            title = title_tag.text.strip() if title_tag else "No Title Found"
            url = (
                link_tag["href"]
                if link_tag and "href" in link_tag.attrs
                else "No URL Found"
            )

            if url.startswith("http") and "google.com/search?q=" not in url:
                results_list.append(
                    {"title": title, "url": url, "snippet": snippet_text}
                )

        if not results_list:
            return {
                "query": search_query,
                "results": [],
                "message": "Blocks were found, but "
                "it was not possible to extract valid results.",
            }

        print(f"Search completed successfully. Extracted {len(results_list)} results.")
        return {"query": search_query, "results": results_list}

    except requests.exceptions.HTTPError as e:
        error_msg = (
            f"HTTP Error: {e}. You might have been temporarily blocked by Google."
        )
        print(error_msg)
        return {"query": search_query, "error": error_msg}
    except requests.exceptions.RequestException as e:
        error_msg = f"Network error during search: {e}."
        print(error_msg)
        return {"query": search_query, "error": error_msg}
    except SystemError as e:
        error_msg = f"An unexpected error occurred during page parsing: {e}."
        print(error_msg)
        return {"query": search_query, "error": error_msg}
