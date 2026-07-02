from pydantic import BaseModel
from typing import Optional


class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    user_id: str
    role: str


class LoginRequest(BaseModel):
    phone: str
    aadhaar_last4: str


class CitizenRegister(BaseModel):
    name: str
    phone: str
    email: Optional[str] = None
    district: str
    aadhaar_last4: str
