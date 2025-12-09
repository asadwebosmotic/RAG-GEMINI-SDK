import logging
from typing import List, Dict, Any
import sys
import os

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from qdrant_client.http.models import Filter, FieldCondition, MatchValue
from RAG.embedding_and_store import client as qdrant_client, embed_model
from config import settings

logger = logging.getLogger(__name__)


async def rag_search(query: str, top_k: int = 5, user_id: str = "anonymous") -> Dict[str, Any]:
    """
    Search RAG collection for relevant chunks.
    
    Args:
        query: Search query
        top_k: Number of results to return
        user_id: User identifier for data isolation
    
    Returns:
        Dictionary with 'results', 'count', 'query', and 'embedding_tokens'
    """
    try:
        logger.info(f"Starting RAG search for query: '{query}' (user_id: {user_id})")
        
        # Generate query embedding and track tokens (rough estimation)
        query_embedding = embed_model.encode(query).tolist()
        # Estimate embedding tokens (rough calculation: ~4 chars per token)
        embedding_tokens = max(1, len(query) // 4)
        logger.info(f"Generated query embedding with {len(query_embedding)} dimensions (estimated {embedding_tokens} tokens)")
        
        # First try without user_id filter to see if any documents exist
        logger.info("Attempting search without user_id filter to check document availability...")
        import asyncio
        loop = asyncio.get_event_loop()
        all_results = await loop.run_in_executor(
            None,
            lambda: qdrant_client.search(
                collection_name="KnowMe_chunks",
                query_vector=query_embedding,
                limit=top_k
            )
        )
        
        logger.info(f"Found {len(all_results)} total results without user filter")
        
        # If no results at all, the collection might be empty or query issue
        if len(all_results) == 0:
            logger.warning("No results found in RAG collection at all - collection might be empty")
            return []
        
        # Try with user_id filter
        search_filter = Filter(
            must=[FieldCondition(key="user_id", match=MatchValue(value=user_id))]
        )
        
        logger.info(f"Searching RAG with user_id filter: '{user_id}'")
        
        # Qdrant search is synchronous, but we're in async context
        filtered_results = await loop.run_in_executor(
            None,
            lambda: qdrant_client.search(
                collection_name="KnowMe_chunks",
                query_vector=query_embedding,
                query_filter=search_filter,
                limit=top_k
            )
        )
        
        logger.info(f"Found {len(filtered_results)} results with user_id filter")
        
        # If filtered results are much fewer, log the available user_ids
        if len(filtered_results) < len(all_results):
            logger.warning(f"User filter reduced results from {len(all_results)} to {len(filtered_results)}")
            # Log sample user_ids from available documents
            sample_user_ids = set()
            for result in all_results[:5]:
                uid = result.payload.get("user_id", "no_user_id")
                sample_user_ids.add(uid)
            logger.warning(f"Available user_ids in sample: {sample_user_ids}")
        
        # Use filtered results if available, otherwise use all results
        results_to_use = filtered_results if len(filtered_results) > 0 else all_results
        logger.info(f"Using {len(results_to_use)} results for processing")
        
        # Format results
        formatted_results = []
        for result in results_to_use:
            formatted_results.append({
                "text": result.payload.get("text", ""),
                "page": result.payload.get("page", 1),
                "source": result.payload.get("source", "unknown"),
                "type": result.payload.get("type", "text"),
                "score": float(result.score)
            })
        
        logger.info(f"RAG search returned {len(formatted_results)} results for query: '{query}' (user_id: {user_id})")
        
        if len(formatted_results) == 0:
            logger.warning(f"No results found in RAG for query: '{query}' with user_id: '{user_id}'")
        else:
            logger.info(f"Top result score: {formatted_results[0]['score']:.4f}")
            logger.info(f"Top result source: {formatted_results[0]['source']}")
            logger.info(f"Top result preview: {formatted_results[0]['text'][:100]}...")

        # Filter by minimum score threshold
        MIN_RAG_SCORE = 0.75  # Increased threshold for better relevance
        filtered_results = [r for r in formatted_results if r["score"] >= MIN_RAG_SCORE]
        
        # Additional check: if top score is below 0.80, likely not relevant
        if filtered_results and filtered_results[0]["score"] < 0.80:
            logger.warning(f"Top RAG score ({filtered_results[0]['score']:.4f}) is below confidence threshold. Results may not be relevant.")
            # Return empty results to force web_search
            logger.info("Returning empty results due to low relevance score")
            return []
        
        # Check if results are generic/unhelpful content
        if filtered_results:
            top_result_text = filtered_results[0]["text"].lower().strip()
            query_lower = query.lower()
            
            # Only filter out generic content
            is_generic_content = (
                len(top_result_text) < 20 or 
                top_result_text in ["table:", "contact", "summary", "experience", "education"] or
                top_result_text.startswith("table:")
            )
            
            if is_generic_content:
                logger.warning(f"RAG results contain generic/unhelpful content: '{top_result_text[:50]}...'")
                logger.info("Returning empty results due to generic content")
                return []
        
        logger.info(f"Filtered results: {len(filtered_results)} (from {len(formatted_results)} total)")
        
        return {
            "results": filtered_results,
            "count": len(filtered_results),
            "query": query,
            "embedding_tokens": embedding_tokens
        }
    
    except Exception as e:
        logger.error(f"Error in RAG search: {e}")
        return {
            "results": [],
            "count": 0,
            "query": query,
            "embedding_tokens": 0
        }

