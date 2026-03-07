#!/usr/bin/env python3
"""Create or update the superadmin user.

Credentials are read from the ADMIN_USER and ADMIN_PASS environment variables.
Usage:
    ADMIN_USER=admin ADMIN_PASS=secret python scripts/create_superadmin.py
"""

import os
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from sqlalchemy.orm import Session

from backend.auth import hash_password
from backend.database import Base, engine
from backend.models.admin_user import AdminUser

username = os.environ.get("ADMIN_USER", "").strip()
password = os.environ.get("ADMIN_PASS", "")

if not username or not password:
    print("ERROR: ADMIN_USER and ADMIN_PASS env vars are required", file=sys.stderr)
    sys.exit(1)

Base.metadata.create_all(bind=engine)

with Session(engine) as db:
    existing = db.query(AdminUser).filter(AdminUser.username == username).first()
    if existing:
        existing.password_hash = hash_password(password)
        existing.is_superadmin = True
        db.commit()
        print(f"Superadmin '{username}' actualizado.")
    else:
        user = AdminUser(
            username=username,
            password_hash=hash_password(password),
            is_superadmin=True,
        )
        db.add(user)
        db.commit()
        print(f"Superadmin '{username}' creado.")
