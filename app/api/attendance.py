# app/api/submit.py

import logging

from fastapi import APIRouter
from fastapi import Depends
from sqlalchemy.orm import Session

from app.db import get_db
from app.schemas import AttendancePingIn, AttendanceEndIn
from app.service.submit import punch_attendance, end_attendance
from app.service.search import get_attendance_data

router = APIRouter(prefix="/attendance", tags=["attendance"])
logger = logging.getLogger(__name__)

# =================================================================================================
#                            Attendance & End Process
# =================================================================================================
@router.post("")
async def post_attendance(
    payload: AttendancePingIn,
    db: Session = Depends(get_db),
):
    """
    출석 버튼: START/EXTEND 자동 판정 (Member.status 기준).
    """
    result = punch_attendance(db, payload)
    logger.info("Attendance result: %s", result)

    #print(result["eventType"], result["name"])
    if result["eventType"] == "START":
        return {"status": "ok", "message": f"{result['name']}님, 안녕하세요"}
    else:
        return {"status": "ok", "message": f"{result['name']}님, 다시 오신 것을 환영합니다"}


@router.post("/end")
def post_attendance_end(
    payload: AttendanceEndIn,
    db: Session = Depends(get_db),
):
    """
    퇴실 버튼: END 처리 + status INACTIVE.
    """

    result = end_attendance(db, payload)
    logger.info("Attendance result: %s", result)
    return {"status": "ok", "message": f"{result['name']}님, 안녕히 가세요"}



# =================================================================================================
#                               View Log
# =================================================================================================
@router.get("/logs")
def get_attendance_logs(
    kioskId: int,              # 쿼리 파라미터 ?kioskId=1129
    db: Session = Depends(get_db),
):
    """
    출결 조회 페이지에서 사용하는 JSON을 반환한다.
    예: GET /attendance/logs?kioskId=1129
    """
    data = get_attendance_data(db, kioskId)
    return data

