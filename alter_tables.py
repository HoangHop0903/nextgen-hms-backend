import sys
import os

sys.path.append(os.getcwd())

from app.core.database import engine
from sqlalchemy import text

def add_columns():
    statements = [
        "ALTER TABLE BenhNhan ADD AnhDaiDien VARCHAR(255);",
        "ALTER TABLE BacSi ADD AnhDaiDien VARCHAR(255);",
        "ALTER TABLE NhanVien ADD AnhDaiDien VARCHAR(255);"
    ]
    with engine.begin() as conn:
        for stmt in statements:
            try:
                conn.execute(text(stmt))
                print(f"Executed: {stmt}")
            except Exception as e:
                print(f"Error executing {stmt}: {e}")

if __name__ == "__main__":
    add_columns()
