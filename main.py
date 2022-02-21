from fastapi import FastAPI, Request, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from tortoise.contrib.fastapi import register_tortoise

from chatrooms.apps.common.exceptions import BadInputError, PermissionDeniedError
from chatrooms.config import settings
from chatrooms.config.endpoints import router


app = FastAPI(
    title="Chatrooms",
    openapi_url=f"{settings.API_BASE_URL}/openapi.json"
)


app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


app.include_router(router, prefix=settings.API_BASE_URL)


register_tortoise(
    app,
    db_url=settings.DATABASE_URI,
    modules={"models": settings.APPS_MODELS},
    generate_schemas=False,
    add_exception_handlers=True,
)


@app.exception_handler(BadInputError)
async def bad_input_error_handler(__: Request, exc: BadInputError):
    return JSONResponse(status_code=status.HTTP_400_BAD_REQUEST, content=exc.message)


@app.exception_handler(PermissionDeniedError)
async def permission_denied_error_handler(__: Request, exc: PermissionDeniedError):
    return JSONResponse(status_code=status.HTTP_403_FORBIDDEN, content={'detail': exc.detail})
