import html
import sqlite3
import time
from pathlib import Path

import altair as alt
import pandas as pd
import streamlit as st

from src.ui import page_title, section_title, setup_page


SENSOR_DB = Path(__file__).resolve().parents[2] / "sensor_api" / "sensor_data.db"
TEMPERATURE_RANGE = (20.0, 28.0)
HUMIDITY_RANGE = (48.0, 58.0)
CDS_RANGE = (50, 200)
DISTANCE_LIMIT = 8.0


setup_page("센서 모니터링")
page_title(
    title="IoT 설비 · 자동검사 모니터링",
    description="실시간 센서 데이터와 LOT 대표 샘플 자동 품질검사 상태를 모니터링합니다.",
    tables="sensor_data, inspection_state, inspection_results",
    task="설비 상태 및 자동검사 실시간 관제",
)

st.markdown(
    """
    <style>
    .sensor-kpi {
        --status: #64748b;
        background: #fff;
        border: 1px solid #dbe3ee;
        border-top: 4px solid var(--status);
        border-radius: 10px;
        min-height: 124px;
        padding: 16px 18px;
        box-shadow: 0 4px 14px rgba(15, 23, 42, .045);
    }
    .sensor-kpi-label { color:#64748b; font-size:.78rem; font-weight:750; }
    .sensor-kpi-value { color:#0f172a; font-size:1.35rem; font-weight:850; margin:8px 0 5px; }
    .sensor-kpi-note { color:#64748b; font-size:.72rem; line-height:1.35; }
    .sensor-reading {
        background:#fff; border:1px solid #dbe3ee; border-radius:10px;
        min-height:142px; padding:16px 18px;
    }
    .sensor-reading-label { color:#64748b; font-size:.78rem; font-weight:750; }
    .sensor-reading-value { color:#0f172a; font-size:1.55rem; font-weight:850; margin:7px 0 6px; }
    .sensor-reading-status { font-size:.76rem; font-weight:800; margin-bottom:5px; }
    .sensor-reading-range { color:#64748b; font-size:.7rem; }
    .status-green { color:#15803d; } .status-red { color:#dc2626; }
    .status-blue { color:#2563eb; } .status-amber { color:#b45309; }
    .status-gray { color:#64748b; }
    .sensor-live { color:#15803d; font-size:.78rem; font-weight:750; margin-bottom:8px; }
    </style>
    """,
    unsafe_allow_html=True,
)


def read_dashboard_data(limit):
    empty = pd.DataFrame()
    if not SENSOR_DB.exists():
        return empty, None, empty
    try:
        with sqlite3.connect(SENSOR_DB, timeout=3) as connection:
            sensor_df = pd.read_sql_query(
                """
                SELECT id, temperature, humidity, distance, tilt, hit, cds,
                       fire, created_at
                FROM sensor_data ORDER BY id DESC LIMIT ?
                """,
                connection,
                params=(limit + 1,),
            )
            try:
                state_row = connection.execute(
                    "SELECT state, last_result, updated_at, safety_reason "
                    "FROM inspection_state WHERE id=1"
                ).fetchone()
            except sqlite3.OperationalError:
                state_row = None

            result_columns = {
                row[1] for row in connection.execute("PRAGMA table_info(inspection_results)")
            }
            if result_columns:
                lot_expression = "lot_no" if "lot_no" in result_columns else "NULL AS lot_no"
                results_df = pd.read_sql_query(
                    f"""
                    SELECT id, {lot_expression}, temperature, humidity, cds,
                           final_result, created_at
                    FROM inspection_results ORDER BY id DESC LIMIT 20
                    """,
                    connection,
                )
            else:
                results_df = empty
    except (sqlite3.Error, pd.errors.DatabaseError):
        return empty, None, empty
    return sensor_df, state_row, results_df


def safe_number(value):
    return pd.to_numeric(pd.Series([value]), errors="coerce").iloc[0]


def in_range(value, lower, upper):
    return pd.notna(value) and lower <= value <= upper


def product_detected(distance):
    return pd.notna(distance) and 0 < distance <= DISTANCE_LIMIT


def format_timestamp(value):
    parsed = pd.to_datetime(value, errors="coerce")
    return parsed.strftime("%Y-%m-%d-%H:%M:%S") if pd.notna(parsed) else "-"


def status_card(column, label, value, note, color):
    with column:
        st.markdown(
            f"""
            <div class="sensor-kpi" style="--status:{color}">
                <div class="sensor-kpi-label">{html.escape(str(label))}</div>
                <div class="sensor-kpi-value">{html.escape(str(value))}</div>
                <div class="sensor-kpi-note">{html.escape(str(note))}</div>
            </div>
            """,
            unsafe_allow_html=True,
        )


