from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse, FileResponse
from fastapi.exceptions import HTTPException as FastAPIHTTPException
from api.exceptions import global_exception_handler, http_exception_handler
from api.routes import health, chat, pdf, get_pdfs, delete_pdfs
import logging

# Enhanced logging configuration
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(),
        logging.FileHandler('rag_gemini_sdk.log', mode='a')
    ]
)
logger = logging.getLogger(__name__)

# Create FastAPI app
app = FastAPI(
    title="AI Agent Backend API",
    description="Production-grade FastAPI backend with Gemini function calling, RAG, and tool integrations",
    version="1.0.0"
)

# CORS configuration
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Configure appropriately for production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Global exception handlers
app.add_exception_handler(Exception, global_exception_handler)
app.add_exception_handler(FastAPIHTTPException, http_exception_handler)

# Include routers with version prefix
app.include_router(health.router, prefix="/v1", tags=["Health"])
app.include_router(chat.router, prefix="/v1", tags=["Chat"])
app.include_router(pdf.router, prefix="/v1", tags=["PDF"])
app.include_router(delete_pdfs.router, prefix="/v1", tags=["PDF"])
app.include_router(get_pdfs.router, prefix="/v1", tags=["PDF"])

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
