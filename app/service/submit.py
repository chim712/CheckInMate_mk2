# app/service/submit.py
import json
from sqlalchemy.orm import Session
from sqlalchemy import text
from fastapi import HTTPException

from app.schemas import AttendancePingIn, AttendanceEndIn

from datetime import datetime, timedelta, timezone
from sqlalchemy import text

from app.service.session import (
    cleanup_expired_sessions,
    get_open_session,
    create_open_session,
    extend_open_session,
    close_open_session_end,
    SESSION_TTL,  # 선택
)



def _find_member_by_kiosk_id(db: Session, kiosk_id: int):
    """
    kiosk_id로 Member 1건 조회.
    현재 세션 상태는 status로만 판단한다.
    """
    row = db.execute(
        text("""
        SELECT id, name, status
        FROM Member
        WHERE kiosk_id = :kiosk_id
          AND deleted_at IS NULL
        """),
        {"kiosk_id": kiosk_id},
    ).mappings().first()

    if row is None:
        raise HTTPException(status_code=404, detail="해당 kioskId의 회원이 존재하지 않습니다.")

    return row



def _get_last_event(db: Session, member_id: int):
    return db.execute(
        text("""
        SELECT event_time, event_type
        FROM AttendanceLog
        WHERE member_id = :member_id
        ORDER BY event_time DESC
        LIMIT 1
        """),
        {"member_id": member_id},
    ).mappings().first()









def punch_attendance(db: Session, payload: AttendancePingIn) -> dict:
    """
    출석 버튼:
      - 요청 시 cleanup 실행(만료 세션 닫기)
      - 마지막 이벤트 기준으로 START / EXTEND 결정 (기존 정책 유지)
      - AttendanceLog 기록(기존 동일)
      - 세션 테이블: START면 세션 생성, EXTEND면 last_ping_at 갱신
      - Member.status는 항상 ACTIVE로 (기존 정책 유지)
      - 기존 API 계약(name/status/eventType) 유지
    """
    # 0) 요청 시 만료 정리
    cleanup_expired_sessions(db)

    member = _find_member_by_kiosk_id(db, payload.kioskId)
    member_id = member["id"]
    member_name = member.get("name")

    last = _get_last_event(db, member_id)

    # DB에 저장하는 시간이 "UTC tz-naive"라는 전제 유지
    now_utc = datetime.now(timezone.utc).replace(tzinfo=None)

    # 1) 이벤트 타입 판단(기존 로직 유지)
    if last is None:
        event_type = "START"
    else:
        last_time = last["event_time"]
        last_type = (last.get("event_type") or "").upper()

        expired = (now_utc - last_time) > SESSION_TTL
        ended = (last_type == "END")

        event_type = "START" if (ended or expired) else "EXTEND"

    # 2) meta 직렬화(기존 동일)
    meta_str = json.dumps(payload.meta, ensure_ascii=False) if payload.meta is not None else None
    source = payload.source or "KIOSK"

    # 3) 로그 기록(기존 동일)
    db.execute(
        text("""
        INSERT INTO AttendanceLog (member_id, event_type, source, meta, event_time)
        VALUES (:member_id, :event_type, :source, :meta, :event_time)
        """),
        {
            "member_id": member_id,
            "event_type": event_type,
            "source": source,
            "meta": meta_str,
            "event_time": now_utc,
        },
    )

    # 4) 세션 처리
    open_sess = get_open_session(db, member_id)

    if event_type == "START":
        # 혹시 남아있는 OPEN이 있으면(비정상/동시성) EXPIRE로 닫고 새로 연다
        if open_sess is not None:
            # 인정시간 = 마지막 인증까지 → end_at = last_ping_at
            db.execute(
                text("""
                UPDATE AttendanceSession
                SET is_open = 0,
                    open_key = NULL,
                    close_reason = 'EXPIRE',
                    end_at = last_ping_at,
                    duration_seconds = TIMESTAMPDIFF(SECOND, start_at, last_ping_at),
                    updated_at = UTC_TIMESTAMP(6)
                WHERE id = :session_id
                  AND is_open = 1
                """),
                {"session_id": open_sess["id"]},
            )
        create_open_session(db, member_id, now_utc)

    else:  # EXTEND
        if open_sess is None:
            # 로그상 EXTEND라도 OPEN 세션이 없으면 복구적으로 START 세션 생성
            # (기존 기능/계약을 깨지 않기 위해 eventType은 그대로 EXTEND 유지)
            create_open_session(db, member_id, now_utc)
        else:
            extend_open_session(db, open_sess["id"], now_utc)

    # 5) Member.status는 항상 ACTIVE로(기존 정책 유지)
    db.execute(
        text("""
        UPDATE Member
        SET status = 'ACTIVE',
            updated_at = UTC_TIMESTAMP(6)
        WHERE id = :member_id
        """),
        {"member_id": member_id},
    )

    db.commit()

    # 6) 반환 계약 유지(기존)
    return {
        "memberId": member_id,
        "name": member_name,
        "eventType": event_type,  # START 또는 EXTEND
        "status": "ACTIVE",
        "eventTime": now_utc.isoformat(),
    }




def end_attendance(db: Session, payload: AttendanceEndIn) -> dict:
    """
    퇴실 버튼:
      - 무조건 END 로그 남기고
      - Member.status = INACTIVE 로 만든다.
      - 이미 INACTIVE여도 그냥 패스 가능 (idempotent)
    """
    cleanup_expired_sessions(db)

    member = _find_member_by_kiosk_id(db, payload.kioskId)
    member_id = member["id"]

    meta_str = json.dumps(payload.meta, ensure_ascii=False) if payload.meta is not None else None

    now_utc = datetime.now(timezone.utc).replace(tzinfo=None)

    # 1) END 로그 기록
    db.execute(
        text("""
            INSERT INTO AttendanceLog (member_id, event_type, source, meta, event_time)
            VALUES (:member_id, 'END', :source, :meta, :event_time)
            """),
        {
            "member_id": member_id,
            "source": payload.source or "KIOSK",
            "meta": meta_str,
            "event_time": now_utc,
        },
    )

    # 1.5) OPEN 세션이 있으면 END로 닫기 (end_at 찍힘)
    close_open_session_end(db, member_id, now_utc)


    # 2) 상태를 INACTIVE로
    db.execute(
        text("""
        UPDATE Member
        SET status = 'INACTIVE',
            updated_at = UTC_TIMESTAMP(6)
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
        "eventTime": now_utc.isoformat(),
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