def reading_card(column, label, value, status, normal_range, status_class):
    with column:
        st.markdown(
            f"""
            <div class="sensor-reading">
                <div class="sensor-reading-label">{html.escape(label)}</div>
                <div class="sensor-reading-value">{html.escape(value)}</div>
                <div class="sensor-reading-status {status_class}">{html.escape(status)}</div>
                <div class="sensor-reading-range">{html.escape(normal_range)}</div>
            </div>
            """,
            unsafe_allow_html=True,
        )


def range_chart(data, field, title, unit, lower, upper, color):
    base = alt.Chart(data).encode(
        x=alt.X("created_at:T", title="측정시간", axis=alt.Axis(format="%H:%M:%S", labelAngle=-35)),
    )
    band = base.mark_area(color="#22c55e", opacity=0.08).encode(
        y=alt.Y("lower:Q", title=f"{title} ({unit})", scale=alt.Scale(zero=False)),
        y2="upper:Q",
    ).transform_calculate(lower=str(lower), upper=str(upper))
    line = base.mark_line(color=color, strokeWidth=2).encode(
        y=alt.Y(f"{field}:Q", title=f"{title} ({unit})", scale=alt.Scale(zero=False)),
        tooltip=[
            alt.Tooltip("created_at:T", title="측정시간", format="%Y-%m-%d-%H:%M:%S"),
            alt.Tooltip(f"{field}:Q", title=title, format=".1f"),
        ],
    )
    limits = alt.Chart(pd.DataFrame({"limit": [lower, upper]})).mark_rule(
        color="#16a34a", strokeDash=[5, 4], opacity=0.8
    ).encode(y="limit:Q")
    return (band + limits + line).properties(height=265).interactive(bind_y=False)


def distance_chart(data):
    base = alt.Chart(data).encode(
        x=alt.X("created_at:T", title="측정시간", axis=alt.Axis(format="%H:%M:%S", labelAngle=-35))
    )
    line = base.mark_line(color="#475569", strokeWidth=2).encode(
        y=alt.Y("distance:Q", title="Distance (cm)"),
        tooltip=[
            alt.Tooltip("created_at:T", title="측정시간", format="%Y-%m-%d-%H:%M:%S"),
            alt.Tooltip("distance:Q", title="거리", format=".1f"),
            alt.Tooltip("detection_label:N", title="제품 감지"),
        ],
    )
    points = base.mark_point(size=45, filled=True).encode(
        y="distance:Q",
        color=alt.Color(
            "detection_label:N",
            scale=alt.Scale(domain=["제품 있음", "제품 없음"], range=["#16a34a", "#94a3b8"]),
            legend=alt.Legend(title=None, orient="top"),
        ),
    )
    threshold = alt.Chart(pd.DataFrame({"limit": [DISTANCE_LIMIT]})).mark_rule(
        color="#d97706", strokeDash=[6, 4]
    ).encode(y="limit:Q")
    return (line + points + threshold).properties(height=265).interactive(bind_y=False)


def rising_edge_events(data):
    chronological = data.sort_values("created_at").copy()
    events = []
    labels = {"hit": "HIT", "tilt": "TILT", "fire": "FIRE"}
    descriptions = {"hit": "충격 감지", "tilt": "기울기 이상", "fire": "화재 감지"}
    for field, label in labels.items():
        values = pd.to_numeric(chronological[field], errors="coerce").fillna(0).astype(int)
        edges = values.eq(1) & values.shift(1, fill_value=0).eq(0)
        for _, row in chronological.loc[edges].iterrows():
            events.append({
                "created_at": row["created_at"], "구분": label,
                "상태": descriptions[field],
            })
    return pd.DataFrame(events).sort_values("created_at", ascending=False) if events else pd.DataFrame()


range_options = {"최근 30건": 30, "최근 60건": 60, "최근 120건": 120, "최근 300건": 300}
selected_range = st.selectbox("조회 범위", range_options, index=1)
sensor_with_context, inspection_state_row, inspection_df = read_dashboard_data(range_options[selected_range])

if not SENSOR_DB.exists():
    st.error(f"센서 DB를 찾을 수 없습니다: {SENSOR_DB}")
elif sensor_with_context.empty:
    st.warning("저장된 센서 데이터가 없습니다. Arduino 수집기와 FastAPI 연결을 확인하세요.")
