# app/api/attendance.py

from fastapi import APIRouter

router = APIRouter(prefix="/attendance", tags=["attendance"])

@router.post("/submit")
async def submit():

    #TODO - write Logic

    return {"status": "ok"}

