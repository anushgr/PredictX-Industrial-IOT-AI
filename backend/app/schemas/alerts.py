from pydantic import BaseModel


class AlertRecord(BaseModel):
    id: str
    time: str
    machine: str
    alert_type: str
    severity: str
    sensor: str
    predicted_cause: str
    status: str


class AlertListResponse(BaseModel):
    items: list[AlertRecord]
