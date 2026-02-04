# app/api/admin.py

import logging

from fastapi import APIRouter
from fastapi import Depends
from sqlalchemy.orm import Session

from app.db.db import get_db
from app.service.search import get_member_list

router = APIRouter(prefix="/admin", tags=["admin"])

@router.get("/members")
def admin_members(orgId: int, db: Session = Depends(get_db)):
    """
    관리자 페이지에서 사용할 전체 구성원 리스트 조회 API URL
    """
    return get_member_list(db, orgId)