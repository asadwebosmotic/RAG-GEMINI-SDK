import logging
from typing import Dict
from tavily import TavilyClient
from config import settings

logger = logging.getLogger(__name__)

# Initialize Tavily client
tavily_client = TavilyClient(api_key=settings.TAVILY_API_KEY)


async def web_search(query: str, depth: str = "basic") -> Dict:
    """
    Perform Tavily web search without caching.

    Args:
        query: Search keyword
        depth: "basic" or "advanced"

    Returns:
        Dict containing search results
    """

    try:
        search_depth = "advanced" if depth == "advanced" else "basic"

        response = tavily_client.search(
            query=query,
            search_depth=search_depth,
            max_results=5,
        )

        result = {
            "query": query,
            "results": response.get("results", []),
            "answer": response.get("answer", ""),
            "response_time": response.get("response_time", 0),
        }

        logger.info(f"Tavily search completed for: {query}")
        return result

    except Exception as e:
        logger.error(f"Error in Tavily search: {e}")
        return {
            "query": query,
            "results": [],
            "answer": f"Error performing search: {str(e)}",
            "response_time": 0,
        }
