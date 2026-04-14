from pydantic import BaseModel


class SensorReading(BaseModel):
    id: str
    name: str
    unit: str
    value: float
    threshold: float
    anomaly_count: int
    series: list[float]


class SensorSeriesResponse(BaseModel):
    items: list[SensorReading]
