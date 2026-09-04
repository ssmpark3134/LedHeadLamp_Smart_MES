import streamlit as st
import pandas as pd
import matplotlib.pyplot as plt
from datetime import date, timedelta
from matplotlib.patches import Patch

from src import queries
from src import chart_queries

from src.ui import (
    setup_page,
    dashboard_hero,
    setup_matplotlib,
    section_title,
    subsection_title
)


# ============================================================
# 페이지 설정
# ============================================================

setup_page("Dashboard")
setup_matplotlib()


# ============================================================
# 데이터 조회
# ============================================================

try:

    # --------------------------------------------------------
    # 기본 MES 데이터
    # --------------------------------------------------------

    fg_stock = queries.get_fg_stock_list()

    rm_stock = queries.get_rm_stock_list()

    today_production = queries.get_today_production_list()

    remaining_orders = (
        queries.get_remaining_production_order_list()
    )


    # --------------------------------------------------------
    # Dashboard 차트 데이터
    # --------------------------------------------------------

    production_chart_list = (
        chart_queries.get_production_chart_list()
    )

    defect_rate_list = (
        chart_queries.get_defect_rate_list()
    )

    shipment_list = (
        chart_queries.get_shipment_dashboard_list()
    )


    # ========================================================
    # KPI 계산
    # ========================================================

    fg_total = sum(
        row["current_stock"]
        for row in fg_stock
    )

    rm_total = sum(
        row["current_stock"]
        for row in rm_stock
    )

    today_production_total = sum(
        row["production_qty"]
        for row in today_production
    )

    remaining_order_count = len(
        remaining_orders
    )

    quality_good_total = sum(
        row["good_qty"]
        for row in (defect_rate_list or [])
    )

    quality_defect_total = sum(
        row["defect_qty"]
        for row in (defect_rate_list or [])
    )

    quality_total = quality_good_total + quality_defect_total
    yield_rate = (
        quality_good_total / quality_total * 100
        if quality_total else 0
    )

    # ========================================================
    # 대시보드 상단 공장 요약
    # ========================================================

    dashboard_hero(
        title="LED Head Lamp Mini MES 운영 대시보드",
        description=(
            "원자재 입고부터 생산, 품질검사, 완제품 재고와 출하까지 "
            "현재 공장 상태를 한 화면에서 확인합니다."
        ),
        summary_items=[
            (f"{fg_total:,} EA", "현재 완제품 재고", "#dc3b3b"),
            (f"{yield_rate:.1f}%", "누적 품질 수율", "#22945f"),
            (f"{rm_total:,} EA", "현재 원자재 재고", "#2563eb")
        ],
        snapshot_items=[
            ("진행 생산지시", f"{remaining_order_count:,}건"),
            ("누적 불량 수량", f"{quality_defect_total:,} EA"),
            ("오늘 생산량", f"{today_production_total:,} EA")
        ]
    )


    # ========================================================
    # 주요 현황
    # ========================================================

    section_title(
        "주요 현황",
        "📌"
    )

    k1, k2, k3, k4 = st.columns(4)


    # --------------------------------------------------------
    # 완제품 재고
    # --------------------------------------------------------

    with k1:

        with st.container(border=True):

            st.metric(
                label="📦 완제품 재고",
                value=f"{fg_total:,} EA"
            )

            st.caption(
                "완제품 LOT 현재 재고"
            )


    # --------------------------------------------------------
    # 원자재 재고
    # --------------------------------------------------------

    with k2:

        with st.container(border=True):

            st.metric(
                label="🧱 원자재 재고",
                value=f"{rm_total:,} EA"
            )

            st.caption(
                "원자재 LOT 현재 재고"
            )


    # --------------------------------------------------------
    # 오늘 생산
    # --------------------------------------------------------

    with k3:

        with st.container(border=True):

            st.metric(
                label="🏭 오늘 생산량",
                value=f"{today_production_total:,} EA"
            )

            st.caption(
                "금일 생산실적 기준"
            )


    # --------------------------------------------------------
    # 진행 생산지시
    # --------------------------------------------------------

    with k4:

        with st.container(border=True):

            st.metric(
                label="📋 진행 생산지시",
                value=f"{remaining_order_count} 건"
            )

            st.caption(
                "완료되지 않은 생산지시"
            )


    # ========================================================
    # 완제품 재고
    # ========================================================

    section_title(
        "완제품 재고 현황",
        "📦"
    )


    if fg_stock:

        fg_df = pd.DataFrame(
            [
                dict(row)
                for row in fg_stock
            ]
        )


        left, right = st.columns(2)


        # ----------------------------------------------------
        # 완제품별 재고
        # ----------------------------------------------------

        with left:

            with st.container(border=True):

                subsection_title(
                    "완제품별 현재 재고",
                    "📈"
                )

                fig, ax = plt.subplots(
                    figsize=(6, 3.5)
                )

                ax.plot(
                    fg_df["item_name"],
                    fg_df["current_stock"],
                    marker="o",
                    linewidth=2.2,
                    markersize=6
                )

                ax.set_xlabel(
                    "완제품",
                    fontsize=9
                )

                ax.set_ylabel(
                    "현재 재고 (EA)",
                    fontsize=9
                )

                ax.set_title(
                    "완제품별 현재 재고",
                    fontweight="bold",
                    fontsize=11,
                    pad=10
                )

                ax.tick_params(
                    axis="x",
                    rotation=20,
                    labelsize=8
                )

                ax.tick_params(
                    axis="y",
                    labelsize=8
                )

                ax.grid(
                    axis="y",
                    alpha=0.25
                )

                plt.tight_layout()

                st.pyplot(
                    fig,
                    use_container_width=True,
                    bbox_inches=None
                )

                plt.close(fig)


        # ----------------------------------------------------
        # 완제품 재고 구성비
        # ----------------------------------------------------

        with right:

            with st.container(border=True):

                subsection_title(
                    "완제품 재고 구성비",
                    "🥧"
                )

                fig, ax = plt.subplots(
                    figsize=(6, 3.5)
                )

                ax.pie(
                    fg_df["current_stock"],
                    labels=fg_df["item_name"],
                    autopct="%1.1f%%",
                    startangle=90,
                    wedgeprops=dict(
                        width=0.42
                    ),
                    textprops=dict(
                        fontsize=7
                    )
                )

                ax.set_title(
                    "완제품 재고 구성비",
                    fontweight="bold",
                    fontsize=11,
                    pad=10
                )

                plt.tight_layout()

                st.pyplot(
                    fig,
                    use_container_width=True,
                    bbox_inches=None
                )

                plt.close(fig)


    else:

        st.info(
            "완제품 재고 데이터가 없습니다."
        )


    # ========================================================
    # 원자재 재고
    # ========================================================

    section_title(
        "원자재 재고 현황",
        "🧱"
    )


    if rm_stock:

        rm_df = pd.DataFrame(
            [
                dict(row)
                for row in rm_stock
            ]
        )


        left, right = st.columns(2)


        # ----------------------------------------------------
        # 원자재별 재고
        # ----------------------------------------------------

        with left:

            with st.container(border=True):

                subsection_title(
                    "원자재별 현재 재고",
                    "📊"
                )

                fig, ax = plt.subplots(
                    figsize=(6, 3.5)
                )

                ax.barh(
                    rm_df["item_name"],
                    rm_df["current_stock"]
                )

                ax.set_xlabel(
                    "현재 재고 (EA)",
                    fontsize=9
                )

                # 왼쪽 품목명은 표시
                ax.set_ylabel(
                    "원자재",
                    fontsize=9
                )

                ax.set_title(
                    "원자재별 현재 재고",
                    fontweight="bold",
                    fontsize=11,
                    pad=10
                )

                ax.tick_params(
                    axis="both",
                    labelsize=8
                )

                ax.grid(
                    axis="x",
                    alpha=0.25
                )

                plt.tight_layout()

                st.pyplot(
                    fig,
                    use_container_width=True,
                    bbox_inches=None
                )

                plt.close(fig)


        # ----------------------------------------------------
        # 원자재 재고 구성비
        # ----------------------------------------------------

        with right:

            with st.container(border=True):

                subsection_title(
                    "원자재 재고 구성비",
                    "🥧"
                )

                fig, ax = plt.subplots(
                    figsize=(6, 3.5)
                )

                ax.pie(
                    rm_df["current_stock"],
                    labels=rm_df["item_name"],
                    autopct="%1.1f%%",
                    startangle=90,
                    wedgeprops=dict(
                        width=0.42
                    ),
                    textprops=dict(
                        fontsize=7
                    )
                )

                ax.set_title(
                    "원자재 재고 구성비",
                    fontweight="bold",
                    fontsize=11,
                    pad=10
                )

                plt.tight_layout()

                st.pyplot(
                    fig,
                    use_container_width=True,
                    bbox_inches=None
                )

                plt.close(fig)


    else:

        st.info(
            "원자재 재고 데이터가 없습니다."
        )


    # ========================================================
    # 생산 / 품질
    # ========================================================

    section_title(
        "생산 / 품질 현황",
        "🏭"
    )


    if production_chart_list:

        date_options = [
            date.today() - timedelta(days=day_offset)
            for day_offset in range(30)
        ]

        selected_production_date = st.selectbox(
            "생산현황 조회 날짜",
            date_options,
            format_func=lambda selected_date: (
                f"{selected_date:%Y.%m.%d}"
                + (" (오늘)" if selected_date == date.today() else "")
            ),
            key="dashboard_production_date"
        )

        daily_production = chart_queries.get_daily_production_order_progress(
            selected_production_date.isoformat()
        )


        left, right = st.columns(2)


        # ====================================================
        # 품목별 생산 현황
        # ====================================================

        with left:

            with st.container(border=True):

                subsection_title(
                    "품목별 생산 현황",
                    "🏭"
                )


                if daily_production:
                    daily_df = pd.DataFrame(
                        [dict(row) for row in daily_production]
                    )

                    chart_df = (
                        daily_df
                        .groupby("item_code", as_index=False)
                        .agg(
                            item_name=("item_name", "first"),
                            order_qty=("order_qty", "sum"),
                            produced_qty=("produced_qty", "sum"),
                        )
                    )

                    fig, ax = plt.subplots(figsize=(6, 3.5))
                    colors = [
                        "#4C78A8",
                        "#F58518",
                        "#54A24B",
                        "#E45756",
                        "#8F63B8",
                        "#2CA6A4",
                    ]
                    legend_handles = []

                    for index, row in chart_df.iterrows():
                        color = colors[index % len(colors)]

                        ax.barh(
                            index,
                            row["order_qty"],
                            color=color,
                            alpha=0.25,
                            height=0.62,
                        )
                        ax.barh(
                            index,
                            row["produced_qty"],
                            color=color,
                            height=0.62,
                        )
                        ax.text(
                            row["produced_qty"],
                            index,
                            f" {row['produced_qty']:,} / {row['order_qty']:,}",
                            va="center",
                            fontsize=7,
                            fontweight="bold",
                        )
                        legend_handles.append(
                            Patch(facecolor=color, label=row["item_name"])
                        )

                    max_qty = max(
                        chart_df["order_qty"].max(),
                        chart_df["produced_qty"].max(),
                    )
                    ax.set_xlim(0, max_qty * 1.2 if max_qty else 1)
                    ax.set_yticks([])
                    ax.set_xlabel("수량 (EA)", fontsize=9)
                    ax.set_title(
                        f"{selected_production_date:%Y.%m.%d} 품목별 생산 현황",
                        fontweight="bold",
                        fontsize=11,
                        pad=10
                    )
                    ax.tick_params(axis="x", labelsize=8)
                    ax.grid(axis="x", alpha=0.25)
                    ax.legend(
                        handles=legend_handles,
                        title="완제품",
                        loc="upper right",
                        fontsize=6,
                        title_fontsize=7,
                        frameon=True,
                    )

                    plt.tight_layout()
                    st.pyplot(
                        fig,
                        use_container_width=True,
                        bbox_inches=None
                    )
                    plt.close(fig)

                    st.caption(
                        "연한 막대 = 생산지시량 / 진한 막대 = 선택일 생산량 "
                        "/ 숫자 = 생산량 · 지시량"
                    )
                else:
                    st.info("선택한 날짜에 등록된 생산실적이 없습니다.")


        # ====================================================
        # 전체 품질 현황
        # ====================================================

        with right:

            with st.container(border=True):

                subsection_title(
                    "전체 품질 현황",
                    "🔍"
                )


                if defect_rate_list:

                    defect_df = pd.DataFrame(
                        [
                            dict(row)
                            for row in defect_rate_list
                        ]
                    )


                    good_qty = (
                        defect_df["good_qty"]
                        .sum()
                    )

                    defect_qty = (
                        defect_df["defect_qty"]
                        .sum()
                    )

                    total_qty = (
                        good_qty
                        + defect_qty
                    )


                    if total_qty > 0:

                        defect_rate = (
                            defect_qty
                            / total_qty
                        ) * 100


                        fig, ax = plt.subplots(
                            figsize=(6, 3.5)
                        )


                        ax.pie(
                            [
                                good_qty,
                                defect_qty
                            ],
                            labels=[
                                "양품",
                                "불량"
                            ],
                            autopct="%1.1f%%",
                            startangle=90,
                            wedgeprops=dict(
                                width=0.42
                            ),
                            textprops=dict(
                                fontsize=8
                            )
                        )


                        ax.set_title(
                            f"전체 불량률 : "
                            f"{defect_rate:.1f}%",
                            fontweight="bold",
                            fontsize=11,
                            pad=10
                        )


                        plt.tight_layout()


                        st.pyplot(
                            fig,
                            use_container_width=True,
                            bbox_inches=None
                        )


                        plt.close(fig)


                    else:

                        st.info(
                            "품질검사 데이터가 없습니다."
                        )


                else:

                    st.info(
                        "품질검사 데이터가 없습니다."
                    )


    else:

        st.info(
            "생산지시 데이터가 없습니다."
        )


    # ========================================================
    # 출하 현황
    # ========================================================

    section_title(
        "출하 현황",
        "🚚"
    )

    if shipment_list:
        shipment_df = pd.DataFrame(
            [dict(row) for row in shipment_list]
        )
        shipment_df["shipment_date"] = pd.to_datetime(
            shipment_df["shipment_date"]
        )

        shipment_total = int(shipment_df["shipment_qty"].sum())
        shipment_count = len(shipment_df)
        customer_count = shipment_df["customer_name"].nunique()

        shipment_chart_col, shipment_table_col = st.columns(
            [1.6, 1]
        )

        with shipment_chart_col:
            with st.container(border=True):
                subsection_title(
                    "고객사별 출하 흐름",
                    "🫧"
                )

                fig, ax = plt.subplots(figsize=(7, 4.2))
                product_names = shipment_df["item_name"].unique()
                shipment_colors = [
                    "#2563EB",
                    "#F59E0B",
                    "#10B981",
                    "#EF4444",
                    "#8B5CF6",
                    "#06B6D4",
                ]
                color_map = {
                    product_name: shipment_colors[
                        index % len(shipment_colors)
                    ]
                    for index, product_name in enumerate(product_names)
                }
                max_shipment_qty = shipment_df["shipment_qty"].max()

                for product_name, product_df in shipment_df.groupby(
                    "item_name"
                ):
                    bubble_sizes = (
                        90
                        + product_df["shipment_qty"]
                        / max_shipment_qty
                        * 430
                    )
                    ax.scatter(
                        product_df["shipment_date"],
                        product_df["customer_name"],
                        s=bubble_sizes,
                        color=color_map[product_name],
                        alpha=0.72,
                        edgecolors="#ffffff",
                        linewidths=1.3,
                        label=product_name,
                    )

                    for _, shipment in product_df.iterrows():
                        ax.annotate(
                            f"{shipment['shipment_qty']:,}",
                            (
                                shipment["shipment_date"],
                                shipment["customer_name"],
                            ),
                            ha="center",
                            va="center",
                            fontsize=7,
                            fontweight="bold",
                            color="#0f172a",
                        )

                ax.set_title(
                    "출하일 · 고객사 · 완제품 · 수량",
                    fontsize=11,
                    fontweight="bold",
                    pad=10,
                )
                ax.set_xlabel("출하일", fontsize=9)
                ax.set_ylabel("고객사", fontsize=9)
                ax.tick_params(axis="both", labelsize=8)
                ax.grid(alpha=0.2)
                ax.legend(
                    title="완제품",
                    loc="best",
                    fontsize=6,
                    title_fontsize=7,
                    frameon=True,
                )
                fig.autofmt_xdate(rotation=20)
                plt.tight_layout()

                st.pyplot(
                    fig,
                    use_container_width=True,
                    bbox_inches=None,
                )
                plt.close(fig)
                st.caption(
                    "버블 크기 = 출하수량 / 색상 = 완제품 / 위치 = 출하일과 고객사"
                )

        with shipment_table_col:
            with st.container(border=True):
                subsection_title(
                    "출하 요약",
                    "📦"
                )

                summary_col1, summary_col2, summary_col3 = st.columns(3)
                summary_col1.metric("누적 출하", f"{shipment_total:,}")
                summary_col2.metric("출하 건수", f"{shipment_count:,}")
                summary_col3.metric("고객사", f"{customer_count:,}")

                st.markdown("**최근 출하 내역**")
                recent_shipment_table = shipment_df[
                    [
                        "shipment_date",
                        "customer_name",
                        "item_name",
                        "shipment_qty",
                    ]
                ].head(7).copy()
                recent_shipment_table["shipment_date"] = (
                    recent_shipment_table["shipment_date"]
                    .dt.strftime("%Y.%m.%d")
                )
                recent_shipment_table.columns = [
                    "출하일",
                    "고객사",
                    "완제품",
                    "수량",
                ]
                recent_shipment_table["수량"] = (
                    recent_shipment_table["수량"]
                    .map(lambda quantity: f"{quantity:,} EA")
                )

                st.dataframe(
                    recent_shipment_table,
                    use_container_width=True,
                    hide_index=True,
                    height=270,
                )

    else:
        st.info("등록된 출하 이력이 없습니다.")


    # ========================================================
    # 상세 데이터 표
    # ========================================================

    section_title("상세 현황", "📋")
    quality_tab, production_tab, order_tab = st.tabs(
        ["⚠️ 완제품 품질", "🏭 오늘 생산실적", "📝 진행 생산지시"]
    )

    with quality_tab:
        if defect_rate_list:
            quality_df = pd.DataFrame(
                [dict(row) for row in defect_rate_list]
            )
            quality_df["defect_rate"] = (
                quality_df["defect_qty"]
                / quality_df["inspection_qty"]
                * 100
            )
            quality_table = quality_df[
                [
                    "item_code",
                    "item_name",
                    "inspection_qty",
                    "good_qty",
                    "defect_qty",
                    "defect_rate",
                ]
            ].copy()
            quality_table.columns = [
                "품목코드",
                "제품명",
                "검사수량",
                "양품수량",
                "불량수량",
                "불량률 (%)",
            ]
            quality_table["불량률 (%)"] = quality_table[
                "불량률 (%)"
            ].map(lambda rate: f"{rate:.1f}%")

            st.dataframe(
                quality_table,
                use_container_width=True,
                hide_index=True,
            )
        else:
            st.info("품질검사 데이터가 없습니다.")

    with production_tab:
        if today_production:
            today_df = pd.DataFrame(
                [dict(row) for row in today_production]
            )
            st.dataframe(
                today_df,
                use_container_width=True,
                hide_index=True,
            )
        else:
            st.info("오늘 생산실적이 없습니다.")

    with order_tab:
        if remaining_orders:
            order_df = pd.DataFrame(
                [dict(row) for row in remaining_orders]
            )
            st.dataframe(
                order_df,
                use_container_width=True,
                hide_index=True,
            )
        else:
            st.success("현재 진행 중인 생산지시가 없습니다.")


# ============================================================
# 오류 처리
# ============================================================

except Exception as exc:

    st.error(
        "대시보드 데이터를 불러오지 못했습니다."
    )

    st.exception(exc)