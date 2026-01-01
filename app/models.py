# app/models.py
from __future__ import annotations

from sqlalchemy import (
    BigInteger, DateTime, ForeignKey, Index, String, Text,
    CheckConstraint, UniqueConstraint, func, Integer
)
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, relationship
from sqlalchemy.dialects.mysql import DATETIME

from datetime import datetime



class Base(DeclarativeBase):
    pass


class Member(Base):
    __tablename__ = "Member"

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    kiosk_id: Mapped[int] = mapped_column(BigInteger, nullable=False, unique=True)
    name: Mapped[str] = mapped_column(String(100), nullable=False)

    status: Mapped[str] = mapped_column(String(16), nullable=False, server_default="INACTIVE")
    role: Mapped[str] = mapped_column(String(16), nullable=False, server_default="USER")

    created_at: Mapped[datetime] = mapped_column(DATETIME(fsp=6), nullable=False, server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(DATETIME(fsp=6), nullable=False, server_default=func.now())
    deleted_at: Mapped[datetime | None] = mapped_column(DATETIME(fsp=6), nullable=True)

    logs: Mapped[list["AttendanceLog"]] = relationship(back_populates="member")

    __table_args__ = (
        CheckConstraint("role IN ('ADMIN','USER')", name="chk_member_role"),
        CheckConstraint("status IN ('INACTIVE','ACTIVE')", name="chk_member_status"),
        UniqueConstraint("kiosk_id", name="uk_member_kiosk_id"),
    )


class AttendanceLog(Base):
    __tablename__ = "AttendanceLog"

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    member_id: Mapped[int] = mapped_column(
        BigInteger,
        ForeignKey("Member.id", name="fk_attendance_member"),
        nullable=False,
    )

    event_time: Mapped[datetime] = mapped_column(DATETIME(fsp=6), nullable=False, server_default=func.now())
    event_type: Mapped[str] = mapped_column(String(16), nullable=False)

    source: Mapped[str | None] = mapped_column(String(32), nullable=True)
    meta: Mapped[str | None] = mapped_column(Text, nullable=True)  # JSON 문자열로 저장(가장 안전)

    member: Mapped["Member"] = relationship(back_populates="logs")

    __table_args__ = (
        CheckConstraint("event_type IN ('END','EXTEND','START')", name="chk_attendance_event_type"),
        Index("idx_attendance_member_time", "member_id", "event_time"),
    )

class AttendanceSession(Base):
    __tablename__ = "AttendanceSession"

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)

    member_id: Mapped[int] = mapped_column(
        BigInteger,
        ForeignKey("Member.id", name="fk_session_member"),
        nullable=False,
    )

    # OPEN 세션 1개 보장을 위한 키
    # - OPEN일 때만 'O' 저장, CLOSED는 NULL
    open_key: Mapped[str | None] = mapped_column(String(1), nullable=True)

    # 1=OPEN, 0=CLOSED (enum 최적화 관점 반영)
    is_open: Mapped[int] = mapped_column(Integer, nullable=False, server_default="1")

    start_at: Mapped[datetime] = mapped_column(DATETIME(fsp=6), nullable=False)
    last_ping_at: Mapped[datetime] = mapped_column(DATETIME(fsp=6), nullable=False)

    # CLOSED 시 확정, OPEN이면 NULL
    end_at: Mapped[datetime | None] = mapped_column(DATETIME(fsp=6), nullable=True)

    # 'END' | 'EXPIRE' (필요 시 'ADMIN' 등 추가)
    close_reason: Mapped[str | None] = mapped_column(String(16), nullable=True)

    # CLOSED 시 확정 저장(통계용)
    duration_seconds: Mapped[int | None] = mapped_column(Integer, nullable=True)

    created_at: Mapped[datetime] = mapped_column(DATETIME(fsp=6), nullable=False, server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(DATETIME(fsp=6), nullable=False, server_default=func.now())

    member: Mapped["Member"] = relationship()

    __table_args__ = (
        # is_open은 0/1만
        CheckConstraint("is_open IN (0, 1)", name="chk_session_is_open"),
        # close_reason 제한(필요 시 확장)
        CheckConstraint("close_reason IS NULL OR close_reason IN ('END','EXPIRE')", name="chk_session_close_reason"),

        # OPEN 세션은 (member_id, open_key) 유니크로 1개 보장
        # - CLOSED는 open_key NULL이므로 여러 개 허용
        UniqueConstraint("member_id", "open_key", name="uk_session_member_openkey"),

        # 만료 정리/현재 재실 조회 핵심 인덱스
        Index("idx_session_open_lastping", "is_open", "last_ping_at"),

        # 개인별/기간별 통계 조회용
        Index("idx_session_member_start", "member_id", "start_at"),
    )
