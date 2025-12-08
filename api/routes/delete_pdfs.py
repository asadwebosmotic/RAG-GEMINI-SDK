from fastapi import APIRouter, HTTPException
from typing import Dict
import os
from qdrant_client import QdrantClient
from qdrant_client.http import models
from qdrant_client.http.models import Filter, FieldCondition, MatchValue

router = APIRouter()
client = QdrantClient()

@router.delete("/pdfs/{pdf_name}")
async def delete_pdf(pdf_name: str, user_id: str = "anonymous") -> Dict[str, str]:
    """
    Delete a PDF's associated chunks from Qdrant by its original filename.
    """
    try:
        # Normalize pdf_name (remove path prefixes, ensure consistent extension)
        pdf_name = os.path.basename(pdf_name.strip())
        if not pdf_name:
            raise HTTPException(status_code=400, detail="Invalid PDF name")

        # Check if chunks exist in Qdrant
        search_result = client.scroll(
            collection_name="KnowMe_chunks",
            scroll_filter=Filter(
                must=[
                    FieldCondition(key="source", match=MatchValue(value=pdf_name)),
                    FieldCondition(key="user_id", match=MatchValue(value=user_id))
                ]
            ),
            limit=1
        )
        chunks_exist = len(search_result[0]) > 0

        if not chunks_exist:
            raise HTTPException(status_code=404, detail=f"No PDF or chunks found for: {pdf_name}")

        # Delete chunks from Qdrant
        client.delete(
            collection_name="KnowMe_chunks",
            points_selector=Filter(
                must=[
                    FieldCondition(key="source", match=MatchValue(value=pdf_name)),
                    FieldCondition(key="user_id", match=MatchValue(value=user_id))
                ]
            )
        )

        return {
            "message": f"Successfully deleted all chunks for PDF '{pdf_name}' from Qdrant."
        }

    except ValueError as ve:
        raise HTTPException(status_code=400, detail=f"Invalid input: {str(ve)}")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to delete PDF or chunks: {str(e)}")