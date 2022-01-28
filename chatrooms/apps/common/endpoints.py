from fastapi import APIRouter

from chatrooms.apps.common.schemas import HealthCheck

health_router = APIRouter()


@health_router.get('/status', response_model=HealthCheck)
def get_health_status():
    return {'status': "OK"}
