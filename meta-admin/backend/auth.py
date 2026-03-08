from datetime import datetime, timedelta, timezone

import bcrypt
from fastapi import Header, HTTPException
from jose import JWTError, jwt

from backend.config import settings

_ALGORITHM = "HS256"


def verify_password(plain: str, hashed: str) -> bool:
    return bcrypt.checkpw(plain.encode(), hashed.encode())


def create_access_token() -> str:
    expire = datetime.now(timezone.utc) + timedelta(hours=settings.access_token_expire_hours)
    payload = {
        "sub": settings.meta_admin_username,
        "exp": expire,
        "role": "meta-admin",
    }
    return jwt.encode(payload, settings.meta_secret_key, algorithm=_ALGORITHM)


def get_current_admin(
    authorization: str | None = Header(default=None),
) -> str:
    """Dependencia FastAPI — valida JWT y devuelve el username del admin."""
    if not authorization or not authorization.startswith("Bearer "):
        raise HTTPException(status_code=401, detail="No autenticado")
    token = authorization.split(" ", 1)[1]
    try:
        payload = jwt.decode(token, settings.meta_secret_key, algorithms=[_ALGORITHM])
        username: str | None = payload.get("sub")
        if not username or payload.get("role") != "meta-admin":
            raise JWTError()
    except JWTError:
        raise HTTPException(status_code=401, detail="Token inválido o expirado") from None
    return username
