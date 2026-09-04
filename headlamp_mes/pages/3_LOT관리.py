import streamlit as st
import pandas as pd

from src.queries import (
    get_fg_stock_list,
    get_rm_stock_list,
    get_lot_list,
    get_fg_item_list, 
    get_rm_item_list, 
    insert_lot
)
from src.ui import (
    setup_page,
    page_title,
    show_database_status,
    show_dataframe,
)


# ============================================
# 페이지 기본 설정
setup_page("LOT 관리")
page_title(
    title="LOT 관리\n",
    description="품목별 재고와 LOT 정보를 조회하는 화면\n",
    tables="lot,item\n",
    task="재고 및 LOT 조회"
)
show_database_status()
# ============================================
# LOT 상세 조회
st.divider()
st.header("📋 LOT 상세")
lot_list = [
    dict(row)
    for row in get_lot_list()
]
if lot_list:
    lot_df = pd.DataFrame(lot_list)
    lot_df = lot_df[
        [
            "lot_no",
            "item_code",
            "item_name",
            "item_type",
            "lot_qty",
            "current_qty",
            "received_date",
            "produced_date",
            "location"
        ]
    ]
    lot_df.columns = [
        "LOT 번호",
        "품목 코드",
        "품목명",
        "품목 종류",
        "전체 수량",
        "현재 수량",
        "입고일",
        "생산일",
        "보관 위치"
    ]
    st.dataframe(
        lot_df,
        use_container_width=True,
        hide_index=True
    )
else:
    st.info("등록된 LOT이 없습니다.")

# ============================================
# 완제품 재고 조회
st.divider()
st.header("📦 완제품 재고")
fg_stock = [
    dict(row)
    for row in get_fg_stock_list()
]
if fg_stock:
    fg_df = pd.DataFrame(fg_stock)
    fg_df.columns = [
        "품목 코드",
        "품목명",
        "단위",
        "현재 재고"
    ]
    st.dataframe(
        fg_df,
        use_container_width=True,
        hide_index=True
    )
else:
    st.info("현재 완제품 재고가 없습니다.")

# ============================================
# 원자재 재고 조회
st.divider()
st.header("🔩 원자재 재고")
rm_stock = [
    dict(row)
    for row in get_rm_stock_list()
]
if rm_stock:
    rm_df = pd.DataFrame(rm_stock)
    rm_df.columns = [
        "품목 코드",
        "품목명",
        "단위",
        "현재 재고"
    ]
    st.dataframe(
        rm_df,
        use_container_width=True,
        hide_index=True
    )
else:
    st.info("현재 원자재 재고가 없습니다.")
