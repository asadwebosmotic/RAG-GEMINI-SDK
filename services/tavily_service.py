import logging
from typing import Dict, Optional
from tavily import TavilyClient
from config import settings
from core.dependencies import get_cache

logger = logging.getLogger(__name__)

tavily_client = TavilyClient(api_key=settings.TAVILY_API_KEY)


async def web_search(query: str, depth: str = "basic") -> Dict:
    """
    Search the web using Tavily API with caching.
    
    Args:
        query: Search query
        depth: Search depth ("basic" or "advanced")
    
    Returns:
        Dictionary with search results
    """
    cache = get_cache()
    cache_key = f"tavily:{query}:{depth}"
    
    # Check cache
    cached_result = None
    if isinstance(cache, dict):
        cached_result = cache.get(cache_key)
    elif hasattr(cache, 'get'):
        cached_result = cache.get(cache_key)
        if isinstance(cached_result, str):
            try:
                import json
                cached_result = json.loads(cached_result)
            except:
                cached_result = None
    
    if cached_result:
        logger.info(f"Returning cached Tavily result for: {query}")
        return cached_result
    
    try:
        # Perform search
        search_depth = "advanced" if depth == "advanced" else "basic"
        response = tavily_client.search(
            query=query,
            search_depth=search_depth,
            max_results=5
        )
        
        result = {
            "query": query,
            "results": response.get("results", []),
            "answer": response.get("answer", ""),
            "response_time": response.get("response_time", 0)
        }
        
        # Cache result
        if isinstance(cache, dict):
            cache[cache_key] = result
        elif hasattr(cache, 'setex'):
            import json
            cache.setex(cache_key, settings.TAVILY_CACHE_TTL, json.dumps(result))
        
        logger.info(f"Tavily search completed for: {query}")
        return result
    
    except Exception as e:
        logger.error(f"Error in Tavily search: {e}")
        return {
            "query": query,
            "results": [],
            "answer": f"Error performing search: {str(e)}",
            "response_time": 0
        }

