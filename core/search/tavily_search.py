import logging
import re
import time
from typing import Any, Dict, List

import requests

from utils.config_manager import get_config_manager
from utils.exceptions import APIError

# Get logger for this module
logger = logging.getLogger(__name__)

TAVILY_URL = "https://api.tavily.com/search"

ALLOWED_DOMAINS = {
    "math.stackexchange.com": "math.stackexchange",
    "mathoverflow.net": "mathoverflow",
    "reddit.com": "reddit",
}


def sanitize_query(text: str) -> str:
    """
    Cleans whitespace and removes non-ASCII characters to reduce API rejections.
    """
    text = re.sub(r"[\t\r\n]+", " ", text)
    text = re.sub(r"\s{2,}", " ", text)
    text = re.sub(r"[^\x20-\x7E]", "", text)  # remove non-printable / unicode chars
    return text.strip()


def query_tavily_search(
    problem_text: str, max_results: int = 5, retries: int = 3, delay: float = 2.0
) -> List[Dict[str, Any]]:
    """
    Queries Tavily API and filters results to math-related domains.
    Retries on transient failure and logs minimal info.

    Args:
        problem_text: The math problem text to search for
        max_results: Maximum number of results to return
        retries: Number of retry attempts on failure
        delay: Base delay between retries in seconds

    Returns:
        List of dictionaries containing search results

    Raises:
        APIError: If API key is missing or requests fail
    """
    config_manager = get_config_manager()
    tavily_api_key = config_manager.get_api_key("tavily")

    if not tavily_api_key:
        raise APIError("Missing TAVILY_API_KEY", api_name="Tavily")

    query = sanitize_query(problem_text)
    logger.info(f"🧪 Tavily query length: {len(query)} chars")

    headers = {
        "Authorization": f"Bearer {tavily_api_key}",
        "Content-Type": "application/json",
    }

    payload = {"query": query, "search_depth": "advanced", "include_answer": True}

    for attempt in range(1, retries + 1):
        try:
            logger.info(f"🔍 Tavily request attempt {attempt}")
            response = requests.post(
                TAVILY_URL, headers=headers, json=payload, timeout=20
            )
            response.raise_for_status()
            break
        except requests.HTTPError as e:
            if e.response.status_code == 400:
                logger.error("❌ Tavily 400 Bad Request")
                logger.error(f"🚨 Query length at failure: {len(query)} chars")
            logger.warning(f"⚠️ Tavily attempt {attempt} failed: {str(e)}")
            if attempt < retries:
                sleep_time = delay * (2 ** (attempt - 1))
                time.sleep(sleep_time)
            else:
                raise APIError(
                    "❌ Tavily request failed after all retries",
                    api_name="Tavily",
                    status_code=getattr(e.response, "status_code", None),
                ) from e
        except requests.RequestException as e:
            logger.warning(f"⚠️ Tavily attempt {attempt} failed: {str(e)}")
            if attempt < retries:
                sleep_time = delay * (2 ** (attempt - 1))
                time.sleep(sleep_time)
            else:
                raise APIError(
                    "❌ Tavily request failed after all retries", api_name="Tavily"
                ) from e

    try:
        data = response.json()
    except ValueError as e:
        raise APIError("❌ Invalid JSON returned from Tavily", api_name="Tavily") from e

    results = []
    for item in data.get("results", []):
        url = item.get("url", "")
        domain = url.split("/")[2] if "://" in url else ""

        for allowed in ALLOWED_DOMAINS:
            if allowed in domain:
                results.append(
                    {
                        "title": item.get("title", ""),
                        "content": item.get("content", ""),
                        "url": url,
                        "source": ALLOWED_DOMAINS[allowed],
                    }
                )
                break

        if len(results) >= max_results:
            break

    logger.info(f"✅ Retrieved {len(results)} relevant documents from Tavily")
    return results
