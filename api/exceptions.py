from fastapi import HTTPException, Request
from fastapi.responses import JSONResponse
import logging

logger = logging.getLogger(__name__)


class APIException(HTTPException):
    """Custom API exception"""
    pass


async def global_exception_handler(request: Request, exc: Exception):
    """Global exception handler for unhandled exceptions"""
    logger.error(f"Unhandled exception: {exc}", exc_info=True)
    return JSONResponse(
        status_code=500,
        content={
            "error": "Internal server error",
            "message": str(exc) if str(exc) else "An unexpected error occurred",
            "path": str(request.url)
        }
    )


async def http_exception_handler(request: Request, exc: HTTPException):
    """Handler for HTTP exceptions"""
    from fastapi.exceptions import HTTPException as FastAPIHTTPException
    if isinstance(exc, FastAPIHTTPException):
        status_code = exc.status_code
        detail = exc.detail
    else:
        status_code = getattr(exc, 'status_code', 500)
        detail = getattr(exc, 'detail', str(exc))
    
    return JSONResponse(
        status_code=status_code,
        content={
            "error": detail,
            "status_code": status_code,
            "path": str(request.url)
        }
    )

