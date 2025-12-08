from fastapi import APIRouter, HTTPException
from qdrant_client import QdrantClient
from qdrant_client.http import models
from qdrant_client.http.models import Filter, FieldCondition, MatchValue

router = APIRouter()
client = QdrantClient()

@router.get("/pdfs/")
async def list_pdfs(user_id: str = "anonymous"):
    '''Gets the name of Pdf files uploaded and stored in qdrant db for a specific user.'''
    try:
        res = client.scroll(
            collection_name="KnowMe_chunks",
            limit=1000,
            with_payload=True,
            scroll_filter=Filter(must=[FieldCondition(key="user_id", match=MatchValue(value=user_id))])
        )
        pdfs = set()
        for point in res[0]:
            source = point.payload.get("source")
            if source:
                pdfs.add(source)
        return {"pdfs": list(pdfs)}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))