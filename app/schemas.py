# app/schemas.py
from pydantic import BaseModel


class AttendancePingIn(BaseModel):
    kioskId: int
    source: str | None = "KIOSK"
    meta: dict | None = None


class AttendanceEndIn(BaseModel):
    kioskId: int
    source: str | None = "KIOSK"
    meta: dict | None = None
