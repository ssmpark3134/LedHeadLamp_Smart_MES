from datetime import datetime
from pathlib import Path
import sqlite3


SENSOR_DB_PATH = (
    Path(__file__).resolve().parents[2] / "sensor_api" / "sensor_data.db"
)


def get_sensor_connection():
    connection = sqlite3.connect(SENSOR_DB_PATH, timeout=5)
    connection.row_factory = sqlite3.Row
    return connection


def format_timestamp(value):
    if not value:
        return "-"
    try:
        return datetime.fromisoformat(str(value)).strftime("%Y-%m-%d-%H:%M:%S")
    except ValueError:
        return str(value)


def start_auto_inspection(production_id, lot_id, lot_no):
    now = datetime.now().isoformat(timespec="microseconds")
    with get_sensor_connection() as connection:
        connection.execute("BEGIN IMMEDIATE")
        current = connection.execute(
            "SELECT state FROM inspection_state WHERE id = 1"
        ).fetchone()
        if current and current["state"] == "SAFETY_STOP":
            raise ValueError(
                "안전 중단 상태입니다. 설비/안전 상태를 정상화하고 "
                "제품을 제거한 후 다시 시작하세요."
            )
        connection.execute(
            """
            UPDATE inspection_state
            SET state = 'READY', last_result = NULL,
                inspection_started_at = NULL, normal_started_at = NULL,
                safety_reason = NULL,
                active_production_id = ?, active_lot_id = ?, active_lot_no = ?,
                updated_at = ?
            WHERE id = 1
            """,
            (production_id, lot_id, lot_no, now),
        )


def get_current_sensor_status():
    with get_sensor_connection() as connection:
        state = connection.execute(
            "SELECT * FROM inspection_state WHERE id = 1"
        ).fetchone()
        sensor = connection.execute(
            "SELECT * FROM sensor_data ORDER BY id DESC LIMIT 1"
        ).fetchone()
    return (dict(state) if state else None, dict(sensor) if sensor else None)


def get_auto_inspection(production_id):
    with get_sensor_connection() as connection:
        row = connection.execute(
            """
            SELECT id AS inspection_id, production_id, lot_id, lot_no,
                   sample_qty, final_result, temperature, humidity, distance,
                   cds, created_at
            FROM inspection_results
            WHERE production_id = ?
            ORDER BY id DESC
            LIMIT 1
            """,
            (production_id,),
        ).fetchone()
    return dict(row) if row else None


def get_auto_inspections():
    with get_sensor_connection() as connection:
        rows = connection.execute(
            """
            SELECT id AS inspection_id, production_id, lot_id, lot_no,
                   sample_qty, final_result, temperature, humidity, distance,
                   cds, created_at
            FROM inspection_results
            WHERE production_id IS NOT NULL
            ORDER BY id DESC
            """
        ).fetchall()
    return [dict(row) for row in rows]


def has_passed_auto_inspection(production_id):
    inspection = get_auto_inspection(production_id)
    return bool(inspection and inspection["final_result"] == "PASS")
