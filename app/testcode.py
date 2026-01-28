# app/testcode.py
from sqlalchemy import text
from app.db.db import engine

with engine.connect() as conn:
    stmt = text("SELECT TOP (1) name FROM sys.tables;")
    result = conn.execute(stmt)
    rows = result.fetchall()
    print(rows)
