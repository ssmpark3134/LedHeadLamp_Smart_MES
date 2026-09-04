import streamlit as st
from datetime import date

from src.queries import (
    get_rm_item_list,
    insert_lot
)
from src.ui import (
    setup_page,
    page_title,
    show_database_status
)

# ============================================
# 페이지 기본 설정
setup_page("원자재 입고")
page_title(
    title="원자재 입고\n",
    description="원자재 입고 정보를 등록하고 LOT을 자동 생성하는 화면\n",
    tables="item,lot\n",
    task="원자재 입고 및 LOT 자동 생성"
)
show_database_status()

# ============================================
# 원자재 입고
st.divider()
st.header("🔩 원자재 입고")

# DB에서 원자재(RM) 목록을 조회한다.
rm_items = [
    dict(item)
    for item in get_rm_item_list()
]

if not rm_items:
    st.warning("등록된 원자재가 없습니다.")
    st.stop()

# ============================================
# 입고 품목 선택
selected_rm = st.selectbox(
    "원자재 선택",
    rm_items,
    format_func=lambda x:
        f"{x['item_code']} - {x['item_name']}"
)


# ============================================
# 입고 수량
received_qty = st.number_input(
    "입고 수량",
    min_value=1,
    value=1000,
    step=1
)
# ============================================
# 입고일
received_date = st.date_input(
    "입고일",
    value=date.today()
)

# ============================================
# 보관 위치
location = st.text_input(
    "보관 위치",
    value="원자재창고"
)

# ============================================
# 입고 처리
if st.button("📥 입고 처리", type="primary"):
    insert_lot(
        item_id=selected_rm["item_id"],
        lot_qty=received_qty,
        received_date=received_date.isoformat(),
        location=location
    )
    st.success(
        f"{selected_rm['item_name']} "
        f"{received_qty:,}개가 입고되었습니다."
    )
    st.info(
        "입고와 동시에 LOT 번호가 자동으로 생성되었습니다."
    )
    st.rerun()