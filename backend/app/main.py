from __future__ import annotations

import asyncio

from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware

from app.core.config import settings
from app.routers import api_router
from app.services.mqtt_ingest import ingestion_service
from app.services.telemetry_db import get_live_sensors_from_db

app = FastAPI(title=settings.app_name, version="2.1.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origin_list,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(api_router, prefix=settings.api_prefix)


@app.get("/health")
def health() -> dict:
    return {
        "status": "healthy",
        "service": settings.app_name,
        "database_connected": ingestion_service.database_connected,
        "database_error": ingestion_service.database_error,
        "mqtt_ingestion_running": ingestion_service.running,
        "last_ingest_insert": ingestion_service.last_insert,
        "last_ingest_error": ingestion_service.last_error,
    }


@app.on_event("startup")
def startup_event() -> None:
    if not ingestion_service.verify_database_connection():
        raise RuntimeError(f"Startup aborted: {ingestion_service.database_error}")

    ingestion_service.start()


@app.on_event("shutdown")
def shutdown_event() -> None:
    ingestion_service.stop()


@app.websocket("/ws/telemetry")
async def telemetry_socket(websocket: WebSocket) -> None:
    await websocket.accept()
    try:
        while True:
            await websocket.send_json(get_live_sensors_from_db())
            await asyncio.sleep(2.0)
    except WebSocketDisconnect:
        return
