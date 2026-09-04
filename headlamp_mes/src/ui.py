import pandas as pd
import streamlit as st
from src.db import DB_PATH, database_exists
import matplotlib.pyplot as plt
font_path = "/usr/share/fonts/truetype/nanum/NanumGothic.ttf"

# ============================================
# 페이지 기본 설정
# ============================================
def setup_page(title: str):
    st.set_page_config(
        page_title=f"Mini MES - {title}",
        page_icon="🏭",
        layout="wide",
        initial_sidebar_state="expanded"
    )


# ============================================
# 공통 UI 스타일
# ============================================
def inject_ui_style():
    st.markdown(
        """
        <style>

        :root {
            --mes-primary: #2563eb;
            --mes-primary-dark: #1d4ed8;
            --mes-navy: #0f172a;
            --mes-text: #334155;
            --mes-muted: #64748b;
            --mes-border: #dbe3ee;
            --mes-surface: #ffffff;
            --mes-background: #f4f7fb;
        }

        .stApp {
            background: var(--mes-background);
            color: var(--mes-text);
        }

        /* =========================================
           전체 화면
        ========================================= */

        .main .block-container {
            padding-top: 2rem;
            padding-bottom: 4rem;
            max-width: 1380px;
        }

        [data-testid="stSidebar"] {
            background: #0f172a;
            border-right: 0;
        }

        [data-testid="stSidebar"] * {
            color: #dbeafe;
        }

        [data-testid="stSidebarNav"]::before {
            content: "HEADLAMP MES";
            display: block;
            padding: 1.25rem 1.25rem .85rem;
            color: #ffffff;
            font-size: 1rem;
            font-weight: 800;
            letter-spacing: .08em;
        }

        [data-testid="stSidebarNav"] a {
            margin: .15rem .65rem;
            border-radius: 9px;
        }

        [data-testid="stSidebarNav"] a:hover {
            background: rgba(255, 255, 255, .09);
        }

        [data-testid="stSidebarNav"] a[aria-current="page"] {
            background: #2563eb;
        }


        /* =========================================
           페이지 제목
        ========================================= */

        .mes-page-title {
            font-size: 2.05rem;
            font-weight: 800;
            color: var(--mes-navy);
            letter-spacing: -.03em;
            margin-bottom: 5px;
        }

        .mes-page-subtitle {
            color: #64748b;
            font-size: 0.95rem;
            margin-bottom: .9rem;
        }

        /* =========================================
           대시보드 히어로
        ========================================= */

        .mes-dashboard-hero {
            display: grid;
            grid-template-columns: minmax(0, 2fr) minmax(320px, .95fr);
            gap: 24px;
            padding: 26px 28px;
            margin-bottom: 24px;
            background:
                radial-gradient(circle at 8% 12%, rgba(37, 99, 235, .08), transparent 28%),
                linear-gradient(120deg, #ffffff 0%, #ffffff 68%, #fffdf5 100%);
            border: 1px solid var(--mes-border);
            border-radius: 14px;
            box-shadow: 0 8px 28px rgba(15, 23, 42, .05);
        }

        .mes-hero-eyebrow {
            color: var(--mes-primary);
            font-size: .72rem;
            font-weight: 800;
            letter-spacing: .09em;
            margin-bottom: 7px;
        }

        .mes-hero-title {
            color: var(--mes-navy);
            font-size: 2rem;
            font-weight: 850;
            letter-spacing: -.04em;
            line-height: 1.2;
            margin-bottom: 9px;
        }

        .mes-hero-description {
            color: var(--mes-muted);
            font-size: .9rem;
            line-height: 1.6;
            margin-bottom: 22px;
        }

        .mes-hero-summary {
            display: grid;
            grid-template-columns: repeat(3, minmax(0, 1fr));
            gap: 12px;
        }

        .mes-hero-stat {
            background: rgba(255, 255, 255, .82);
            border: 1px solid #edf1f6;
            border-left: 4px solid var(--stat-color, var(--mes-primary));
            border-radius: 9px;
            padding: 13px 14px;
        }

        .mes-hero-stat-value {
            color: var(--mes-navy);
            font-size: 1.15rem;
            font-weight: 850;
            margin-bottom: 5px;
        }

        .mes-hero-stat-label {
            color: var(--mes-muted);
            font-size: .76rem;
            font-weight: 650;
        }

        .mes-hero-snapshot {
            align-self: stretch;
            background: #132235;
            border-radius: 11px;
            padding: 18px 20px;
            color: #ffffff;
        }

        .mes-snapshot-label {
            color: #93c5fd;
            font-size: .66rem;
            font-weight: 800;
            letter-spacing: .06em;
            margin-bottom: 8px;
        }

        .mes-snapshot-title {
            font-size: 1.08rem;
            font-weight: 800;
            margin-bottom: 13px;
        }

        .mes-snapshot-row {
            display: flex;
            justify-content: space-between;
            gap: 16px;
            padding: 10px 0;
            border-top: 1px solid rgba(255, 255, 255, .13);
            color: #dbeafe;
            font-size: .79rem;
            font-weight: 650;
        }

        .mes-snapshot-row strong {
            color: #ffffff;
            white-space: nowrap;
        }


        /* =========================================
           페이지 설명 카드
        ========================================= */

        .mes-info-card {
            display: inline-flex;
            align-items: center;
            gap: 10px;
            background: #eaf2ff;
            border: 1px solid #cfe0ff;
            border-radius: 999px;
            padding: 7px 12px;
            margin-bottom: 12px;
        }

        .mes-info-label {
            font-size: 0.75rem;
            font-weight: 800;
            color: #64748b;

            margin: 0;
        }

        .mes-info-value {
            font-size: 0.78rem;
            color: #334155;
            line-height: 1.3;
        }


        /* =========================================
           DB 상태
        ========================================= */

        .mes-db-status {
            display: flex;
            align-items: center;

            width: fit-content;
            color: #15803d;
            padding: 0 2px;
            font-size: 0.78rem;
            font-weight: 700;
            margin-bottom: 24px;
        }


        /* =========================================
           섹션 제목
        ========================================= */

        .mes-section-title {
            font-size: 1.15rem;
            font-weight: 800;

            color: var(--mes-navy);
            margin-top: 18px;
            margin-bottom: 12px;
            padding-left: 11px;
            border-left: 4px solid var(--mes-primary);
        }


        /* =========================================
           작은 섹션 제목
        ========================================= */

        .mes-subsection-title {
            font-size: 1rem;
            font-weight: 750;

            color: #334155;

            margin-top: 8px;
            margin-bottom: 8px;
        }


        /* =========================================
           카드
        ========================================= */

        .mes-card {
            background: #ffffff;

            border: 1px solid #e2e8f0;

            border-radius: 12px;

            padding: 16px;

            box-shadow:
                0 5px 18px rgba(15, 23, 42, 0.05);

            margin-bottom: 12px;
        }


        /* =========================================
           상태 카드
        ========================================= */

        .mes-card-blue {
            background: #eff6ff;
            border: 1px solid #bfdbfe;
            border-radius: 12px;
            padding: 16px;
        }

        .mes-card-green {
            background: #f0fdf4;
            border: 1px solid #bbf7d0;
            border-radius: 12px;
            padding: 16px;
        }

        .mes-card-yellow {
            background: #fffbeb;
            border: 1px solid #fde68a;
            border-radius: 12px;
            padding: 16px;
        }

        .mes-card-red {
            background: #fef2f2;
            border: 1px solid #fecaca;
            border-radius: 12px;
            padding: 16px;
        }


        /* =========================================
           KPI
        ========================================= */

        .mes-kpi {
            background: #ffffff;

            border: 1px solid #e2e8f0;

            border-radius: 12px;

            padding: 15px;

            min-height: 105px;

            box-shadow:
                0 5px 18px rgba(15, 23, 42, 0.05);
        }

        .mes-kpi-label {
            font-size: 0.8rem;
            font-weight: 700;
            color: #64748b;

            margin-bottom: 6px;
        }

        .mes-kpi-value {
            font-size: 1.6rem;
            font-weight: 800;
            color: #111827;
        }


        /* =========================================
           알림
        ========================================= */

        .mes-alert {
            background: #fff7ed;

            border: 1px solid #fed7aa;

            color: #9a3412;

            border-radius: 10px;

            padding: 12px 14px;

            font-weight: 650;

            margin-bottom: 8px;
        }

        .mes-success {
            background: #f0fdf4;

            border: 1px solid #bbf7d0;

            color: #166534;

            border-radius: 10px;

            padding: 12px 14px;

            font-weight: 650;

            margin-bottom: 8px;
        }


        /* =========================================
           데이터 테이블
        ========================================= */

        [data-testid="stDataFrame"] {
            border: 1px solid var(--mes-border);
            border-radius: 10px;
            overflow: hidden;
            box-shadow: 0 3px 12px rgba(15, 23, 42, .04);
        }


        /* =========================================
           버튼
        ========================================= */

        .stButton > button {
            min-height: 2.7rem;
            border-radius: 9px;
            font-weight: 700;
            transition: transform .12s ease, box-shadow .12s ease;
        }

        .stButton > button:hover {
            transform: translateY(-1px);
            box-shadow: 0 5px 14px rgba(37, 99, 235, .18);
        }

        .stButton > button[kind="primary"] {
            background: var(--mes-primary);
            border-color: var(--mes-primary);
        }


        /* =========================================
           입력창
        ========================================= */

        .stTextInput input,
        .stNumberInput input,
        .stDateInput input {
            border-radius: 9px;
            background: #ffffff;
        }

        [data-baseweb="select"] > div {
            border-radius: 9px;
            background: #ffffff;
        }

        [data-testid="stVerticalBlockBorderWrapper"] {
            background: var(--mes-surface);
            border-color: var(--mes-border) !important;
            border-radius: 12px;
            box-shadow: 0 4px 14px rgba(15, 23, 42, .045);
        }

        [data-testid="stMetric"] {
            background: #ffffff;
            border: 1px solid var(--mes-border);
            border-radius: 12px;
            padding: 15px 17px;
        }

        [data-testid="stMetricLabel"] {
            color: var(--mes-muted);
            font-weight: 700;
        }

        [data-testid="stMetricValue"] {
            color: var(--mes-navy);
        }

        hr {
            border-color: #e2e8f0 !important;
            margin: 1.7rem 0 !important;
        }

        h1, h2, h3 {
            color: var(--mes-navy);
            letter-spacing: -.02em;
        }

        [data-testid="stAlert"] {
            border-radius: 10px;
        }


        /* =========================================
           모바일
        ========================================= */

        @media (max-width: 900px) {

            .main .block-container {
                padding-top: 1.25rem;
                padding-left: 1rem;
                padding-right: 1rem;
            }

            .mes-page-title {
                font-size: 1.6rem;
            }

            .mes-info-card {
                display: flex;
                border-radius: 10px;
            }

            .mes-dashboard-hero {
                grid-template-columns: 1fr;
                padding: 21px;
            }

            .mes-hero-title {
                font-size: 1.55rem;
            }

            .mes-hero-summary {
                grid-template-columns: 1fr;
            }

        }

        </style>
        """,
        unsafe_allow_html=True
    )


