# app/models.py
from __future__ import annotations

from sqlalchemy import (
    BigInteger, DateTime, ForeignKey, Index, String, Text,
    CheckConstraint, UniqueConstraint, func
)
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, relationship


class Base(DeclarativeBase):
    pass


class Member(Base):
    __tablename__ = "Member"

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    kiosk_id: Mapped[int] = mapped_column(BigInteger, nullable=False, unique=True)
    name: Mapped[str] = mapped_column(String(100), nullable=False)

    status: Mapped[str] = mapped_column(String(16), nullable=False, server_default="INACTIVE")
    role: Mapped[str] = mapped_column(String(16), nullable=False, server_default="USER")

    created_at: Mapped[str] = mapped_column(DateTime(fsp=6), nullable=False, server_default=func.now())
    updated_at: Mapped[str] = mapped_column(DateTime(fsp=6), nullable=False, server_default=func.now())
    deleted_at: Mapped[str | None] = mapped_column(DateTime(fsp=6), nullable=True)

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

    event_time: Mapped[str] = mapped_column(DateTime(fsp=6), nullable=False, server_default=func.now())
    event_type: Mapped[str] = mapped_column(String(16), nullable=False)

    source: Mapped[str | None] = mapped_column(String(32), nullable=True)
    meta: Mapped[str | None] = mapped_column(Text, nullable=True)  # JSON 문자열로 저장(가장 안전)

    member: Mapped["Member"] = relationship(back_populates="logs")

    __table_args__ = (
        CheckConstraint("event_type IN ('END','EXTEND','START')", name="chk_attendance_event_type"),
        Index("idx_attendance_member_time", "member_id", "event_time"),
    )
