from fastapi import APIRouter, Depends

from app.dependencies import get_current_user
from app.services.analytics_db import get_analytics_from_db

router = APIRouter()


@router.get("/analytics")
def analytics(_: dict = Depends(get_current_user)) -> dict:
    return get_analytics_from_db()
