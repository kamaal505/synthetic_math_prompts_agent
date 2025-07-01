import os
import requests
import time
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


def query_tavily_search(problem_text, max_results=5, retries=3, delay=2):
    """
    Queries Tavily API and filters results to math-related domains.
    Retries on transient failure, and logs only minimal info.
    """
    if not TAVILY_API_KEY:
        raise EnvironmentError("Missing TAVILY_API_KEY in .env")

    query = " ".join(problem_text.strip().split())  # sanitize whitespace
    log_info("🔍 Tavily query sent.")

    headers = {
        "Authorization": f"Bearer {TAVILY_API_KEY}",
        "Content-Type": "application/json"
    }

    payload = {
        "query": query,
        "search_depth": "advanced",
        "include_answer": True  # ✅ enables full question body
    }

    for attempt in range(1, retries + 1):
        try:
            response = requests.post(TAVILY_URL, headers=headers, json=payload, timeout=10)
            response.raise_for_status()
            break
        except requests.RequestException as e:
            log_error(f"⚠️ Tavily attempt {attempt} failed", exception=e)
            if attempt < retries:
                time.sleep(delay)
            else:
                raise

    data = response.json()

    results = []
    for item in data.get("results", []):
        url = item.get("url", "")
        domain = url.split("/")[2] if "://" in url else ""

        for allowed in ALLOWED_DOMAINS:
            if allowed in domain:
                results.append({
                    "title": item.get("title", ""),
                    "content": item.get("content", ""),  # ✅ use full content field
                    "url": url,
                    "source": ALLOWED_DOMAINS[allowed]
                })
                break

        if len(results) >= max_results:
            break

    return results
