import os
import requests
import time
import re
from dotenv import load_dotenv
from utils.logging_config import log_info, log_error

load_dotenv()
TAVILY_API_KEY = os.getenv("TAVILY_API_KEY")
TAVILY_URL = "https://api.tavily.com/search"

ALLOWED_DOMAINS = {
    "math.stackexchange.com": "math.stackexchange",
    "mathoverflow.net": "mathoverflow",
    "reddit.com": "reddit"
}


def sanitize_query(text: str) -> str:
    """
    Cleans whitespace and removes non-ASCII characters to reduce API rejections.
    """
    text = re.sub(r"[\t\r\n]+", " ", text)
    text = re.sub(r"\s{2,}", " ", text)
    text = re.sub(r"[^\x20-\x7E]", "", text)  # remove non-printable / unicode chars
    return text.strip()


def query_tavily_search(problem_text, max_results=5, retries=3, delay=2):
    """
    Queries Tavily API and filters results to math-related domains.
    Retries on transient failure and logs minimal info.
    """
    if not TAVILY_API_KEY:
        raise EnvironmentError("Missing TAVILY_API_KEY in .env")

    query = sanitize_query(problem_text)

    log_info(f"🧪 Tavily query length: {len(query)} chars")

    headers = {
        "Authorization": f"Bearer {TAVILY_API_KEY}",
        "Content-Type": "application/json"
    }

    payload = {
        "query": query,
        "search_depth": "advanced",
        "include_answer": True
    }

    for attempt in range(1, retries + 1):
        try:
            log_info(f"🔍 Tavily request attempt {attempt}")
            response = requests.post(TAVILY_URL, headers=headers, json=payload, timeout=20)
            response.raise_for_status()
            break
        except requests.HTTPError as e:
            if e.response.status_code == 400:
                log_error("❌ Tavily 400 Bad Request")
                log_error(f"🚨 Query length at failure: {len(query)} chars")
            log_error(f"⚠️ Tavily attempt {attempt} failed", exception=e)
            if attempt < retries:
                time.sleep(delay * (2 ** (attempt - 1)))
            else:
                raise RuntimeError("❌ Tavily request failed after all retries") from e
        except requests.RequestException as e:
            log_error(f"⚠️ Tavily attempt {attempt} failed", exception=e)
            if attempt < retries:
                time.sleep(delay * (2 ** (attempt - 1)))
            else:
                raise RuntimeError("❌ Tavily request failed after all retries") from e

    try:
        data = response.json()
    except ValueError:
        raise RuntimeError("❌ Invalid JSON returned from Tavily")

    results = []
    for item in data.get("results", []):
        url = item.get("url", "")
        domain = url.split("/")[2] if "://" in url else ""

        for allowed in ALLOWED_DOMAINS:
            if allowed in domain:
                results.append({
                    "title": item.get("title", ""),
                    "content": item.get("content", ""),
                    "url": url,
                    "source": ALLOWED_DOMAINS[allowed]
                })
                break

        if len(results) >= max_results:
            break

    return results
