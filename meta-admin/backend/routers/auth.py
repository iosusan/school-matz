from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

from backend.auth import create_access_token, verify_password
from backend.config import settings

router = APIRouter(prefix="/auth", tags=["auth"])


class LoginRequest(BaseModel):
    username: str
    password: str


class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"


@router.post("/login", response_model=TokenResponse)
def login(body: LoginRequest):
    if body.username != settings.meta_admin_username:
        raise HTTPException(status_code=401, detail="Credenciales incorrectas")
    if not settings.meta_admin_password_hash:
        raise HTTPException(status_code=500, detail="Contraseña del administrador no configurada")
    if not verify_password(body.password, settings.meta_admin_password_hash):
        raise HTTPException(status_code=401, detail="Credenciales incorrectas")
    return TokenResponse(access_token=create_access_token())
