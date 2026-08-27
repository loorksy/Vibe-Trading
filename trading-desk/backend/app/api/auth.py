from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.auth import create_access_token, get_current_user, get_default_password_hash, verify_password
from app.config import get_settings
from app.database import get_db
from app.schemas import LoginRequest, TokenResponse

router = APIRouter(prefix="/auth", tags=["auth"])


@router.post("/login", response_model=TokenResponse)
async def login(body: LoginRequest):
    settings = get_settings()
    password_hash = settings.operator_password_hash or get_default_password_hash()
    if body.username != settings.operator_username or not verify_password(body.password, password_hash):
        raise HTTPException(status_code=401, detail="Invalid credentials")
    return TokenResponse(access_token=create_access_token(body.username))


@router.get("/me")
async def me(user: str = Depends(get_current_user)):
    return {"username": user}
