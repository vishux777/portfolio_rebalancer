import sqlite3
import os

DB_PATH = os.path.join(os.path.dirname(__file__), "model_portfolio.db")


def get_conn():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn


def get_clients():
    conn = get_conn()
    rows = conn.execute("SELECT client_id, client_name, total_invested FROM clients").fetchall()
    conn.close()
    return [dict(r) for r in rows]


def get_model_funds():
    conn = get_conn()
    rows = conn.execute(
        "SELECT fund_id, fund_name, asset_class, allocation_pct FROM model_funds ORDER BY fund_id"
    ).fetchall()
    conn.close()
    return [dict(r) for r in rows]


def get_client_holdings(client_id: str):
    conn = get_conn()
    rows = conn.execute(
        "SELECT holding_id, client_id, fund_id, fund_name, current_value FROM client_holdings WHERE client_id = ?",
        (client_id,),
    ).fetchall()
    conn.close()
    return [dict(r) for r in rows]


def get_rebalance_history(client_id: str):
    conn = get_conn()
    rows = conn.execute(
        """SELECT session_id, client_id, created_at, portfolio_value,
                  total_to_buy, total_to_sell, net_cash_needed, status
           FROM rebalance_sessions
           WHERE client_id = ?
           ORDER BY created_at DESC""",
        (client_id,),
    ).fetchall()
    result = []
    for r in rows:
        session = dict(r)
        items = conn.execute(
            """SELECT item_id, session_id, fund_id, fund_name, action,
                      amount, current_pct, target_pct, post_rebalance_pct, is_model_fund
               FROM rebalance_items WHERE session_id = ?""",
            (session["session_id"],),
        ).fetchall()
        session["items"] = [dict(i) for i in items]
        result.append(session)
    conn.close()
    return result


def save_rebalance_session(client_id, portfolio_value, total_to_buy, total_to_sell, net_cash_needed, items):
    conn = get_conn()
    from datetime import datetime
    created_at = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    cur = conn.execute(
        """INSERT INTO rebalance_sessions
           (client_id, created_at, portfolio_value, total_to_buy, total_to_sell, net_cash_needed, status)
           VALUES (?, ?, ?, ?, ?, ?, 'PENDING')""",
        (client_id, created_at, portfolio_value, total_to_buy, total_to_sell, net_cash_needed),
    )
    session_id = cur.lastrowid
    for item in items:
        conn.execute(
            """INSERT INTO rebalance_items
               (session_id, fund_id, fund_name, action, amount, current_pct, target_pct, post_rebalance_pct, is_model_fund)
               VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)""",
            (
                session_id,
                item["fund_id"],
                item["fund_name"],
                item["action"],
                item["amount"],
                item["current_pct"],
                item.get("target_pct"),
                item.get("post_rebalance_pct"),
                item["is_model_fund"],
            ),
        )
    conn.commit()
    conn.close()
    return session_id


def update_plan(allocations: list):
    """allocations: list of {fund_id, allocation_pct}"""
    conn = get_conn()
    for a in allocations:
        conn.execute(
            "UPDATE model_funds SET allocation_pct = ? WHERE fund_id = ?",
            (a["allocation_pct"], a["fund_id"]),
        )
    conn.commit()
    conn.close()


def update_session_status(session_id: int, status: str):
    conn = get_conn()
    conn.execute("UPDATE rebalance_sessions SET status = ? WHERE session_id = ?", (status, session_id))
    conn.commit()
    conn.close()
