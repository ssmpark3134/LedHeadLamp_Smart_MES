import serial
import time
import requests
from datetime import datetime

SERIAL_PORT = "COM7"
BAUD_RATE = 115200
API_URL = "http://localhost:8000/sensor"

ser = serial.Serial(
    port=SERIAL_PORT,
    baudrate=BAUD_RATE,
    timeout=3
)

time.sleep(2)

print("Arduino Sensor Collector Started")
print(f"Serial Port : {SERIAL_PORT}")
print(f"API Server  : {API_URL}")
print("------------------------------------------")

tilt = None
hit = None
cds = None
temperature = None
humidity = None
distance = None
fire = None

try:
    while True:
        line = ser.readline().decode(
            "utf-8",
            errors="ignore"
        ).strip()

        if not line:
            continue

        if line.startswith("TILT"):
            tilt = int(line.split(":")[1].strip())

        elif line.startswith("HIT"):
            hit = int(line.split(":")[1].strip())

        elif line.startswith("CDS"):
            cds = int(line.split(":")[1].strip())

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
            fire = int(line.split(":")[1].strip())

            now = datetime.now().strftime(
                "%Y-%m-%d %H:%M:%S"
            )

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

            sensor_data = {
                "temperature": temperature,
                "humidity": humidity,
                "distance": distance,
                "tilt": tilt,
                "hit": hit,
                "cds": cds,
                "fire": fire
            }

            response = requests.post(
                API_URL,
                json=sensor_data,
                timeout=5
            )

            response.raise_for_status()

            print("WSL API 전송 완료")
            print("------------------------------------------")

except KeyboardInterrupt:
    print("\n센서 데이터 수집기를 종료합니다.")

finally:
    ser.close()