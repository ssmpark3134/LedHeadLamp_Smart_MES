import streamlit as st
import pandas as pd
from datetime import date
from src.queries import (
    get_fg_item_list,
    insert_production_order,
    get_production_order_list
)
from src.ui import (
    setup_page,
    page_title,
    show_database_status
)
# ============================================
# 페이지 기본 설정
setup_page("생산지시")
page_title(
    title="생산지시\n",
    description="완제품 생산을 위한 생산지시를 등록하는 화면\n",
    tables="production_order,item\n",
    task="생산지시 등록"
)
show_database_status()

# ============================================
# 생산지시 등록
st.divider()
st.header("🏭 생산지시 등록")

# DB에서 완제품 목록을 조회한다.
fg_items = [
    dict(item)
    for item in get_fg_item_list()
]

# 완제품이 없는 경우
if not fg_items:
    st.warning("등록된 완제품이 없습니다.")
    st.stop()

# ============================================
# 생산할 완제품 선택
selected_fg = st.selectbox(
    "생산할 완제품",
    fg_items,
    format_func=lambda x:
        f"{x['item_code']} - {x['item_name']}"
)

# ============================================
# 생산 지시 수량
order_qty = st.number_input(
    "생산 지시 수량",
    min_value=1,
    value=1000,
    step=1
)

# ============================================
# 납기일
due_date = st.date_input(
    "납기일",
    value=date.today()
)

# ============================================
# 생산지시 등록
if st.button("🏭 생산지시 등록", type="primary"):
    insert_production_order(
        product_item_id=selected_fg["item_id"],
        order_qty=order_qty,
        due_date=due_date.isoformat()
    )
    st.success(
        f"{selected_fg['item_name']} "
        f"{order_qty:,}개 생산지시가 등록되었습니다."
    )
    st.rerun()
# ============================================
# 생산지시 목록
# ============================================
st.divider()
st.header("📋 생산지시 목록")
order_list = [
    dict(row)
    for row in get_production_order_list()
]

if order_list:
    order_df = pd.DataFrame(order_list)
    order_df = order_df[
        [
            "order_no",
            "item_code",
            "item_name",
            "order_qty",
            "due_date",
            "status"
        ]
    ]
    order_df.columns = [
        "생산지시번호",
        "완제품 코드",
        "완제품명",
        "지시 수량",
        "납기일",
        "상태"
    ]

    st.dataframe(
        order_df,
        use_container_width=True,
        hide_index=True
    )
else:
    st.info("등록된 생산지시가 없습니다.")