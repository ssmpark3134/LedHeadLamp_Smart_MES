from datetime import date

import streamlit as st

from src.queries import get_production_list_for_quality, insert_quality, update_lot_qty_by_quality
from src.sensor_queries import (
    format_timestamp,
    get_auto_inspection,
    get_current_sensor_status,
    start_auto_inspection,
)
from src.ui import page_title, setup_page, show_database_status


setup_page("품질검사")
page_title(
    title="품질검사\n",
    description="완제품 LOT 대표 샘플 자동검사와 MES 최종 품질승인을 등록합니다.\n",
    tables="production,quality,lot / sensor inspection_results\n",
    task="LOT 샘플 자동검사 후 최종 품질승인",
)
show_database_status()
st.divider()
st.header("🔍 품질검사 등록")

production_list = [dict(row) for row in get_production_list_for_quality()]
if not production_list:
    st.info("품질검사를 등록할 완제품 LOT가 없습니다.")
    st.stop()

selected_production = st.selectbox(
    "검사 대상 완제품 LOT",
    production_list,
    format_func=lambda item: (
        f"{item['lot_no']} - {item['item_name']} - {item['production_qty']:,} EA"
    ),
)
st.info(
    f"**LOT:** {selected_production['lot_no']}  \n"
    f"**품목:** {selected_production['item_name']}  \n"
    f"**생산일:** {selected_production['production_date']}  \n"
    f"**생산수량:** {selected_production['production_qty']:,} EA  \n"
    "**검사방식:** LOT 대표 샘플 자동검사 / **샘플수량:** 1 EA  \n"
    "**MES 품질상태:** 검사대기"
)


@st.fragment(run_every=1)
def inspection_panel():
    production_id = selected_production["production_id"]
    lot_id = selected_production["lot_id"]
    lot_no = selected_production["lot_no"]

    st.subheader("📡 자동 센서 검사")
    if st.button("자동 센서 검사 시작", type="primary"):
        try:
            start_auto_inspection(production_id, lot_id, lot_no)
        except ValueError as exc:
            st.error(str(exc))
        else:
            st.success(f"{lot_no}을(를) 현재 자동검사 대상으로 설정했습니다.")

    state, sensor = get_current_sensor_status()
    auto_result = get_auto_inspection(production_id)
    target_matches = bool(
        state
        and state.get("active_production_id") == production_id
        and state.get("active_lot_id") == lot_id
        and state.get("active_lot_no") == lot_no
    )
    state_name = state["state"] if target_matches else "NOT_STARTED"
    state_labels = {
        "NOT_STARTED": "미검사", "READY": "검사 대기",
        "INSPECTING": "검사 중", "SENSOR_ERROR": "검사 조건 이상",
        "SAFETY_STOP": "안전 중단",
        "PASS": "검사 합격", "WAIT_REMOVE": "제품 제거 대기",
    }
    product_present = bool(sensor and 0 < sensor["distance"] <= 8.0)
    col1, col2 = st.columns(2)
    col1.metric("제품 감지", "제품 있음" if product_present else "제품 없음")
    col2.metric("검사 상태", state_labels.get(state_name, state_name))

    if state_name == "SAFETY_STOP":
        reason_labels = {
            "FIRE": "화재 감지", "HIT": "충격 감지", "TILT": "기울기 이상"
        }
        reasons = [
            reason_labels.get(item, item)
            for item in (state.get("safety_reason") or "").split(",")
            if item
        ]
        st.error(
            f"**중단 원인:** {', '.join(reasons) if reasons else '확인 필요'}  \n"
            "설비/안전 상태를 정상화하고 제품을 제거한 후 "
            "다시 검사하세요."
        )

    if sensor:
        col1, col2, col3, col4 = st.columns(4)
        col1.metric("Temperature", f"{sensor['temperature']:.1f} °C")
        col2.metric("Humidity", f"{sensor['humidity']:.1f} %")
        col3.metric("CdS", int(sensor["cds"]))
        col4.metric("Distance", f"{sensor['distance']:.1f} cm")

    if auto_result:
        st.success(
            f"**자동검사:** {auto_result['final_result']}  \n"
            f"**검사 ID:** {auto_result['inspection_id']}  \n"
            f"**샘플수량:** {auto_result['sample_qty']} EA  \n"
            f"**Temperature / Humidity / CdS:** {auto_result['temperature']:.1f} °C / "
            f"{auto_result['humidity']:.1f} % / {auto_result['cds']}  \n"
            f"**검사시간:** {format_timestamp(auto_result['created_at'])}"
        )
    else:
        st.info("이 LOT에 연결된 자동검사 PASS 결과가 없습니다.")

    st.divider()
    st.subheader("✅ MES 최종 품질 판정")
    production_qty = selected_production["production_qty"]
    good_qty = st.number_input("양품 수량", 0, production_qty, production_qty, key=f"good_{production_id}")
    defect_qty = st.number_input("불량 수량", 0, production_qty, 0, key=f"defect_{production_id}")
    defect_reason = st.text_input("불량 사유", key=f"reason_{production_id}")
    inspector_name = st.text_input("검사자", key=f"inspector_{production_id}")
    inspection_date = st.date_input("검사일", value=date.today(), key=f"date_{production_id}")
    final_pass = defect_qty == 0 and good_qty == production_qty
    auto_pass = bool(
        auto_result
        and auto_result["final_result"] == "PASS"
        and state_name != "SAFETY_STOP"
    )
    if final_pass and not auto_pass:
        st.warning("최종 합격 등록은 이 LOT의 자동검사 PASS 후 가능합니다.")

    if st.button("최종 품질 판정 등록", key=f"quality_{production_id}"):
        if state_name == "SAFETY_STOP":
            st.error("안전 중단 상태에서는 MES 최종 품질 합격을 등록할 수 없습니다.")
            st.stop()
        if good_qty + defect_qty != production_qty:
            st.error("양품과 불량 수량의 합이 생산수량과 같아야 합니다.")
            st.stop()
        if defect_qty > 0 and not defect_reason.strip():
            st.error("불량품이 있으면 불량 사유를 입력해야 합니다.")
            st.stop()
        if not inspector_name.strip():
            st.error("검사자를 입력해야 합니다.")
            st.stop()
        result = "합격" if final_pass else "불합격"
        try:
            insert_quality(production_id, result, good_qty, defect_qty, defect_reason,
                           inspector_name, inspection_date.isoformat())
            update_lot_qty_by_quality(production_id, good_qty)
        except ValueError as exc:
            st.error(str(exc))
            st.stop()
        st.success(f"{lot_no} MES 최종 품질 판정이 등록되었습니다.")
        st.rerun()


inspection_panel()
