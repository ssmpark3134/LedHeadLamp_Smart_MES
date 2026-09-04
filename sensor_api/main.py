import sqlite3
from datetime import datetime
from pathlib import Path

from fastapi import FastAPI


app = FastAPI()

DB_FILE = Path(__file__).resolve().parent / "sensor_data.db"

TEMPERATURE_MIN = 20.0
TEMPERATURE_MAX = 28.0
HUMIDITY_MIN = 48.0
HUMIDITY_MAX = 58.0
CDS_MIN = 50
CDS_MAX = 200
PRODUCT_DISTANCE_MAX = 8.0
PASS_HOLD_SECONDS = 2.0


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

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS inspection_results (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            temperature REAL NOT NULL,
            humidity REAL NOT NULL,
            distance REAL NOT NULL,
            cds INTEGER NOT NULL,
            temperature_result TEXT NOT NULL,
            humidity_result TEXT NOT NULL,
            cds_result TEXT NOT NULL,
            final_result TEXT NOT NULL,
            created_at TEXT NOT NULL
        )
    """)

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS inspection_state (
            id INTEGER PRIMARY KEY CHECK (id = 1),
            state TEXT NOT NULL,
            last_result TEXT,
            inspection_started_at TEXT,
            normal_started_at TEXT,
            updated_at TEXT NOT NULL
        )
    """)

    state_columns = {
        row[1] for row in cursor.execute("PRAGMA table_info(inspection_state)")
    }
    if "inspection_started_at" not in state_columns:
        cursor.execute(
            "ALTER TABLE inspection_state ADD COLUMN inspection_started_at TEXT"
        )
    if "normal_started_at" not in state_columns:
        cursor.execute(
            "ALTER TABLE inspection_state ADD COLUMN normal_started_at TEXT"
        )
    for column_name, column_type in (
        ("active_production_id", "INTEGER"),
        ("active_lot_id", "INTEGER"),
        ("active_lot_no", "TEXT"),
        ("safety_reason", "TEXT"),
    ):
        if column_name not in state_columns:
            cursor.execute(
                f"ALTER TABLE inspection_state ADD COLUMN {column_name} {column_type}"
            )

    result_columns = {
        row[1] for row in cursor.execute("PRAGMA table_info(inspection_results)")
    }
    for column_name, column_type in (
        ("production_id", "INTEGER"),
        ("lot_id", "INTEGER"),
        ("lot_no", "TEXT"),
        ("sample_qty", "INTEGER NOT NULL DEFAULT 1"),
    ):
        if column_name not in result_columns:
            cursor.execute(
                f"ALTER TABLE inspection_results ADD COLUMN {column_name} {column_type}"
            )

    cursor.execute("""
        INSERT OR IGNORE INTO inspection_state (id, state, last_result, updated_at)
        VALUES (1, 'READY', NULL, ?)
    """, (datetime.now().strftime("%Y-%m-%d %H:%M:%S"),))

    conn.commit()
    conn.close()


init_db()


@app.get("/")
def root():
    return {
        "message": "Sensor API running",
        "database": str(DB_FILE),
    }


