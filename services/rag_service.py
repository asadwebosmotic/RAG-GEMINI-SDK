import logging
from typing import List, Dict
import sys
import os

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from qdrant_client import QdrantClient
from qdrant_client.http.models import Filter, FieldCondition, MatchValue
from sentence_transformers import SentenceTransformer
from config import settings

logger = logging.getLogger(__name__)

# Initialize clients
qdrant_client = QdrantClient(host=settings.QDRANT_HOST, port=settings.QDRANT_PORT)
embed_model = SentenceTransformer("intfloat/e5-base-v2")


async def rag_search(query: str, top_k: int = 5, user_id: str = "anonymous") -> List[Dict]:
    """
    Search RAG collection for relevant chunks.
    
    Args:
        query: Search query
        top_k: Number of results to return
        user_id: User identifier for data isolation
    
    Returns:
        List of dictionaries with 'text', 'page', 'source', 'type', 'score'
    """
    try:
        # Generate query embedding
        query_embedding = embed_model.encode(query).tolist()
        
        # Search Qdrant with user filter
        search_filter = Filter(
            must=[FieldCondition(key="user_id", match=MatchValue(value=user_id))]
        ) if user_id != "anonymous" else None
        
        # Qdrant search is synchronous, but we're in async context
        # In production, consider using async Qdrant client if available
        import asyncio
        loop = asyncio.get_event_loop()
        results = await loop.run_in_executor(
            None,
            lambda: qdrant_client.search(
                collection_name="KnowMe_chunks",
                query_vector=query_embedding,
                query_filter=search_filter,
                limit=top_k
            )
        )
        
        # Format results
        formatted_results = []
        for result in results:
            formatted_results.append({
                "text": result.payload.get("text", ""),
                "page": result.payload.get("page", 1),
                "source": result.payload.get("source", "unknown"),
                "type": result.payload.get("type", "text"),
                "score": float(result.score)
            })
        
        logger.info(f"RAG search returned {len(formatted_results)} results for query: {query[:50]}")
        return formatted_results
    
    except Exception as e:
        logger.error(f"Error in RAG search: {e}")
        return []

