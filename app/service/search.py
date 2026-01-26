# app/service/search.py
from collections import OrderedDict
from datetime import timedelta
from zoneinfo import ZoneInfo

KST = ZoneInfo("Asia/Seoul")
UTC = ZoneInfo("UTC")

from sqlalchemy.orm import Session
from sqlalchemy import text
from fastapi import HTTPException

from app.service.session import cleanup_expired_sessions


def get_attendance_data(db: Session, kiosk_id: int) -> dict:
    """
    kioskId 기준으로 Member + AttendanceLog를 조회하여
    프론트에서 사용하는 attendanceData JSON 형태로 변환한다.
    """
    cleanup_expired_sessions(db)

    # 1) 우선 회원부터 확인 (없으면 404)
    member = db.execute(
        text("""
        SELECT id, name, status
        FROM Member
        WHERE kiosk_id = :kiosk_id
          AND deleted_at IS NULL
        """),
        {"kiosk_id": kiosk_id},
    ).mappings().first()

    if member is None:
        raise HTTPException(status_code=404, detail="해당 kioskId의 회원이 존재하지 않습니다.")

    member_id = member["id"]
    member_name = member["name"]

    # 2) AttendanceLog 전체(혹은 나중에 기간 필터 추가 가능)
    rows = db.execute(
        text("""
        SELECT event_time, event_type, source
        FROM AttendanceLog
        WHERE member_id = :member_id
        ORDER BY event_time ASC
        """),
        {"member_id": member_id},
    ).mappings().all()

    # 3) 기본 응답 골격
    result = {
        "userId": member_id,
        "userName": member_name,
        "logData": []
    }

    if not rows:
        # 로그가 하나도 없으면 logData = [] 그대로 반환
        return result

    # 요일 코드 (mon, tue, ... sun)
    weekday_codes = ["mon", "tue", "wed", "thu", "fri", "sat", "sun"]

    # 날짜별 그룹핑 (입력 순서 유지)
    day_map: OrderedDict[str, dict] = OrderedDict()

    for r in rows:
        dt_utc = r["event_time"]  # SQLAlchemy가 datetime으로 가져옴

        # ※ event_time이 sysutcdatetime() 기준이면 KST로 보고 싶을 때 +9시간
        dt_local = dt_utc + timedelta(hours=9)

        date_str = dt_local.strftime("%Y-%m-%d")   # "2025-11-26"
        time_str = dt_local.strftime("%H:%M:%S")   # "13:30:05"
        day_code = weekday_codes[dt_local.weekday()]  # 0=월 → "mon" ...

        # 날짜별 entry 생성
        if date_str not in day_map:
            entry = {
                "date": date_str,
                "day": day_code,
                "events": []
            }
            day_map[date_str] = entry
            result["logData"].append(entry)

        # 이벤트 추가 (type은 소문자로 내려줌: start/extend/end)
        day_map[date_str]["events"].append({
            "time": time_str,
            "type": (r["event_type"] or "").lower(),
            "source": (r["source"] or "").lower()
        })

    return result




def get_active_attendance_list(db: Session) -> dict:
    """
    현재 재실 중인(ACTIVE) 회원 목록을 반환한다.
    - 요청 시 cleanup 수행
    - Member.status = 'ACTIVE' 기준
    """
    cleanup_expired_sessions(db)

    rows = db.execute(
        text("""
        SELECT id, kiosk_id, name, updated_at
        FROM Member
        WHERE status = 'ACTIVE'
          AND deleted_at IS NULL
        ORDER BY name ASC
        """)
    ).mappings().all()

    result = {
        "totalCount": len(rows),
        "list": []
    }

    for r in rows:
        updated_at: datetime | None = r["updated_at"]

        if updated_at:
            # DB에서 naive UTC로 오는 경우
            if updated_at.tzinfo is None:
                updated_at = updated_at.replace(tzinfo=UTC)

            updated_at_kst = updated_at.astimezone(KST)
            time_str = updated_at_kst.strftime("%Y-%m-%d %H:%M")
        else:
            time_str = None

        result["list"].append({
            "memberId": r["id"],
            "kioskId": r["kiosk_id"],
            "name": r["name"],
            "time": time_str,
        })

    return result