else:
    sensor_with_context["created_at"] = pd.to_datetime(sensor_with_context["created_at"], errors="coerce")
    sensor_with_context = sensor_with_context.dropna(subset=["created_at"]).sort_values("created_at")
    display_data = sensor_with_context.tail(range_options[selected_range]).copy()
    latest = display_data.iloc[-1]
    for field in ("temperature", "humidity", "distance", "cds"):
        display_data[field] = pd.to_numeric(display_data[field], errors="coerce")

    temperature = safe_number(latest["temperature"])
    humidity = safe_number(latest["humidity"])
    cds = safe_number(latest["cds"])
    distance = safe_number(latest["distance"])
    detected = product_detected(distance)
    inspection_state = inspection_state_row[0] if inspection_state_row else "READY"
    equipment_normal = not any(int(latest.get(field, 0) or 0) == 1 for field in ("tilt", "hit", "fire"))
    active_safety_labels = [
        label for field, label in (
            ("fire", "화재 감지"), ("hit", "충격 감지"), ("tilt", "기울기 이상")
        ) if int(latest.get(field, 0) or 0) == 1
    ]
    last_result = inspection_df.iloc[0]["final_result"] if not inspection_df.empty else "미검사"

    state_meta = {
        "READY": ("검사 대기", "#64748b", "샘플 진입 대기"),
        "INSPECTING": ("검사 중", "#2563eb", "정상 조건 2초 확인"),
        "SENSOR_ERROR": ("검사 조건 이상", "#dc2626", "정상 유지 타이머 초기화"),
        "SAFETY_STOP": (
            "SAFETY STOP", "#dc2626",
            "안전 정상화 후 제품을 제거하세요",
        ),
        "PASS": ("PASS", "#15803d", "LOT 대표 샘플 합격"),
        "WAIT_REMOVE": ("제품 제거 대기", "#d97706", "중복 검사 방지 중"),
    }
    inspection_label, inspection_color, inspection_note = state_meta.get(
        inspection_state, (inspection_state, "#dc2626", "알 수 없는 상태")
    )

    st.markdown('<div class="sensor-live">● LIVE · 1초 자동 새로고침</div>', unsafe_allow_html=True)
    kpi_columns = st.columns(4)
    status_card(kpi_columns[0], "설비 상태", "NORMAL" if equipment_normal else "ERROR",
                " · ".join(active_safety_labels) if active_safety_labels else "Tilt · Hit · Fire 정상",
                "#15803d" if equipment_normal else "#dc2626")
    status_card(kpi_columns[1], "제품 감지", "제품 있음" if detected else "제품 없음",
                f"현재 {distance:.1f} cm" if pd.notna(distance) else "거리 데이터 없음",
                "#15803d" if detected else "#64748b")
    status_card(kpi_columns[2], "검사 상태", inspection_label, inspection_note, inspection_color)
    status_card(kpi_columns[3], "최근 자동검사", last_result,
                "최근 inspection_results 기준", "#15803d" if last_result == "PASS" else "#64748b")
    if inspection_state == "SAFETY_STOP":
        stored_reason = inspection_state_row[3] if inspection_state_row else None
        reason_labels = {
            "FIRE": "화재 감지", "HIT": "충격 감지", "TILT": "기울기 이상"
        }
        reasons = [reason_labels.get(item, item) for item in (stored_reason or "").split(",") if item]
        st.error(
            f"자동검사가 설비/안전 이상으로 중단되었습니다. "
            f"원인: {', '.join(reasons) if reasons else '확인 필요'}. "
            "안전 상태를 정상화하고 제품을 제거한 후 다시 검사하세요."
        )

    section_title("현재 센서값")
    reading_columns = st.columns(4)
    reading_card(reading_columns[0], "Temperature", f"{temperature:.1f} °C" if pd.notna(temperature) else "-",
                 "정상" if in_range(temperature, *TEMPERATURE_RANGE) else "기준 이상",
                 "정상범위 20.0 ~ 28.0 °C", "status-green" if in_range(temperature, *TEMPERATURE_RANGE) else "status-red")
    reading_card(reading_columns[1], "Humidity", f"{humidity:.1f} %" if pd.notna(humidity) else "-",
                 "정상" if in_range(humidity, *HUMIDITY_RANGE) else "기준 이상",
                 "정상범위 48.0 ~ 58.0 %", "status-green" if in_range(humidity, *HUMIDITY_RANGE) else "status-red")
    reading_card(reading_columns[2], "HeadLamp CdS", f"{int(cds)}" if pd.notna(cds) else "-",
                 "정상" if in_range(cds, *CDS_RANGE) else "기준 이상",
                 "품질범위 50 ~ 200", "status-green" if in_range(cds, *CDS_RANGE) else "status-red")
    reading_card(reading_columns[3], "Distance", f"{distance:.1f} cm" if pd.notna(distance) else "-",
                 "제품 있음" if detected else "제품 없음",
                 "0 < Distance ≤ 8.0 cm", "status-green" if detected else "status-gray")

    section_title("검사 환경 모니터링")
    left, right = st.columns(2)
    with left:
        st.subheader("온도 추세")
        st.caption("정상범위 20.0 ~ 28.0 °C")
        st.altair_chart(range_chart(display_data, "temperature", "Temperature", "°C", 20.0, 28.0, "#2563eb"), width="stretch")
    with right:
        st.subheader("습도 추세")
        st.caption("정상범위 48.0 ~ 58.0 %")
        st.altair_chart(range_chart(display_data, "humidity", "Humidity", "%", 48.0, 58.0, "#0f766e"), width="stretch")

    section_title("제품 검사 센서")
    display_data["detection_label"] = display_data["distance"].apply(
        lambda value: "제품 있음" if product_detected(value) else "제품 없음"
    )
    left, right = st.columns(2)
    with left:
        st.subheader("HeadLamp 조도 검사 추세")
        st.caption("품질 정상범위 50 ~ 200")
        st.altair_chart(range_chart(display_data, "cds", "CdS", "value", 50, 200, "#7c3aed"), width="stretch")
    with right:
        st.subheader("제품 감지 거리")
        st.caption("8 cm 이내 제품 감지 · -1은 미감지")
        st.altair_chart(distance_chart(display_data), width="stretch")

    section_title("설비 이상 모니터링")
    all_events = rising_edge_events(sensor_with_context)
    if not all_events.empty:
        window_start = display_data["created_at"].min()
        events = all_events[all_events["created_at"] >= window_start].copy()
    else:
        events = all_events
    event_counts = events["구분"].value_counts().to_dict() if not events.empty else {}
    equipment_columns = st.columns(3)
    for column, field, label, alert_label in (
        (equipment_columns[0], "hit", "충격(Hit)", "충격 감지"),
        (equipment_columns[1], "tilt", "기울기(Tilt)", "기울기 이상"),
        (equipment_columns[2], "fire", "화재(Fire)", "화재 감지"),
    ):
        active = int(latest.get(field, 0) or 0) == 1
        status_card(column, label, alert_label if active else "현재 정상",
                    f"{selected_range} 이벤트 {event_counts.get(field.upper(), 0)}회",
                    "#dc2626" if active else "#15803d")

    if not events.empty:
        bucketed = events.copy()
        bucketed["시간대"] = bucketed["created_at"].dt.floor("min")
        bucketed = bucketed.groupby(["시간대", "구분"]).size().reset_index(name="이벤트 수")
        event_chart = alt.Chart(bucketed).mark_bar().encode(
            x=alt.X("시간대:T", title="시간", axis=alt.Axis(format="%H:%M")),
            y=alt.Y("이벤트 수:Q", title="발생 횟수", axis=alt.Axis(tickMinStep=1)),
            color=alt.Color("구분:N", scale=alt.Scale(domain=["HIT", "TILT", "FIRE"], range=["#d97706", "#2563eb", "#dc2626"])),
            tooltip=[alt.Tooltip("시간대:T", format="%Y-%m-%d-%H:%M"), "구분:N", "이벤트 수:Q"],
        ).properties(height=210)
        st.altair_chart(event_chart, width="stretch")
        event_display = events.head(20).copy()
        event_display["시간"] = event_display["created_at"].apply(format_timestamp)
        st.dataframe(event_display[["시간", "구분", "상태"]], width="stretch", hide_index=True)
    else:
        st.info(f"{selected_range} 내 설비 이상 이벤트가 없습니다.")

