from fastapi import APIRouter, HTTPException, status

from app.core.security import create_access_token, verify_password
from app.schemas.auth import CurrentUser, LoginRequest, TokenResponse
from app.services.mock_data import get_user_by_email

router = APIRouter()


@router.post("/login", response_model=TokenResponse)
def login(payload: LoginRequest) -> TokenResponse:
    user = get_user_by_email(payload.email)
    if not user or not verify_password(payload.password, user["password_hash"]):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid credentials")

    token = create_access_token(
        subject=user["email"],
        extra_claims={"role": user["role"], "uid": user["id"]},
    )
    return TokenResponse(access_token=token)


@router.get("/me", response_model=CurrentUser)
def me() -> CurrentUser:
    user = get_user_by_email("ava@predictx.ai")
    assert user is not None
    return CurrentUser(id=user["id"], name=user["name"], email=user["email"], role=user["role"])
