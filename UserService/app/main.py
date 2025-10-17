from fastapi import FastAPI
from presentation.middlewares.logging_middleware import log_middleware
from core.response import JsonResponse
from core.exceptions import AppException
from core.error_handler import app_exception_handler,general_exception_handler
from presentation.routers.user_router import user_router
import uvicorn
from starlette.middleware.base import BaseHTTPMiddleware

app = FastAPI(title="User Service (Onion Architecture)")

app.add_exception_handler(AppException, app_exception_handler)
app.add_exception_handler(Exception, general_exception_handler)
app.include_router(user_router)
app.add_middleware(BaseHTTPMiddleware, dispatch=log_middleware)

@app.get("/")
def health_root():
    return JsonResponse(message="User Service is up and running", status_code=200, data={})

if __name__ == "__main__":
    uvicorn.run(app="main:app",host="0.0.0.0",port=8080,reload=True)
