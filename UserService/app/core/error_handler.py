from logging import Logger
from fastapi import Depends, Request
from fastapi.responses import JSONResponse
from core.dependancies import get_logger
from core.exceptions import AppException

logger = get_logger()  # ✅ get real logger instance

async def app_exception_handler(request: Request, exc: AppException):
    logger.error(f"{request.method} {request.url} -> {exc.message}")
    return JSONResponse(
        status_code=exc.status_code,
        content={"status": "error", "message": exc.message},
    )

async def general_exception_handler(request: Request, exc: Exception):
    logger.exception(f"Unhandled error: {str(exc)}")
    return JSONResponse(
        status_code=500,
        content={"status": "error", "message": "Internal Server Error"},
    )
