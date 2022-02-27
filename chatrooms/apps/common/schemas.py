from pydantic.main import BaseModel


class HealthCheck(BaseModel):
    status: str


class ResponseDetail(BaseModel):
    detail: str
