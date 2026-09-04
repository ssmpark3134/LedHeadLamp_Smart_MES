import streamlit as st
import pandas as pd
from src.queries import (
    get_lot_tracking_list,
    get_forward_lot_tracking,
    get_backward_lot_tracking
)
from src.ui import (
    setup_page,
    page_title,
    show_database_status
)
# ============================================
# 페이지 기본 설정
# ============================================
setup_page("LOT 추적")
page_title(
    title="LOT 추적\n",
    description="원자재 LOT와 완제품 LOT의 정방향 및 역방향 추적을 조회하는 화면\n",
    tables="lot,production,production_material,shipment,item\n",
    task="LOT 기준 생산 및 출하 이력 추적"
)
show_database_status()

# ============================================
# LOT 추적 화면
# ============================================
st.divider()
st.header("🔎 LOT 추적")

# ============================================
# 정방향 / 역방향 탭
# ============================================
forward_tab, backward_tab = st.tabs(
    [
        "➡️ 정방향 추적",
        "⬅️ 역방향 추적"
    ]
)

# ============================================================
# 정방향 추적
# 원자재 LOT → 생산 → 완제품 LOT → 출하
# ============================================================
with forward_tab:

    st.subheader("➡️ 정방향 추적")

    st.caption(
        "원자재 LOT에서 출발하여 "
        "생산된 완제품 LOT와 출하 이력을 추적합니다."
    )

    st.divider()

    # ============================================
    # 원자재 LOT 목록 조회
    # ============================================
    rm_lots = [
        dict(row)
        for row in get_lot_tracking_list()
        if row["item_type"] == "RM"
    ]


    if not rm_lots:

        st.warning(
            "등록된 원자재 LOT가 없습니다."
        )

    else:

        selected_rm_lot = st.selectbox(
            "원자재 LOT 선택",
            rm_lots,
            format_func=lambda x:
                f"{x['lot_no']} - {x['item_name']}",
            key="forward_lot"
        )


        # ========================================
        # 선택한 원자재 LOT 기본정보
        # ========================================

        st.divider()
        st.subheader("📦 원자재 LOT 정보")

        col1, col2, col3, col4 = st.columns(4)

        col1.metric(
            "LOT 번호",
            selected_rm_lot["lot_no"]
        )

        col2.metric(
            "품목",
            selected_rm_lot["item_name"]
        )

        col3.metric(
            "전체 수량",
            f"{selected_rm_lot['lot_qty']:,} EA"
        )

        col4.metric(
            "현재 재고",
            f"{selected_rm_lot['current_qty']:,} EA"
        )

    # ============================================
    # 원자재 LOT → 생산 → 완제품 LOT 추적
    # ============================================

    tracking_list = [
        dict(row)
        for row in get_forward_lot_tracking(
            selected_rm_lot["lot_id"]
        )
    ]

    st.divider()
    st.subheader("🏭 생산 추적")

    if not tracking_list:

        st.info(
            "현재 이 원자재 LOT가 사용된 생산실적이 없습니다."
        )

    else:

    # ========================================
    # 생산 이력 3개씩 카드 형태로 표시
    # ========================================
        for start in range(0, len(tracking_list), 3):

            row_items = tracking_list[start:start + 3]

            cols = st.columns(3)

            for col, tracking in zip(cols, row_items):

                with col:

                    with st.container(border=True):

                        # --------------------------------
                        # 생산실적 기본 정보
                        # --------------------------------

                        st.markdown(
                            f"**🏭 {tracking['production_no']}**"
                        )

                        st.caption(
                            f"{tracking['production_date']}"
                        )

                        st.write(
                            f"작업자: **{tracking['worker_name']}**"
                        )

                        st.write(
                            f"설비: **{tracking['equipment_name']}**"
                        )

                        # --------------------------------
                        # 생산 수량
                        # --------------------------------

                        st.metric(
                            "생산수량",
                            f"{tracking['production_qty']:,} EA"
                        )

                        st.write(
                            f"원자재 사용: "
                            f"**{tracking['used_qty']:,} EA**"
                        )

                        st.divider()

                        # --------------------------------
                        # 생산된 완제품
                        # --------------------------------

                        st.markdown("**📦 완제품 LOT**")

                        st.write(
                            tracking["output_lot_no"]
                        )

                        st.caption(
                            tracking["output_item_name"]
                        )

                        st.write(
                            f"LOT 수량: "
                            f"**{tracking['output_lot_qty']:,} EA**"
                        )

                        st.write(
                            f"현재 재고: "
                            f"**{tracking['output_current_qty']:,} EA**"
                        )

                        st.write(
                            f"보관 위치: "
                            f"**{tracking['output_location']}**"
                        )

        # ========================================
        # 추가 LOT 정보
        # ========================================

        st.write(
            f"**품목 코드:** {selected_rm_lot['item_code']}"
        )

        st.write(
            f"**보관 위치:** {selected_rm_lot['location']}"
        )

        if selected_rm_lot["received_date"]:

            st.write(
                f"**입고일:** {selected_rm_lot['received_date']}"
            )

