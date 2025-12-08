from fastapi import APIRouter
from typing import Dict

router = APIRouter()


@router.get("/health")
async def health_check() -> Dict:
    """Health check endpoint"""
    return {
        "status": "healthy",
        "services": {
            "api": "operational"
        }
    }


@router.get("/")
async def root() -> Dict:
    """Root endpoint"""
    return {
        "message": "AI Agent Backend API",
        "version": "1.0.0"
    }

