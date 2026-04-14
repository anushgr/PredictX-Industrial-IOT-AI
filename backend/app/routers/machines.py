from fastapi import APIRouter, Depends, HTTPException

from app.dependencies import get_current_user
from app.services.mock_data import get_machine_by_id, get_machines

router = APIRouter()


@router.get("/machines")
def list_machines(_: dict = Depends(get_current_user)) -> list[dict]:
    return [
        {
            "id": machine["id"],
            "name": machine["name"],
            "status": machine["status"],
            "rpm": machine["rpm"],
            "temperature": machine["temperature"],
            "vibration": machine["vibration"],
            "failureProbability": machine["failure_probability"],
            "lastMaintenance": machine["last_maintenance"].isoformat(),
        }
        for machine in get_machines()
    ]


@router.get("/machines/{machine_id}")
def machine_detail(machine_id: str, _: dict = Depends(get_current_user)) -> dict:
    machine = get_machine_by_id(machine_id)
    if not machine:
        raise HTTPException(status_code=404, detail="Machine not found")
    return {
        **machine,
        "last_maintenance": machine["last_maintenance"].isoformat(),
    }
