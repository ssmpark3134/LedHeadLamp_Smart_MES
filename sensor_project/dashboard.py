import streamlit as st
import sqlite3
import pandas as pd
import time

DB_FILE = "sensor_data.db"

st.set_page_config(
    page_title="Arduino Sensor Monitor",
    layout="wide"
)

st.title("Arduino Sensor 실시간 모니터링")

# --------------------------------------------------
# DB에서 가장 최근 데이터 조회
# --------------------------------------------------

def get_latest_data():

    conn = sqlite3.connect(DB_FILE)

    query = """
    SELECT
        temperature,
        humidity,
        distance,
        tilt,
        hit,
        cds,
        fire,
        created_at
    FROM sensor_data
    ORDER BY id DESC
    LIMIT 1
    """

    df = pd.read_sql_query(query, conn)

    conn.close()

    return df


# --------------------------------------------------
# 실시간 화면
# --------------------------------------------------

placeholder = st.empty()

while True:

    df = get_latest_data()

    with placeholder.container():

        if df.empty:

            st.warning("저장된 센서 데이터가 없습니다.")

        else:

            data = df.iloc[0]

            st.subheader(
                f"최근 측정 시간 : {data['created_at']}"
            )

            # ------------------------------------------
            # 첫 번째 줄
            # ------------------------------------------

            col1, col2, col3 = st.columns(3)

            col1.metric(
                "온도",
                f"{data['temperature']:.1f} °C"
            )

            col2.metric(
                "습도",
                f"{data['humidity']:.1f} %"
            )

            col3.metric(
                "거리",
                f"{data['distance']:.1f} cm"
            )

            # ------------------------------------------
            # 두 번째 줄
            # ------------------------------------------

            col4, col5, col6, col7 = st.columns(4)

            col4.metric(
                "Tilt",
                int(data["tilt"])
            )

            col5.metric(
                "Hit",
                int(data["hit"])
            )

            col6.metric(
                "CdS",
                int(data["cds"])
            )

            col7.metric(
                "Fire",
                int(data["fire"])
            )

    # 2초마다 DB 다시 조회
    time.sleep(2)