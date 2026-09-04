import sqlite3
import serial
import time
from datetime import datetime

# --------------------------------------------------
# 설정
# --------------------------------------------------

SERIAL_PORT = "COM7"
BAUD_RATE = 115200

DB_FILE = "sensor_data.db"

# --------------------------------------------------
# 데이터베이스 연결
# --------------------------------------------------

conn = sqlite3.connect(DB_FILE)

cursor = conn.cursor()

# --------------------------------------------------
# sensor_data 테이블 생성
# --------------------------------------------------

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

# --------------------------------------------------
# Arduino Serial 연결
# --------------------------------------------------

ser = serial.Serial(
    port=SERIAL_PORT,
    baudrate=BAUD_RATE,
    timeout=3
)

time.sleep(2)

print("Arduino Sensor Collector Started")
print(f"Serial Port : {SERIAL_PORT}")
print(f"Database    : {DB_FILE}")
print("------------------------------------------")

# --------------------------------------------------
# 센서 데이터 저장용 변수
# --------------------------------------------------

tilt = None
hit = None
cds = None
temperature = None
humidity = None
distance = None
fire = None

# --------------------------------------------------
# 데이터 수집
# --------------------------------------------------

try:

    while True:

        line = ser.readline().decode(
            "utf-8",
            errors="ignore"
        ).strip()

        if not line:
            continue

        # --------------------------------------------------
        # Arduino 데이터 분석
        # --------------------------------------------------

        if line.startswith("TILT"):

            tilt = int(
                line.split(":")[1].strip()
            )


        elif line.startswith("HIT"):

            hit = int(
                line.split(":")[1].strip()
            )


        elif line.startswith("CDS"):

            cds = int(
                line.split(":")[1].strip()
            )


        elif line.startswith("Temperature"):

            temperature = float(
                line.split(":")[1]
                .replace("C", "")
                .strip()
            )


        elif line.startswith("Humidity"):

            humidity = float(
                line.split(":")[1]
                .replace("%", "")
                .strip()
            )


        elif line.startswith("Distance"):

            distance = float(
                line.split(":")[1]
                .replace("cm", "")
                .strip()
            )


        elif line.startswith("FIRE Digital"):

            fire = int(
                line.split(":")[1].strip()
            )

            # --------------------------------------------------
            # 날짜 / 시간 생성
            # --------------------------------------------------

            now = datetime.now().strftime(
                "%Y-%m-%d %H:%M:%S"
            )

            # --------------------------------------------------
            # 현재 센서값 출력
            # --------------------------------------------------

            print()
            print(f"DateTime    : {now}")
            print("------------------------------------------")
            print(f"Temperature : {temperature:.1f} C")
            print(f"Humidity    : {humidity:.1f} %")
            print(f"Distance    : {distance:.1f} cm")
            print(f"Tilt        : {tilt}")
            print(f"Hit         : {hit}")
            print(f"CdS         : {cds}")
            print(f"Fire        : {fire}")
            print("------------------------------------------")

            # --------------------------------------------------
            # SQLite 저장
            # --------------------------------------------------

            cursor.execute(
                """
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
                """,
                (
                    temperature,
                    humidity,
                    distance,
                    tilt,
                    hit,
                    cds,
                    fire,
                    now
                )
            )

            conn.commit()

            print("DB 저장 완료")
            print("------------------------------------------")


except KeyboardInterrupt:

    print("\n센서 데이터 수집기를 종료합니다.")


finally:

    ser.close()

    conn.close()