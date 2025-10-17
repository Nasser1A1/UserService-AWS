from fastapi.responses import JSONResponse
from fastapi.encoders import jsonable_encoder
from pydantic import BaseModel

def JsonResponse(data=None, message="Success", status_code=200):
    # ✅ Convert safely (handles datetime, Pydantic, lists, etc.)
    data = jsonable_encoder(data)

    return JSONResponse(
        status_code=status_code,
        content={
            "status": "success" if status_code < 400 else "error",
            "message": message,
            "data": data,
        },
    )
