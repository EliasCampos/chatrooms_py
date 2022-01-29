from fastapi import APIRouter

from chatrooms.apps.common.endpoints import health_router
from chatrooms.apps.users.endpoints import auth_router


router = APIRouter()
router.include_router(health_router, prefix='/health', tags=["health"])
router.include_router(auth_router, prefix='/auth', tags=["auth"])
