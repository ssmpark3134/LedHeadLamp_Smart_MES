from src.db import fetch_all

# ============================================
# 생산 지시 차트 전용 함수
# ============================================
def get_production_chart_list():
    sql = """
        SELECT
            po.order_id,
            po.order_no,
            i.item_code,
            i.item_name,
            po.order_qty,

            COALESCE(
                SUM(p.production_qty),
                0
            ) AS produced_qty

        FROM production_order AS po

        JOIN item AS i
            ON po.product_item_id = i.item_id

        LEFT JOIN production AS p
            ON po.order_id = p.order_id

        GROUP BY
            po.order_id,
            po.order_no,
            i.item_code,
            i.item_name,
            po.order_qty

        ORDER BY po.order_id
    """

    return fetch_all(sql)


def get_daily_production_by_period(start_date: str, end_date: str):
    """지정 기간의 실제 생산량을 날짜와 품목별로 집계한다."""

    sql = """
        SELECT
            DATE(p.production_date) AS production_date,
            i.item_code,
            i.item_name,
            SUM(p.production_qty) AS produced_qty
        FROM production AS p
        JOIN production_order AS po
            ON p.order_id = po.order_id
        JOIN item AS i
            ON po.product_item_id = i.item_id
        WHERE DATE(p.production_date) BETWEEN ? AND ?
        GROUP BY
            DATE(p.production_date),
            i.item_id,
            i.item_code,
            i.item_name
        ORDER BY
            DATE(p.production_date),
            i.item_id
    """

    return fetch_all(sql, (start_date, end_date))


def get_daily_production_order_progress(production_date: str):
    """선택 날짜에 생산한 작업지시의 지시량과 당일 생산량을 조회한다."""

    sql = """
        SELECT
            po.order_id,
            i.item_code,
            i.item_name,
            po.order_qty,
            SUM(p.production_qty) AS produced_qty
        FROM production AS p
        JOIN production_order AS po
            ON p.order_id = po.order_id
        JOIN item AS i
            ON po.product_item_id = i.item_id
        WHERE DATE(p.production_date) = ?
        GROUP BY
            po.order_id,
            i.item_code,
            i.item_name,
            po.order_qty
        ORDER BY i.item_id, po.order_id
    """

    return fetch_all(sql, (production_date,))

# ============================================
# 품질 불량률 조회
# ============================================
def get_defect_rate_list():
    sql = """
        SELECT
            i.item_code,
            i.item_name,

            COALESCE(
                SUM(q.good_qty),
                0
            ) AS good_qty,

            COALESCE(
                SUM(q.defect_qty),
                0
            ) AS defect_qty,

            COALESCE(
                SUM(q.good_qty),
                0
            )
            +
            COALESCE(
                SUM(q.defect_qty),
                0
            ) AS inspection_qty

        FROM quality AS q

        JOIN production AS p
            ON q.production_id = p.production_id

        JOIN production_order AS po
            ON p.order_id = po.order_id

        JOIN item AS i
            ON po.product_item_id = i.item_id

        GROUP BY
            i.item_id,
            i.item_code,
            i.item_name

        ORDER BY
            i.item_id
    """

    return fetch_all(sql)


def get_shipment_dashboard_list():
    """대시보드용 출하 이력을 최신순으로 조회한다."""

    sql = """
        SELECT
            s.shipment_id,
            s.shipment_date,
            s.customer_name,
            s.customer_po,
            s.shipment_qty,
            l.lot_no,
            i.item_code,
            i.item_name
        FROM shipment AS s
        JOIN lot AS l
            ON s.lot_id = l.lot_id
        JOIN item AS i
            ON l.item_id = i.item_id
        ORDER BY DATE(s.shipment_date) DESC, s.shipment_id DESC
    """

    return fetch_all(sql)