# ============================================
# 페이지 제목
# ============================================
def page_title(
    title: str,
    description: str,
    tables: str,
    task: str
):

    inject_ui_style()

    st.markdown(
        f"""
        <div class="mes-page-title">
            {title.replace(chr(10), "<br>")}
        </div>

        <div class="mes-page-subtitle">
            {description.replace(chr(10), "<br>")}
        </div>

        <div class="mes-info-card">
            <div class="mes-info-label">
                화면 정보
            </div>
            <div class="mes-info-value">
                {task} · 관련 데이터: {tables.replace(chr(10), " ").strip()}
            </div>
        </div>
        """,
        unsafe_allow_html=True
    )


def dashboard_hero(
    title: str,
    description: str,
    summary_items: list[tuple[str, str, str]],
    snapshot_items: list[tuple[str, str]]
):
    """대시보드 최상단의 공장 현황 요약 영역을 표시한다."""

    inject_ui_style()

    summary_html = "".join(
        (
            f'<div class="mes-hero-stat" style="--stat-color:{color}">'
            f'<div class="mes-hero-stat-value">{value}</div>'
            f'<div class="mes-hero-stat-label">{label}</div>'
            '</div>'
        )
        for value, label, color in summary_items
    )

    snapshot_html = "".join(
        (
            '<div class="mes-snapshot-row">'
            f'<span>{label}</span><strong>{value}</strong>'
            '</div>'
        )
        for label, value in snapshot_items
    )

    st.markdown(
        (
            '<div class="mes-dashboard-hero">'
            '<div>'
            '<div class="mes-hero-eyebrow">HEADLAMP MANUFACTURING SYSTEM</div>'
            f'<div class="mes-hero-title">{title}</div>'
            f'<div class="mes-hero-description">{description}</div>'
            f'<div class="mes-hero-summary">{summary_html}</div>'
            '</div>'
            '<div class="mes-hero-snapshot">'
            '<div class="mes-snapshot-label">LIVE FACTORY SNAPSHOT</div>'
            '<div class="mes-snapshot-title">생산라인 운영 현황</div>'
            f'{snapshot_html}'
            '</div>'
            '</div>'
        ),
        unsafe_allow_html=True
    )


