from fastapi import APIRouter, Depends

from app.dependencies import get_current_user
from app.services.mock_data import get_users

router = APIRouter()


@router.get("/users")
def list_users(_: dict = Depends(get_current_user)) -> list[dict]:
    return [
        {
            "id": user["id"],
            "name": user["name"],
            "email": user["email"],
            "role": user["role"],
            "lastLogin": user["last_login"],
            "accessLevel": user["access_level"],
            "status": user["status"],
        }
        for user in get_users()
    ]
