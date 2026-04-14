from pydantic import BaseModel


class FailureRisk(BaseModel):
    label: str
    value: float


class AlertPrediction(BaseModel):
    id: str
    machine: str
    severity: str
    sensor: str
    cause: str
    confidence: float
    recommendation: str


class PredictionListResponse(BaseModel):
    items: list[FailureRisk]
