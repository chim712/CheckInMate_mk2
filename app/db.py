# app/db.py
import os

from dotenv import load_dotenv
from sqlalchemy import create_engine
from sqlalchemy.engine import URL
from sqlalchemy.orm import sessionmaker

# .env 로드
load_dotenv()

# 환경변수 읽기
DB_SERVER = os.getenv("DB_SERVER")
DB_DATABASE = os.getenv("DB_DATABASE", "checkInMate_Database")
DB_USER = os.getenv("DB_USER")
DB_PASSWORD = os.getenv("DB_PASSWORD")

if not all([DB_SERVER, DB_DATABASE, DB_USER, DB_PASSWORD]):
    raise RuntimeError("DB 환경변수(DB_SERVER, DB_DATABASE, DB_USER, DB_PASSWORD)가 설정되어 있지 않습니다.")

# ----------------------------
# ODBC 접속 문자열 (Azure SQL)
# ----------------------------
odbc_connect_str = (
    "DRIVER={ODBC Driver 18 for SQL Server};"
    f"SERVER={DB_SERVER};"
    f"DATABASE={DB_DATABASE};"
    f"UID={DB_USER};"
    f"PWD={DB_PASSWORD};"
    "Encrypt=yes;"
    "TrustServerCertificate=yes;"
    "Connection Timeout=30;"
)

connection_url = URL.create(
    "mssql+pyodbc",
    query={"odbc_connect": odbc_connect_str},
)

# SQLAlchemy Engine 생성
engine = create_engine(
    connection_url,
    pool_pre_ping=True,        # 죽은 커넥션 자동 감지
    fast_executemany=True,     # 대량 insert 성능 개선
)

# Session 팩토리
SessionLocal = sessionmaker(
    bind=engine,
    autocommit=False,
    autoflush=False,
)


# FastAPI 의존성용 헬퍼
def get_db():
    """
    FastAPI dependency로 사용할 DB 세션 생성/정리 함수.
    """
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