# ============================================================
# 역방향 추적
# FG LOT → 생산 → RM LOT → 출하
# ============================================================

with backward_tab:

    st.subheader("⬅️ 역방향 추적")

    st.caption(
        "완제품 LOT에서 출발하여 "
        "생산정보, 사용된 원자재 LOT, 출하정보를 추적합니다."
    )

    st.divider()

    # ========================================
    # 1. 완제품 LOT 목록
    # ========================================

    fg_lots = [
        dict(row)
        for row in get_lot_tracking_list()
        if row["item_type"] == "FG"
    ]

    if not fg_lots:

        st.warning(
            "등록된 완제품 LOT가 없습니다."
        )

    else:

        selected_fg_lot = st.selectbox(
            "완제품 LOT 선택",
            fg_lots,
            format_func=lambda x:
                f"{x['lot_no']} - {x['item_name']}",
            key="backward_lot"
        )

        # ========================================
        # 2. 완제품 LOT 기본정보
        # ========================================

        st.divider()
        st.subheader("📦 완제품 LOT 정보")

        col1, col2, col3, col4 = st.columns([3.5, 3.5, 1, 1])

        col1.metric(
            "LOT 번호",
            selected_fg_lot["lot_no"]
        )

        col2.metric(
            "품목",
            selected_fg_lot["item_name"]
        )

        col3.metric(
            "생산수량",
            f"{selected_fg_lot['lot_qty']:,} EA"
        )

        col4.metric(
            "현재 재고",
            f"{selected_fg_lot['current_qty']:,} EA"
        )

        # ========================================
        # 3. 역방향 추적 데이터 조회
        # ========================================

        tracking_list = [
            dict(row)
            for row in get_backward_lot_tracking(
                selected_fg_lot["lot_id"]
            )
        ]

        if not tracking_list:

            st.warning(
                "이 완제품 LOT에 연결된 "
                "생산정보가 없습니다."
            )

        else:

            # ====================================
            # 4. 생산정보
            # ====================================

            production = tracking_list[0]

            st.divider()
            st.subheader("🏭 생산정보")

            col1, col2, col3 = st.columns(3)

            col1.write(
                f"**생산번호**  \n"
                f"{production['production_no']}"
            )

            col2.write(
                f"**생산일**  \n"
                f"{production['production_date']}"
            )

            col3.metric(
                "생산수량",
                f"{production['production_qty']:,} EA"
            )

            col1, col2 = st.columns(2)

            col1.write(
                f"**작업자**  \n"
                f"{production['worker_name']}"
            )

            col2.write(
                f"**생산설비**  \n"
                f"{production['equipment_name']}"
            )

            # ====================================
            # 5. 사용 원자재 LOT
            # ====================================

            st.divider()
            st.subheader("🧩 사용 원자재 LOT")

            for start in range(
                0,
                len(tracking_list),
                3
            ):

                row_items = tracking_list[
                    start:start + 3
                ]

                cols = st.columns(3)

                for col, material in zip(
                    cols,
                    row_items
                ):

                    with col:

                        with st.container(
                            border=True
                        ):

                            st.markdown(
                                f"**🧱 "
                                f"{material['material_name']}**"
                            )

                            st.caption(
                                material["material_code"]
                            )

                            st.write(
                                f"원자재 LOT  \n"
                                f"**{material['material_lot_no']}**"
                            )

                            st.metric(
                                "사용수량",
                                f"{material['used_qty']:,} EA"
                            )

                            st.write(
                                f"LOT 전체수량: "
                                f"**{material['material_lot_qty']:,} EA**"
                            )

                            st.write(
                                f"현재 재고: "
                                f"**{material['material_current_qty']:,} EA**"
                            )

                            st.write(
                                f"보관위치: "
                                f"**{material['material_location']}**"
                            )

            # ====================================
            # 6. 출하정보
            # ====================================

            st.divider()
            st.subheader("🚚 출하정보")

            shipment = tracking_list[0]

            if shipment["customer_name"] is None:

                st.info(
                    "아직 출하되지 않은 "
                    "완제품 LOT입니다."
                )

            else:

                col1, col2, col3 = st.columns(3)

                col1.write(
                    f"**거래처**  \n"
                    f"{shipment['customer_name']}"
                )

                col2.write(
                    f"**출하일**  \n"
                    f"{shipment['shipment_date']}"
                )

                col3.metric(
                    "출하수량",
                    f"{shipment['shipment_qty']:,} EA"
                )

                if shipment["customer_po"]:

                    st.write(
                        f"**고객 PO**  \n"
                        f"{shipment['customer_po']}"
                    )
 