section_title("최근 자동검사 결과")
if inspection_df.empty:
    st.info("저장된 자동검사 결과가 없습니다.")
else:
    result_display = inspection_df.copy()
    result_display["검사시간"] = result_display["created_at"].apply(format_timestamp)
    result_display["lot_no"] = result_display["lot_no"].fillna("미연결")
    result_display = result_display.rename(columns={
        "lot_no": "LOT 번호", "temperature": "Temperature (°C)",
        "humidity": "Humidity (%)", "cds": "CdS", "final_result": "결과",
    })
    st.dataframe(result_display[["검사시간", "LOT 번호", "Temperature (°C)", "Humidity (%)", "CdS", "결과"]],
                 width="stretch", hide_index=True)

section_title("최근 센서 원본 데이터")
with st.expander("원본 데이터 표 열기"):
    if sensor_with_context.empty:
        st.info("표시할 센서 데이터가 없습니다.")
    else:
        raw_display = display_data.sort_values("created_at", ascending=False).copy()
        raw_display["시간"] = raw_display["created_at"].apply(format_timestamp)
        raw_display = raw_display.rename(columns={
            "temperature": "Temperature (°C)", "humidity": "Humidity (%)",
            "cds": "CdS", "distance": "Distance (cm)", "tilt": "Tilt",
            "hit": "Hit", "fire": "Fire",
        })
        st.dataframe(raw_display[["시간", "Temperature (°C)", "Humidity (%)", "CdS", "Distance (cm)", "Tilt", "Hit", "Fire"]],
                     width="stretch", hide_index=True)

time.sleep(1)
st.rerun()
