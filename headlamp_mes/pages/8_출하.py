import streamlit as st
from datetime import date
from src.queries import (
    get_shippable_lot_list,
    insert_shipment
)
from src.ui import (
    setup_page,
    page_title,
    show_database_status
)
# ============================================
# 페이지 기본 설정
setup_page("출하")
page_title(
    title="출하\n",
    description="품질검사가 완료된 완제품 LOT를 고객에게 출하하는 화면\n",
    tables="lot,shipment\n",
    task="완제품 출하 등록 및 재고 차감"
)
show_database_status()

# ============================================
# 출하 등록
st.divider()
st.header("🚚 출하 등록")
lot_list = [
    dict(row)
    for row in get_shippable_lot_list()
]

if not lot_list:
    st.info(
        "현재 출하 가능한 완제품 LOT가 없습니다."
    )
    st.stop()


# ============================================
# 출하 LOT 선택
selected_lot = st.selectbox(
    "출하 LOT 선택",
    lot_list,
    format_func=lambda x:
        f"{x['lot_no']} - "
        f"{x['item_name']} "
        f"(재고 {x['current_qty']:,}개)"
)

# ============================================
# 현재 LOT 정보 표시
st.info(
    f"""
    **LOT 번호:** {selected_lot['lot_no']}
    **품목:** {selected_lot['item_name']}
    **현재 재고:** {selected_lot['current_qty']:,}개
    """
)

# ============================================
# 고객명 입력
customer_name = st.text_input(
    "고객명",
    placeholder="고객명을 입력하세요."
)

# ============================================
# 고객 PO 입력
customer_po = st.text_input(
    "고객 PO",
    placeholder="고객 발주번호가 있다면 입력하세요."
)

# ============================================
# 출하수량 입력
shipment_qty = st.number_input(
    "출하수량",
    min_value=1,
    max_value=selected_lot["current_qty"],
    value=min(1000, selected_lot["current_qty"]),
    step=1
)

# ============================================
# 출하일
shipment_date = st.date_input(
    "출하일",
    value=date.today()
)

# ============================================
# 출하 등록
if st.button(
    "🚚 출하 등록",
    type="primary"
):
    # 고객명 입력 여부 확인
    if not customer_name.strip():
        st.warning(
            "고객명을 입력해주세요."
        )
        st.stop()

    # 출하수량이 현재 재고를 초과하는지 확인
    if shipment_qty > selected_lot["current_qty"]:
        st.warning(
            "출하수량이 현재 LOT 재고를 초과할 수 없습니다."
        )
        st.stop()

    # 출하 등록
    insert_shipment(
        lot_id=selected_lot["lot_id"],
        customer_name=customer_name,
        customer_po=customer_po,
        shipment_qty=shipment_qty,
        shipment_date=shipment_date.isoformat()
    )

    st.success(
        f"{selected_lot['lot_no']}에서 "
        f"{shipment_qty:,}개가 출하되었습니다."
    )
    st.rerun()