from fastapi import APIRouter, UploadFile, File, HTTPException
from typing import Optional
import os
import tempfile
import sys

sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
from RAG.parsing_and_chunking import extract, chunk_pdfplumber_parsed_data
from RAG.embedding_and _store import embed_and_store_pdf

router = APIRouter()


@router.post("/upload-pdf")
async def upload_pdf(
    file: UploadFile = File(...),
    user_id: Optional[str] = "anonymous"
):
    """Upload and process PDF file for RAG"""
    try:
        # Validate file type
        if not file.filename.endswith('.pdf'):
            raise HTTPException(status_code=400, detail="Only PDF files are supported")
        
        # Save uploaded file temporarily
        with tempfile.NamedTemporaryFile(delete=False, suffix='.pdf') as tmp_file:
            content = await file.read()
            tmp_file.write(content)
            tmp_path = tmp_file.name
        
        try:
            # Extract PDF content
            extraction_result = extract(tmp_path)
            
            # Convert to dict format for chunking
            pages_dict = []
            for page in extraction_result.pages:
                pages_dict.append({
                    "text": page.text,
                    "metadata": {
                        "page_number": page.page_number,
                        "source": page.filename,
                        "type": "text"
                    }
                })
            
            # Chunk the extracted content
            chunks = chunk_pdfplumber_parsed_data(pages_dict)
            
            # Embed and store in Qdrant
            stored_points = embed_and_store_pdf(chunks, user_id)
            
            return {
                "message": "PDF processed successfully",
                "chunks_stored": len(stored_points),
                "filename": file.filename,
                "user_id": user_id
            }
        
        finally:
            # Clean up temp file
            if os.path.exists(tmp_path):
                os.unlink(tmp_path)
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error processing PDF: {str(e)}")

