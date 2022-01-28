from pydantic.main import BaseModel


class HealthCheck(BaseModel):
    status: str
