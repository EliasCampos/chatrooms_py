from fastapi import APIRouter

from chatrooms.apps.common.endpoints import health_router


router = APIRouter()
router.include_router(health_router, prefix='/health', tags=["health"])
