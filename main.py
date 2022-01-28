from fastapi import FastAPI

from chatrooms.config import settings
from chatrooms.config.endpoints import router


app = FastAPI(
    title="Chatrooms",
    openapi_url=f"{settings.API_BASE_URL}/openapi.json"
)


app.include_router(router, prefix=settings.API_BASE_URL)
