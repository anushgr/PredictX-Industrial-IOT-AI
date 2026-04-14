from fastapi import APIRouter

from app.routers import analytics, auth, machines, predictions, reports, sensors, users

api_router = APIRouter()
api_router.include_router(auth.router, tags=["auth"])
api_router.include_router(users.router, tags=["users"])
api_router.include_router(sensors.router, tags=["sensors"])
api_router.include_router(machines.router, tags=["machines"])
api_router.include_router(predictions.router, tags=["predictions"])
api_router.include_router(analytics.router, tags=["analytics"])
api_router.include_router(reports.router, tags=["reports"])
