# app/service/submit.py
import json
from sqlalchemy.orm import Session
from sqlalchemy import text
from fastapi import HTTPException

from app.schemas import AttendancePingIn, AttendanceEndIn


def _find_member_by_kiosk_id(db: Session, kiosk_id: int):
    """
    kiosk_id로 Member 1건 조회.
    현재 세션 상태는 status로만 판단한다.
    """
    row = db.execute(
        text("""
        SELECT id, name, status
        FROM dbo.Member
        WHERE kiosk_id = :kiosk_id
          AND deleted_at IS NULL
        """),
        {"kiosk_id": kiosk_id},
    ).mappings().first()

    if row is None:
        raise HTTPException(status_code=404, detail="해당 kioskId의 회원이 존재하지 않습니다.")

    return row


def punch_attendance(db: Session, payload: AttendancePingIn) -> dict:
    """
    출석 버튼:
      - Member.status가 INACTIVE면 START
      - ACTIVE면 EXTEND
      - 항상 최종 status는 ACTIVE로 만든다.
    """
    member = _find_member_by_kiosk_id(db, payload.kioskId)
    member_id = member["id"]
    current_status = (member["status"] or "INACTIVE").upper()

    if current_status == "ACTIVE":
        event_type = "EXTEND"
    else:
        event_type = "START"

    meta_str = json.dumps(payload.meta, ensure_ascii=False) if payload.meta is not None else None

    # 1) 로그 기록
    db.execute(
        text("""
        INSERT INTO dbo.AttendanceLog (member_id, event_type, source, meta)
        VALUES (:member_id, :event_type, :source, :meta)
        """),
        {
            "member_id": member_id,
            "event_type": event_type,
            "source": payload.source or "KIOSK",
            "meta": meta_str,
        },
    )

    # 2) 상태는 항상 ACTIVE로
    if current_status != "ACTIVE":
        db.execute(
            text("""
            UPDATE dbo.Member
            SET status = 'ACTIVE',
                updated_at = SYSUTCDATETIME()
            WHERE id = :member_id
            """),
            {"member_id": member_id},
        )

    db.commit()

    return {
        "memberId": member_id,
        "name": member["name"],
        "eventType": event_type,      # START 또는 EXTEND
        "status": "ACTIVE",
    }


def end_attendance(db: Session, payload: AttendanceEndIn) -> dict:
    """
    퇴실 버튼:
      - 무조건 END 로그 남기고
      - Member.status = INACTIVE 로 만든다.
      - 이미 INACTIVE여도 그냥 패스 가능 (idempotent)
    """
    member = _find_member_by_kiosk_id(db, payload.kioskId)
    member_id = member["id"]

    meta_str = json.dumps(payload.meta, ensure_ascii=False) if payload.meta is not None else None

    # 1) END 로그 기록
    db.execute(
        text("""
        INSERT INTO dbo.AttendanceLog (member_id, event_type, source, meta)
        VALUES (:member_id, 'END', :source, :meta)
        """),
        {
            "member_id": member_id,
            "source": payload.source or "KIOSK",
            "meta": meta_str,
        },
    )

    # 2) 상태를 INACTIVE로
    db.execute(
        text("""
        UPDATE dbo.Member
        SET status = 'INACTIVE',
            updated_at = SYSUTCDATETIME()
        WHERE id = :member_id
        """),
        {"member_id": member_id},
    )

    db.commit()

    return {
        "memberId": member_id,
        "name": member["name"],
        "eventType": "END",
        "status": "INACTIVE",
    }


# Attendance API 응답 예시:
#
# 1) 출석 첫 입력 → START
# {
#     "memberId": 1234,
#     "name": "홍길동",
#     "eventType": "START",
#     "status": "ACTIVE"
# }
#
# 2) 출석 연장 → EXTEND
# {
#     "memberId": 1234,
#     "name": "홍길동",
#     "eventType": "EXTEND",
#     "status": "ACTIVE"
# }
#
# 3) 퇴실 처리 → END
# {
#     "memberId": 1234,
#     "name": "홍길동",
#     "eventType": "END",
#     "status": "INACTIVE"
# }
