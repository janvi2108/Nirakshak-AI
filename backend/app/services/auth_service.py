import hashlib
from datetime import datetime, timedelta
from jose import jwt
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from app.config import settings
from app.models.citizen import Citizen
import logging

logger = logging.getLogger(__name__)


def hash_aadhaar(aadhaar_last4: str, phone: str) -> str:
    return hashlib.sha256(f"{aadhaar_last4}:{phone}".encode()).hexdigest()


def create_access_token(user_id: str, role: str = "citizen") -> str:
    payload = {
        "sub": user_id, "role": role,
        "exp": datetime.utcnow() + timedelta(minutes=settings.jwt_expire_minutes),
        "iat": datetime.utcnow(),
    }
    return jwt.encode(payload, settings.jwt_secret_key, algorithm=settings.jwt_algorithm)


async def get_or_create_citizen(db, name, phone, district, aadhaar_last4, email=None):
    aadhaar_hash = hash_aadhaar(aadhaar_last4, phone)
    result = await db.execute(select(Citizen).where(Citizen.aadhaar_hash == aadhaar_hash))
    citizen = result.scalar_one_or_none()
    if not citizen:
        citizen = Citizen(aadhaar_hash=aadhaar_hash, name=name, phone=phone, email=email, district=district)
        db.add(citizen)
        await db.commit()
        await db.refresh(citizen)
    return citizen


async def login_citizen(db, phone, aadhaar_last4):
    aadhaar_hash = hash_aadhaar(aadhaar_last4, phone)
    result = await db.execute(select(Citizen).where(Citizen.aadhaar_hash == aadhaar_hash))
    citizen = result.scalar_one_or_none()
    if not citizen:
        return None
    token = create_access_token(citizen.id, role="citizen")
    return {"access_token": token, "token_type": "bearer", "user_id": citizen.id, "role": "citizen"}
