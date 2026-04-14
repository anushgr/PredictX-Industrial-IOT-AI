from fastapi import APIRouter, Depends

from app.dependencies import get_current_user
from app.services.mock_data import get_live_sensors, get_sensor_history

router = APIRouter()


@router.get("/sensors/live")
def sensors_live(_: dict = Depends(get_current_user)) -> list[dict]:
    return get_live_sensors()


@router.get("/sensors/history")
def sensors_history(_: dict = Depends(get_current_user)) -> list[dict]:
    return get_sensor_history()