# ============================================
# DB 파일 존재 여부 표시
# ============================================
def show_database_status():

    if database_exists():

        st.markdown(
            f"""
            <div class="mes-db-status">
                ● 시스템 정상 · 데이터베이스 연결됨
            </div>
            """,
            unsafe_allow_html=True
        )

    else:

        st.error(
            f"데이터베이스 파일을 찾을 수 없습니다: {DB_PATH}"
        )


# ============================================
# 섹션 제목
# ============================================
def section_title(
    title: str,
    icon: str = ""
):

    st.markdown(
        f"""
        <div class="mes-section-title">
            {icon} {title}
        </div>
        """,
        unsafe_allow_html=True
    )


# ============================================
# 서브 섹션 제목
# ============================================
def subsection_title(
    title: str,
    icon: str = ""
):

    st.markdown(
        f"""
        <div class="mes-subsection-title">
            {icon} {title}
        </div>
        """,
        unsafe_allow_html=True
    )


# ============================================
# 기본 카드
# ============================================
def card_start():

    st.markdown(
        '<div class="mes-card">',
        unsafe_allow_html=True
    )


def card_end():

    st.markdown(
        '</div>',
        unsafe_allow_html=True
    )


# ============================================
# KPI 지표
# ============================================
def metric_row(
    values: list[tuple[str, object]]
):

    columns = st.columns(len(values))

    for column, (label, value) in zip(
        columns,
        values
    ):

        with column:

            st.markdown(
                (
                    '<div class="mes-kpi">'
                    f'<div class="mes-kpi-label">{label}</div>'
                    f'<div class="mes-kpi-value">{value}</div>'
                    '</div>'
                ),
                unsafe_allow_html=True
            )


# ============================================
# DataFrame 표시
# ============================================
def show_dataframe(
    df: pd.DataFrame,
    empty_message: str = "조건에 해당하는 데이터가 없습니다."
):

    if df.empty:

        st.info(empty_message)

    else:

        st.dataframe(
            df,
            use_container_width=True,
            hide_index=True
        )


# ============================================
# 단일 조회 결과 → dict
# ============================================
def row_to_dict(row):

    if row is None:
        return {}

    return {
        key: row[key]
        for key in row.keys()
    }

# 글꼴
def setup_matplotlib():
    plt.rcParams["font.family"] = "NanumGothic"
    plt.rcParams["axes.unicode_minus"] = False