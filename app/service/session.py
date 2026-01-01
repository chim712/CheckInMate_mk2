# app/service/session.py
from sqlalchemy.orm import Session
from datetime import datetime, timedelta, timezone
from sqlalchemy import text


SESSION_TTL = timedelta(hours=3)


# =========================================
#       Session Helper Function
# =========================================

def cleanup_expired_sessions(db: Session):
    """
    요청이 들어올 때만 만료 세션 정리.
    - OPEN && last_ping_at < now - 3h 인 세션을 EXPIRE로 닫는다.
    - 인정시간은 마지막 인증까지만: end_at = last_ping_at
    - duration_seconds 확정
    - 필요 시 Member.status도 INACTIVE로 맞춘다(OPEN 세션이 없어진 멤버)
    """
    now_utc = datetime.now(timezone.utc).replace(tzinfo=None)
    cutoff = now_utc - SESSION_TTL

    # 1) 만료된 OPEN 세션 닫기
    # - end_at = last_ping_at (뻥튀기 방지)
    # - duration_seconds = TIMESTAMPDIFF(SECOND, start_at, end_at)
    db.execute(
        text("""
        UPDATE AttendanceSession
        SET is_open = 0,
            open_key = NULL,
            close_reason = 'EXPIRE',
            end_at = last_ping_at,
            duration_seconds = TIMESTAMPDIFF(SECOND, start_at, last_ping_at),
            updated_at = UTC_TIMESTAMP(6)
        WHERE is_open = 1
          AND last_ping_at < :cutoff
        """),
        {"cutoff": cutoff},
    )

    # 2) Member.status 동기화(캐시 유지 목적)
    # - OPEN 세션이 하나도 없는 멤버는 INACTIVE로 맞춤
    # - ACTIVE를 무조건 내리지는 않고, 실제 open 세션 존재 여부로만 판단
    db.execute(
        text("""
        UPDATE Member m
        LEFT JOIN (
            SELECT member_id
            FROM AttendanceSession
            WHERE is_open = 1
            GROUP BY member_id
        ) s ON s.member_id = m.id
        SET m.status = 'INACTIVE',
            m.updated_at = UTC_TIMESTAMP(6)
        WHERE m.deleted_at IS NULL
          AND m.status = 'ACTIVE'
          AND s.member_id IS NULL
        """)
    )


def get_open_session(db: Session, member_id: int):
    return db.execute(
        text("""
        SELECT id, member_id, start_at, last_ping_at
        FROM AttendanceSession
        WHERE member_id = :member_id
          AND is_open = 1
        ORDER BY start_at DESC
        LIMIT 1
        """),
        {"member_id": member_id},
    ).mappings().first()


def create_open_session(db: Session, member_id: int, now_utc: datetime):
    # open_key='O' 로 OPEN 세션 유일성 보장
    db.execute(
        text("""
        INSERT INTO AttendanceSession
            (member_id, open_key, is_open, start_at, last_ping_at, created_at, updated_at)
        VALUES
            (:member_id, 'O', 1, :now_utc, :now_utc, UTC_TIMESTAMP(6), UTC_TIMESTAMP(6))
        """),
        {"member_id": member_id, "now_utc": now_utc},
    )


def extend_open_session(db: Session, session_id: int, now_utc: datetime):
    db.execute(
        text("""
        UPDATE AttendanceSession
        SET last_ping_at = :now_utc,
            updated_at = UTC_TIMESTAMP(6)
        WHERE id = :session_id
          AND is_open = 1
        """),
        {"session_id": session_id, "now_utc": now_utc},
    )


def close_open_session_end(db: Session, member_id: int, now_utc: datetime):
    """
    END 버튼으로 세션 종료.
    - end_at = now_utc (END 자체를 마지막 인증으로 취급)
    - duration_seconds 확정
    """
    db.execute(
        text("""
        UPDATE AttendanceSession
        SET is_open = 0,
            open_key = NULL,
            close_reason = 'END',
            end_at = :now_utc,
            duration_seconds = TIMESTAMPDIFF(SECOND, start_at, :now_utc),
            updated_at = UTC_TIMESTAMP(6)
        WHERE member_id = :member_id
          AND is_open = 1
        """),
        {"member_id": member_id, "now_utc": now_utc},
    )

# =========================================
