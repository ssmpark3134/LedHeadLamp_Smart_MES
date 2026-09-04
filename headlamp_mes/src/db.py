from pathlib import Path
import sqlite3
import pandas as pd

BASE_DIR = Path(__file__).resolve().parent.parent
DB_PATH = BASE_DIR /'sql'/'headlamp_mes.db'

def database_exists() -> bool:
    return DB_PATH.exists()

def get_connection() -> sqlite3.Connection:
    if not database_exists():
        raise FileNotFoundError(f"SQLite 데이터베이스 파일을 찾을 수 없습니다: {DB_PATH}")

    connection = sqlite3.connect(DB_PATH)
    connection.row_factory = sqlite3.Row  # 안의 내용 가져오기
    connection.execute("PRAGMA foreign_keys = ON")
    return connection

# pandas 데이터 프레임 변환
def fetch_dataframe(sql: str, params: tuple = ()) -> pd.DataFrame:
    with get_connection() as connection:
        return pd.read_sql_query(sql, connection, params=params)
# 하나의 데이터 조회 
def fetch_one(sql: str, params: tuple = ()) -> sqlite3.Row | None:
    with get_connection() as connection:
        cursor = connection.execute(sql, params)
        return cursor.fetchone()
# 여러 데이터 조회
def fetch_all(sql: str, params: tuple = ()) -> list[sqlite3.Row]:
    with get_connection() as connection:
        cursor = connection.execute(sql, params)
        return cursor.fetchall()
# 데이터를 변경하는 sql문 실행
def execute(sql: str, params : tuple = ()):
    with get_connection() as connection:
        cursor = connection.execute(sql, params)
        connection.commit()
        return cursor.rowcount