import streamlit as st
from datetime import date
from src.queries import (
    get_production_order_list,
    insert_production,
    get_production_order_progress,
    update_production_order_status,
    get_today_production_list,
    get_remaining_production_order_list
)
from src.ui import (
    setup_page,
    page_title,
    show_database_status,
    metric_row,
    row_to_dict
)
# ============================================
# 페이지 기본 설정
# ============================================
setup_page("생산실적")
page_title(
    title="생산실적\n",
    description="생산지시에 따라 실제 생산된 수량을 등록하는 화면\n",
    tables="production_order,production,lot\n",
    task="생산실적 등록 및 완제품 LOT 자동생성"
)
show_database_status()
# ============================================
#오늘 생산 현황
# ============================================
st.divider()
st.header("📊 오늘 생산현황")

today_production_list = [
    dict(row)
    for row in get_today_production_list()
]
if not today_production_list:
    st.info("오늘 등록된 생산실적이 없습니다.")
else:
    # 오늘 생산 건수
    today_production_count = len(today_production_list)
    # 오늘 총 생산수량 계산
    today_total_qty = sum(
        row["production_qty"]
        for row in today_production_list
    )
    

    # --------------------------------------------
    # 오늘 생산실적 요약
    # --------------------------------------------
    metric_row([
        ("오늘 생산 건수", f"{today_production_count}건"),
        ("오늘 총 생산수량", f"{today_total_qty:,}개")
    ])

    # --------------------------------------------
    # 오늘 생산실적 상세
    # --------------------------------------------
    for start in range(0, len(today_production_list), 3):
        row_items = today_production_list[start:start+3]
        cols = st.columns(3)
        for col,production in zip(cols, row_items):
            with col:
                with st.container(border=True):
                    st.markdown(
                        f"**🏭 "
                        f"{production['production_no']}**"
                    )

                    st.caption(
                        production["item_name"]
                    )

                    st.write(
                        f"생산수량: "
                        f"**{production['production_qty']:,}개**"
                    )

                    st.write(
                        f"작업자: "
                        f"{production['worker_name']}"
                    )

                    st.write(
                        f"설비: "
                        f"{production['equipment_name']}"
                    )
# ============================================
# 남은 작업지시
# ============================================
st.divider()
st.header("📋 남은 작업지시")
remaining_order_list = [
    row_to_dict(row) for row in get_remaining_production_order_list()
]
if not remaining_order_list:
    st.success("현재 남은 생산 작업지시가 없습니다.")
else:
    for start in range(0, len(remaining_order_list), 3):
        row_items = remaining_order_list[start:start + 3]
        cols = st.columns(3)
        for col, order in zip(cols, row_items):
            with col:
                with st.container(border = True):
                    st.markdown(
                        f"**📋 "
                        f"{order['order_no']}**"
                    )

                    st.caption(
                        order["item_name"]
                    )

                    st.write(
                        f"지시수량: "
                        f"**{order['order_qty']:,}개**"
                    )

                    st.write(
                        f"생산수량: "
                        f"**{order['produced_qty']:,}개**"
                    )

                    st.write(
                        f"남은수량: "
                        f"**{order['remaining_qty']:,}개**"
                    )

                    st.write(
                        f"납기일: "
                        f"{order['due_date']}"
                    )

# ============================================
# 생산실적 등록
# ============================================
st.divider()
st.header("🏭 생산실적 등록")

order_list = [
    row_to_dict(row)
    for row in get_production_order_list()
    if row["status"] != "완료"
]

if not order_list:
    st.success("등록된 생산지시가 없습니다.")
else:
    # ========================================
    # 생산지시 선택
    # ========================================
    selected_order = st.selectbox(
        "생산지시 선택",
        order_list,
        format_func=lambda x:
            f"{x['order_no']} - "
            f"{x['item_name']} "
            f"({x['order_qty']:,}개)",
        key="production_order_select"
    )

    # ============================================
    # 선택한 생산지시 조회
    progress = get_production_order_progress(
        selected_order["order_id"]
    )

    order_qty = progress["order_qty"]
    produced_qty = progress["produced_qty"]

    remaining_qty = order_qty - produced_qty

    # ============================================
    # 생산지시 진행상황 표시
    metric_row([
        (
            "생산지시 수량",
            f"{order_qty:,}개"
        ),
        (
            "현재 생산 수량",
            f"{produced_qty:,}개"
        ),
        (
            "남은 생산 수량",
            f"{remaining_qty:,}개"
        )
    ])

    # ============================================
    # 작업자 입력
    worker_name = st.text_input(
        "작업자",
        placeholder="작업자 이름을 입력하세요."
    )

    # ============================================
    # 생산 설비 입력
    equipment_name = st.text_input(
        "생산 설비",
        placeholder="예: 조립라인-01"
    )

    # ============================================
    # 생산일
    production_date = st.date_input(
        "생산일",
        value=date.today()
    )

    # ============================================
    # 실제 생산수량
    production_qty = st.number_input(
        "실제 생산수량",
        min_value=1,
        max_value=max(1, remaining_qty),
        value=min(1000, max(1, remaining_qty)),
        step=1
    )

    # ============================================
    # 생산실적 등록
    if st.button(
        "🏭 생산실적 등록",
        type="primary"
    ):
        # 작업자 입력 여부 확인
        if not worker_name.strip():
            st.warning("작업자 이름을 입력해주세요.")
            st.stop()

        # 설비 입력 여부 확인
        if not equipment_name.strip():
            st.warning("생산 설비를 입력해주세요.")
            st.stop()

        # 실제 생산수량이 생산지시 수량을 초과하는지 확인
        if production_qty > remaining_qty:
            st.warning(
                "실제 생산수량이 남은 생산수량을 초과할 수 없습니다."
            )
            st.stop()

        # 생산실적 db등록
        insert_production(
            order_id=selected_order["order_id"],
            worker_name=worker_name,
            equipment_name=equipment_name,
            production_date=production_date.isoformat(),
            production_qty=production_qty
        )
        if production_qty == remaining_qty:
            update_production_order_status(
                selected_order["order_id"],
                "완료"
            )
        st.success(
            f"{selected_order['item_name']} "
            f"{production_qty:,}개 생산실적이 등록되었습니다."
        )
        st.info(
            "생산실적 등록과 동시에 완제품 LOT가 자동 생성되었습니다."
        )
        st.rerun()