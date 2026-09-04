import json
import serial
import time
from datetime import datetime
from urllib import error, request

SERIAL_PORT = "COM7"
BAUD_RATE = 115200

API_URL = "http://127.0.0.1:8000/sensor"

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
print(f"API URL     : {API_URL}")
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

            # --------------------------------------------------
            # FastAPI 전송 (검사 판정은 API에서 수행)
            # --------------------------------------------------

            payload = json.dumps({
                "temperature": temperature,
                "humidity": humidity,
                "distance": distance,
                "tilt": tilt,
                "hit": hit,
                "cds": cds,
                "fire": fire,
            }).encode("utf-8")
            api_request = request.Request(
                API_URL,
                data=payload,
                headers={"Content-Type": "application/json"},
                method="POST",
            )
            try:
                with request.urlopen(api_request, timeout=3) as response:
                    response.read()
                print("API 전송 완료")
            except (error.URLError, TimeoutError) as exc:
                print(f"API 전송 실패: {exc}")
            print("------------------------------------------")

except KeyboardInterrupt:
    print("\n센서 데이터 수집기를 종료합니다.")

finally:

    ser.close()
