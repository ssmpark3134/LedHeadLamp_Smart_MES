import pandas as pd
import streamlit as st

from src.queries import (
    activate_item,
    deactivate_item,
    get_item_list,
    get_reactivate_item_list,
    insert_item,
    update_item,
)
from src.ui import page_title, setup_page, show_database_status, show_dataframe


setup_page("Item-품목관리")

page_title(
    title="품목관리",
    description="품목 정보를 조회하고 관리하는 화면",
    tables="item",
    task="품목 조회 및 CRUD",
)
show_database_status()

items_dict = [dict(item) for item in get_item_list()]
reactivate_items = [dict(item) for item in get_reactivate_item_list()]

list_tab, create_tab, update_tab, status_tab = st.tabs(
    ["📦 품목 조회", "➕ 품목 등록", "✏️ 품목 수정", "⚙️ 사용 관리"]
)


with list_tab:
    st.subheader("등록 품목")
    show_dataframe(
        pd.DataFrame(items_dict),
        empty_message="등록된 품목 데이터가 없습니다.",
    )


with create_tab:
    st.subheader("새 품목 등록")

    with st.form("item_create_form"):
        item_code = st.text_input("품목 코드")
        item_name = st.text_input("품목명")
        item_type = st.selectbox("품목 종류", ["FG", "RM"])
        unit = st.text_input("단위", value="EA")
        create_submitted = st.form_submit_button("품목 등록", type="primary")

    if create_submitted:
        insert_item(item_code, item_name, item_type, unit)
        st.success("품목이 등록되었습니다.")
        st.rerun()


with update_tab:
    st.subheader("품목 정보 수정")

    if not items_dict:
        st.info("수정할 품목이 없습니다.")
    else:
        selected_item = st.selectbox(
            "수정할 품목 선택",
            items_dict,
            format_func=lambda item: (
                f"{item['item_code']} - {item['item_name']}"
            ),
            key="update_item_select",
        )

        with st.form("item_update_form"):
            update_name = st.text_input(
                "품목명",
                value=selected_item["item_name"],
            )
            update_type = st.selectbox(
                "품목 타입",
                ["FG", "RM"],
                index=0 if selected_item["item_type"] == "FG" else 1,
            )
            update_unit = st.text_input(
                "단위",
                value=selected_item["unit"],
            )
            update_submitted = st.form_submit_button(
                "변경사항 저장",
                type="primary",
            )

        if update_submitted:
            update_item(
                selected_item["item_id"],
                update_name,
                update_type,
                update_unit,
            )
            st.success("품목 정보가 수정되었습니다.")
            st.rerun()


with status_tab:
    stop_col, resume_col = st.columns(2)

    with stop_col:
        with st.container(border=True):
            st.subheader("품목 사용 중지")
            st.caption("사용 중인 품목을 비활성 상태로 변경합니다.")

            if not items_dict:
                st.info("사용 중지할 품목이 없습니다.")
            else:
                selected_deactivate = st.selectbox(
                    "사용 중지할 품목",
                    items_dict,
                    format_func=lambda item: (
                        f"{item['item_code']} - {item['item_name']}"
                    ),
                    key="deactivate_item",
                )

                if st.button("사용 중지", key="deactivate_button"):
                    deactivate_item(selected_deactivate["item_id"])
                    st.warning("품목이 비활성화되었습니다.")
                    st.rerun()

    with resume_col:
        with st.container(border=True):
            st.subheader("품목 사용 재개")
            st.caption("비활성 품목을 다시 사용할 수 있게 변경합니다.")

            if not reactivate_items:
                st.info("현재 비활성화된 품목이 없습니다.")
            else:
                selected_reactivate = st.selectbox(
                    "사용 재개할 품목",
                    reactivate_items,
                    format_func=lambda item: (
                        f"{item['item_code']} - {item['item_name']}"
                    ),
                    key="reactivate_item",
                )

                if st.button("사용 재개", key="reactivate_button"):
                    activate_item(selected_reactivate["item_id"])
                    st.success("품목 사용이 재개되었습니다.")
                    st.rerun()