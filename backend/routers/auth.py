from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy.orm import Session

from backend.auth import create_access_token, get_current_admin, verify_password
from backend.database import get_db
from backend.models.admin_user import AdminUser

router = APIRouter(prefix="/auth", tags=["auth"])


class LoginRequest(BaseModel):
    username: str
    password: str


class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"


@router.post("/login", response_model=TokenResponse)
def login(data: LoginRequest, db: Session = Depends(get_db)):
    user = db.query(AdminUser).filter(AdminUser.username == data.username).first()
    if not user or not verify_password(data.password, user.password_hash):
        raise HTTPException(status_code=401, detail="Credenciales incorrectas")
    return TokenResponse(access_token=create_access_token(user.username))


@router.get("/me")
def me(current_user: AdminUser = Depends(get_current_admin)):
    return {"username": current_user.username, "is_superadmin": current_user.is_superadmin}


@router.get("/status")
def status(db: Session = Depends(get_db)):
    """Returns whether at least one superadmin has been created."""
    has_admin = db.query(AdminUser).filter(AdminUser.is_superadmin == True).first() is not None  # noqa: E712
    return {"has_superadmin": has_admin}
