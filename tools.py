import requests
from bs4 import BeautifulSoup
from pathlib import Path

# --- Tool definitions for the API ---

web_search_tool = {
    "name": "web_search",
    "description": "Search the web for information on a topic. Returns a list of search results with titles, URLs, and snippets. Use when you need to find pages about a topic before fetching them.",
    "input_schema": {
        "type": "object",
        "properties": {
            "query": {
                "type": "string",
                "description": "The search query. Be specific. 3-6 words usually works best.",
            }
        },
        "required": ["query"],
    },
}

fetch_url_tool = {
    "name": "fetch_url",
    "description": "Fetch and extract the readable text content of a web page given its URL. Use after web_search to read the full content of a promising result.",
    "input_schema": {
        "type": "object",
        "properties": {
            "url": {
                "type": "string",
                "description": "The full URL to fetch (including https://).",
            }
        },
        "required": ["url"],
    },
}

save_note_tool = {
    "name": "save_note",
    "description": "Save a research note for later use in the final report. Use this whenever you find a useful fact, statistic, or quote during research.",
    "input_schema": {
        "type": "object",
        "properties": {
            "topic": {
                "type": "string",
                "description": "Short tag for what the note is about (e.g. 'market_size', 'key_player_zomato').",
            },
            "content": {
                "type": "string",
                "description": "The actual note text. Include the source URL if relevant.",
            },
        },
        "required": ["topic", "content"],
    },
}

ALL_TOOLS = [web_search_tool, fetch_url_tool, save_note_tool]


# --- Tool implementations ---

def web_search(query: str) -> dict:
    """
    Stub web search. Returns hand-curated 'results' for common q-commerce queries.
    In production: swap with Brave Search / Tavily / SerpAPI.
    """
    # Mock results — pretend these came from a real search engine
    fake_results = {
        "default": [
            {
                "title": "Quick commerce in India: A 2024 retrospective",
                "url": "https://example.com/q-commerce-india-2024",
                "snippet": "India's quick commerce market crossed $5B in GMV in 2024, with Blinkit, Zepto, and Instamart as the dominant players.",
            },
            {
                "title": "Zepto raises $665M at $5B valuation",
                "url": "https://example.com/zepto-funding-2024",
                "snippet": "Zepto's latest round reflects investor confidence in the dark store model despite high cash burn.",
            },
            {
                "title": "Why quick commerce works in India but failed in the US",
                "url": "https://example.com/q-commerce-geography",
                "snippet": "Population density, low labor costs, and existing kirana ecosystems explain India's q-commerce success.",
            },
        ]
    }
    
    # Match the query loosely against any of these
    query_lower = query.lower()
    if any(term in query_lower for term in ["q-commerce", "quick commerce", "dark store", "blinkit", "zepto"]):
        return {
        "query": query,
        "results": [
            f"[SOURCE: {r['url']}] {r['title']} — {r['snippet']}"
            for r in fake_results["default"]
        ]
    }
    
    # If the query doesn't match, return an empty list (this is realistic — most searches don't hit gold)
    if not results:
        return {
            "query": query,
            "results": [],
            "instruction_to_agent": (
                "No sources found for this query. You must NOT answer this aspect "
                "of the user's question from general knowledge. Either rephrase and "
                "try a different search, or explicitly tell the user this aspect "
                "cannot be addressed from available sources."
            )
        }

def fetch_url(url: str) -> dict:
    """
    Fetch a URL and return cleaned text. For our fake URLs, return canned content.
    For real URLs, do an actual HTTP fetch.
    """
    # Mock content for our example URLs
    fake_pages = {
        "https://example.com/q-commerce-india-2024": """
            India's quick commerce sector experienced rapid expansion in 2024.
            The total GMV crossed $5 billion, up from $2.8B in 2023 — a 78% year-over-year increase.
            
            Key players by market share:
            - Blinkit (Zomato): ~40% market share
            - Zepto: ~30%
            - Instamart (Swiggy): ~25%
            - Others: ~5%
            
            Average order values range from INR 400-500 across players, with Blinkit reporting the highest AOV.
            Dark store density in metros exceeds 1 store per 1.5 square kilometers in saturated zones like South Bombay.
        """,
        "https://example.com/zepto-funding-2024": """
            Zepto raised $665 million in its 2024 round at a $5 billion valuation.
            The company reports 25 million orders per month across 350+ dark stores.
            Founded by Aadit Palicha and Kaivalya Vohra in 2021, Zepto operates in 10+ Indian cities.
            Their unit economics show contribution margin positive in mature dark stores after 18 months.
        """,
        "https://example.com/q-commerce-geography": """
            Quick commerce has thrived in India because of three structural factors:
            1. Population density: Indian metros have 30,000+ people per square kilometer in core areas
            2. Labor cost: Delivery riders earn INR 25,000-40,000 per month — sustainable unit economics
            3. Kirana coexistence: Q-commerce competes with kirana on convenience, not price
            
            In contrast, US attempts (Gopuff, Jokr, Fridge No More) failed because of:
            - Lower density making dark store networks uneconomical
            - Higher labor costs per delivery
            - Strong incumbent grocery delivery (Instacart, Amazon Fresh) for non-immediate needs
        """,
    }
    
    if url in fake_pages:
        return {
            "url": url,
            "content": f"[SOURCE URL: {url}]\n\n{fake_pages[url].strip()}\n\n[END SOURCE]"
        }
    
    # For real URLs, attempt an actual fetch
    try:
        response = requests.get(url, timeout=10, headers={"User-Agent": "research-agent/1.0"})
        response.raise_for_status()
        soup = BeautifulSoup(response.text, "html.parser")
        # Strip scripts, styles, and other non-content elements
        for element in soup(["script", "style", "nav", "footer", "header"]):
            element.decompose()
        text = soup.get_text(separator="\n", strip=True)
        # Truncate to a reasonable length
        return {"url": url, "content": text[:5000]}
    except Exception as e:
        return {"url": url, "error": f"Could not fetch: {str(e)}"}


def save_note(topic: str, content: str) -> dict:
    """Append a note to a local notes file."""
    Path("notes").mkdir(exist_ok=True)
    notes_file = Path("notes/research.md")
    
    with notes_file.open("a") as f:
        f.write(f"\n## {topic}\n\n{content}\n")
    
    return {"status": "saved", "topic": topic, "file": str(notes_file)}


# --- Dispatch map ---
TOOL_FUNCTIONS = {
    "web_search": lambda args: web_search(args["query"]),
    "fetch_url": lambda args: fetch_url(args["url"]),
    "save_note": lambda args: save_note(args["topic"], args["content"]),
}