@app.post("/sensor")
def receive_sensor(data: dict):
    now_datetime = datetime.now()
    now = now_datetime.isoformat(timespec="microseconds")

    conn = sqlite3.connect(DB_FILE)
    cursor = conn.cursor()
    cursor.execute("BEGIN IMMEDIATE")

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

    cursor.execute("""
        SELECT state, inspection_started_at, normal_started_at,
               active_production_id, active_lot_id, active_lot_no,
               safety_reason
        FROM inspection_state
        WHERE id = 1
    """)
    (
        inspection_state,
        _,
        normal_started_at,
        active_production_id,
        active_lot_id,
        active_lot_no,
        safety_reason,
    ) = cursor.fetchone()
    product_present = 0 < data["distance"] <= PRODUCT_DISTANCE_MAX
    safety_reasons = [
        name for name, value in (
            ("TILT", data["tilt"]),
            ("HIT", data["hit"]),
            ("FIRE", data["fire"]),
        )
        if value == 1
    ]
    safety_abnormal = bool(safety_reasons)
    current_safety_reason = ",".join(safety_reasons)

    temperature_result = (
        "PASS" if TEMPERATURE_MIN <= data["temperature"] <= TEMPERATURE_MAX
        else "FAIL"
    )
    humidity_result = (
        "PASS" if HUMIDITY_MIN <= data["humidity"] <= HUMIDITY_MAX
        else "FAIL"
    )
    cds_result = "PASS" if CDS_MIN <= data["cds"] <= CDS_MAX else "FAIL"
    quality_normal = all(result == "PASS" for result in (
        temperature_result, humidity_result, cds_result
    ))

    if inspection_state in ("PASS", "WAIT_REMOVE"):
        inspection_state = "WAIT_REMOVE" if product_present else "READY"
        cursor.execute("""
            UPDATE inspection_state
            SET state = ?, inspection_started_at = NULL,
                normal_started_at = NULL, safety_reason = NULL, updated_at = ?
            WHERE id = 1
        """, (inspection_state, now))
    elif inspection_state == "SAFETY_STOP":
        if not safety_abnormal and not product_present:
            inspection_state = "READY"
            safety_reason = None
        elif safety_abnormal:
            safety_reason = current_safety_reason
        cursor.execute("""
            UPDATE inspection_state
            SET state = ?, last_result = NULL, inspection_started_at = NULL,
                normal_started_at = NULL, safety_reason = ?, updated_at = ?
            WHERE id = 1
        """, (inspection_state, safety_reason, now))
    elif safety_abnormal and product_present:
        inspection_state = "SAFETY_STOP"
        cursor.execute("""
            UPDATE inspection_state
            SET state = ?, last_result = NULL, inspection_started_at = NULL,
                normal_started_at = NULL, safety_reason = ?, updated_at = ?
            WHERE id = 1
        """, (inspection_state, current_safety_reason, now))
    elif not product_present:
        inspection_state = "READY"
        cursor.execute("""
            UPDATE inspection_state
            SET state = ?, last_result = NULL, inspection_started_at = NULL,
                normal_started_at = NULL, safety_reason = NULL, updated_at = ?
            WHERE id = 1
        """, (inspection_state, now))
    elif inspection_state in ("READY", "INSPECTING", "SENSOR_ERROR"):
        if not quality_normal:
            inspection_state = "SENSOR_ERROR"
            cursor.execute("""
                UPDATE inspection_state SET state = ?, last_result = NULL,
                    normal_started_at = NULL, safety_reason = NULL, updated_at = ?
                WHERE id = 1
            """, (inspection_state, now))
        else:
            if normal_started_at is None:
                normal_started_at = now
            normal_since = datetime.fromisoformat(normal_started_at)
            normal_elapsed = (now_datetime - normal_since).total_seconds()
            inspection_started_at = now if inspection_state == "READY" else None
            inspection_state = "INSPECTING"

            if normal_elapsed >= PASS_HOLD_SECONDS:
                cursor.execute("""
                    INSERT INTO inspection_results (
                        temperature, humidity, distance, cds,
                        temperature_result, humidity_result, cds_result,
                        final_result, created_at,
                        production_id, lot_id, lot_no, sample_qty
                    )
                    VALUES (?, ?, ?, ?, ?, ?, ?, 'PASS', ?, ?, ?, ?, 1)
                """, (
                    data["temperature"], data["humidity"], data["distance"],
                    data["cds"], temperature_result, humidity_result,
                    cds_result, now, active_production_id, active_lot_id,
                    active_lot_no
                ))
                inspection_state = "PASS"

            cursor.execute("""
                UPDATE inspection_state
                SET state = ?, last_result = ?,
                    inspection_started_at = COALESCE(inspection_started_at, ?),
                    normal_started_at = ?, safety_reason = NULL, updated_at = ?
                WHERE id = 1
            """, (
                inspection_state,
                "PASS" if inspection_state == "PASS" else None,
                inspection_started_at,
                normal_started_at,
                now
            ))
    conn.commit()
    conn.close()

    print("DB 저장 완료:", data)

    return {
        "status": "ok",
        "inspection_state": inspection_state,
        "created_at": now
    }
