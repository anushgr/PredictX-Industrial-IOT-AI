from datetime import date

from pydantic import BaseModel


class MachineBase(BaseModel):
    id: str
    name: str
    status: str
    rpm: int
    temperature: float
    vibration: float
    failure_probability: float
    last_maintenance: date


class MachineDetail(MachineBase):
    plant: str
    location: str
    operating_hours: int
    model: str


class MachineListResponse(BaseModel):
    items: list[MachineBase]
