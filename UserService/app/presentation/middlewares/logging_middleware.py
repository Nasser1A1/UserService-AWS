import json
from logging import Logger
from fastapi import Depends, Request

from core.dependancies import get_logger
from core.logger import LoggingService
from time import time
logger = get_logger()  # ✅ get real logger instance

async def log_middleware(request: Request, call_next):
    """
    Middleware to log incoming requests and outgoing responses.
    Logs the method, URL, and status code.
    """
    start_time = time()
    response = await call_next(request)
    # Clone response body (StreamingResponse requires special handling)
    response_body = b""
    async for chunk in response.body_iterator:
        response_body += chunk

        # Replace the original iterator, so the client still gets the response
    response.body_iterator = iterate_in_memory(response_body)

        # Try to parse as JSON
    try:
        json_data = json.loads(response_body.decode("utf-8"))
    except Exception:
            json_data = None  # Not JSON or failed to parse

    
    log_dict = {
        'url' : request.url.path,
        'method' : request.method,
        'status_code' : response.status_code,
        'response_data': json_data['data'] if json_data and 'data' in json_data else None,
        'response_message': json_data['message'] if json_data and 'message' in json_data else None,
        'processing_time':  round(time() - start_time, 4) 
    }
    logger.info(log_dict, extra=log_dict)
    return response

# Helper to recreate body iterator for downstream response sending
async def iterate_in_memory(data: bytes):
    yield data