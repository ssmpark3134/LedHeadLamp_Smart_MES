import streamlit as st
import pandas as pd
from datetime import date
from src.queries import (
    get_production_list_for_quality,
    insert_quality,
    update_lot_qty_by_quality
)
from src.ui import (
    setup_page,
    page_title,
    show_database_status
)
# ============================================
# 페이지 기본 설정
setup_page("품질검사")
page_title(
    title="품질검사\n",
    description="생산된 제품의 양품 및 불량 수량을 검사하는 화면\n",
    tables="production,quality\n",
    task="품질검사 등록"
)
show_database_status()

# ============================================
# 품질검사 등록
st.divider()
st.header("🔍 품질검사 등록")

production_list = [
    dict(row)
    for row in get_production_list_for_quality()
]

if not production_list:
    st.info("품질검사를 등록할 생산실적이 없습니다.")
    st.stop()

# ============================================
# 생산실적 선택
selected_production = st.selectbox(
    "검사할 생산실적",
    production_list,
    format_func=lambda x:
        f"{x['production_no']} - "
        f"{x['item_name']} - "
        f"{x['production_qty']:,}개"
)
# 선택한 생산실적의 생산수량
production_qty = selected_production["production_qty"]

# ============================================
# 생산수량 표시
st.info(
    f"검사 대상 생산수량: **{production_qty:,}개**"
)
# ============================================
# 양품 수량
good_qty = st.number_input(
    "양품 수량",
    min_value=0,
    max_value=production_qty,
    value=production_qty,
    step=1
)

# ============================================
# 불량 수량
defect_qty = st.number_input(
    "불량 수량",
    min_value=0,
    max_value=production_qty,
    value=0,
    step=1
)

# ============================================
# 수량 검증
total_qty = good_qty + defect_qty
if total_qty != production_qty:
    st.warning(
        f"양품({good_qty:,}) + "
        f"불량({defect_qty:,}) = "
        f"{total_qty:,}개입니다.\n\n"
        f"생산수량 {production_qty:,}개와 "
        f"일치해야 합니다."
    )

# ============================================
# 불량 사유
defect_reason = st.text_input(
    "불량 사유",
    placeholder="불량이 있는 경우 입력하세요."
)

# ============================================
# 검사자
inspector_name = st.text_input(
    "검사자",
    placeholder="검사자 이름을 입력하세요."
)

# ============================================
# 검사일
inspection_date = st.date_input(
    "검사일",
    value=date.today()
)
# ============================================
# 품질검사 결과
if good_qty > 0 and defect_qty > 0:

    st.info(
        f"검사 결과: "
        f"양품 **{good_qty:,}개 → 합격** / "
        f"불량 **{defect_qty:,}개 → 불합격**"
    )

elif good_qty > 0 and defect_qty == 0:

    st.success(
        f"검사 결과: "
        f"양품 **{good_qty:,}개 → 합격**"
    )

elif good_qty == 0 and defect_qty > 0:

    st.error(
        f"검사 결과: "
        f"불량 **{defect_qty:,}개 → 불합격**"
    )

# ============================================
# 품질검사 등록
if st.button(
    "🔍 품질검사 등록",
    type="primary"
):
    # 양품 + 불량 = 생산수량인지 확인한다.
    if good_qty + defect_qty != production_qty:
        st.error(
            "양품 수량과 불량 수량의 합이 "
            "생산수량과 일치하지 않습니다."
        )
        st.stop()


    # 불량품이 있는데 불량 사유가 없는 경우
    if defect_qty > 0 and not defect_reason.strip():
        st.warning(
            "불량품이 존재하는 경우 "
            "불량 사유를 입력해주세요."
        )
        st.stop()

    # 검사자 입력 여부 확인
    if not inspector_name.strip():
        st.warning(
            "검사자 이름을 입력해주세요."
        )
        st.stop()

    # 검사 결과 db등록
    insert_quality(
        production_id=selected_production["production_id"],
        result = "합격" if defect_qty == 0 else "불합격",
        good_qty=good_qty,
        defect_qty=defect_qty,
        defect_reason=defect_reason,
        inspector_name=inspector_name,
        inspection_date=inspection_date.isoformat()
    )

    # ============================================
    # 품질검사 결과를 완제품 LOT 재고에 반영
    update_lot_qty_by_quality(
        production_id=selected_production["production_id"],
        good_qty=good_qty
    )

    st.success(
        f"{selected_production['production_no']} "
        f"품질검사가 등록되었습니다."
    )
    st.rerun()