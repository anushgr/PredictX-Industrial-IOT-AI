from fastapi import APIRouter, Depends

from app.dependencies import get_current_user
from app.services.mock_data import get_analytics

router = APIRouter()


@router.get("/analytics")
def analytics(_: dict = Depends(get_current_user)) -> dict:
    return get_analytics()
