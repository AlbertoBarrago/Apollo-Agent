"""
Tool Web Search

This tool aims users to get a result from web search.

Author: Alberto Barrago
License: BSD 3-Clause License - 2024
"""

import requests
import time
import random
from bs4 import BeautifulSoup
from urllib.parse import quote_plus


def web_search(search_term: str) -> dict:
    """
    Search the web for real-time information about any topic by directly scraping Google.
    The search results will include relevant snippets and URLs from web pages.

    Args:
        search_term (str): The search term to look up on the web.
                           Be specific and include relevant keywords for better results.
                           For technical queries, include version numbers or dates if relevant.

    Returns:
        dict: A dictionary containing the search query and a list of search results.
              Each search result is a dictionary with 'title', 'url', and 'snippet'.
              Returns an error message if the search fails.
    """
    print(f"search_term -> ${search_term}")

    results_list = []
    # Encode the search term for the URL
    encoded_search_term = quote_plus(search_term)

    search_url = f"https://www.google.com/search?q={encoded_search_term}&num=5"  # num=5 for 5 results

    # Mimic a common browser User-Agent to reduce the chance of being blocked
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                      "AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36",
        "Accept-Language": "en-US,en;q=0.9",
        "Accept-Encoding": "gzip, deflate, br",
        "Accept": "text/html,application/xhtml+xml,"
                  "application/xml;q=0.9,image/avif,"
                  "image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.7",
        "DNT": "1",
        "Connection": "keep-alive"
    }

    try:
        # Add a random delay to be less aggressive and reduce blocking risk
        time.sleep(random.uniform(2, 5))

        response = requests.get(search_url, headers = headers, timeout=10.0)
        response.raise_for_status()  # Raise an exception for HTTP errors (4xx or 5xx)

        soup = BeautifulSoup(response.text, 'html.parser')

        # Google's HTML structure changes, so these selectors might need updates in the future.
        # Common selectors for search results:
        # div.g -> individual result block (older)
        # div.tF2Cxc -> main result block (newer, often contains title, link, snippet)
        # h3.LC20lb -> title
        # a -> link (inside tF2Cxc)
        # div.VwiC3b -> snippet
        search_results_blocks = soup.find_all('div', class_='tF2Cxc')

        if not search_results_blocks:
            search_results_blocks = soup.find_all('div', class_='g')

        for block in search_results_blocks[:5]:  # Ensure max 5 results
            title_tag = block.find('h3')
            link_tag = block.find('a')
            snippet_tag = block.find('div', class_='VwiC3b')  # or other common snippet classes like .IsZvec

            title = title_tag.text.strip() if title_tag else "No Title Found"
            url = link_tag['href'] if link_tag and 'href' in link_tag.attrs else "No URL Found"
            snippet = snippet_tag.text.strip() if snippet_tag else "No snippet available."

            # Filter out internal Google links or malformed URLs if necessary
            if url and not url.startswith("http://webcache.googleusercontent.com") and not url.startswith("/search?"):
                results_list.append({
                    "title": title,
                    "url": url,
                    "snippet": snippet
                })

            print(f"results_list -> ${results_list}")
            if len(results_list) >= 5:
                break

        if not results_list:
            return {
                "query": search_term,
                "results": [],
                "message": "No relevant search results found. "
                           "Google might have blocked the request or changed its HTML structure."
            }

        return {
            "query": search_term,
            "results": results_list
        }

    except requests.exceptions.RequestException as e:
        return {
            "query": search_term,
            "error": f"Network or HTTP error during web search: {e}. "
                     f"You might be rate-limited or blocked."
        }
    except Exception as e:
        return {
            "query": search_term,
            "error": f"An unexpected error occurred during web search: {e}. "
                     f"Google's HTML structure might have changed."
        }
