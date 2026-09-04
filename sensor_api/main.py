import sqlite3
from datetime import datetime
from pathlib import Path

from fastapi import FastAPI


app = FastAPI()

DB_FILE = Path(__file__).parent / "sensor_data.db"


def init_db():
    conn = sqlite3.connect(DB_FILE)
    cursor = conn.cursor()

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS sensor_data (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            temperature REAL NOT NULL,
            humidity REAL NOT NULL,
            distance REAL NOT NULL,
            tilt INTEGER NOT NULL,
            hit INTEGER NOT NULL,
            cds INTEGER NOT NULL,
            fire INTEGER NOT NULL,
            created_at TEXT NOT NULL
        )
    """)

    conn.commit()
    conn.close()


init_db()


@app.get("/")
def root():
    return {"message": "Sensor API running"}


@app.post("/sensor")
def receive_sensor(data: dict):
    now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    conn = sqlite3.connect(DB_FILE)
    cursor = conn.cursor()

    cursor.execute("""
        INSERT INTO sensor_data (
            temperature,
            humidity,
            distance,
            tilt,
            hit,
            cds,
            fire,
            created_at
        )
        VALUES (?, ?, ?, ?, ?, ?, ?, ?)
    """, (
        data["temperature"],
        data["humidity"],
        data["distance"],
        data["tilt"],
        data["hit"],
        data["cds"],
        data["fire"],
        now
    ))

    conn.commit()
    conn.close()

    print("DB 저장 완료:", data)

    return {
        "status": "ok",
        "created_at": now
    }
