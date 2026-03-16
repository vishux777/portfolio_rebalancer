"""
Core rebalancing calculation logic.
No ORM — pure Python + SQL via database.py.
"""
from database import get_model_funds, get_client_holdings


def compute_rebalance(client_id: str):
    model_funds = get_model_funds()          # [{fund_id, fund_name, asset_class, allocation_pct}]
    holdings    = get_client_holdings(client_id)  # [{fund_id, fund_name, current_value}]

    # Build lookup: fund_id -> model allocation
    model_map = {f["fund_id"]: f for f in model_funds}

    # Total portfolio value = sum of ALL holdings (including non-plan funds)
    total_value = sum(h["current_value"] for h in holdings)

    # Build holdings map: fund_id -> current_value
    holding_map = {h["fund_id"]: h for h in holdings}

    results = []

    
    for mf in model_funds:
        fid   = mf["fund_id"]
        fname = mf["fund_name"]
        target_pct = mf["allocation_pct"]   # e.g. 30.0

        hv = holding_map.get(fid, {}).get("current_value", 0.0)
        current_pct = (hv / total_value * 100) if total_value > 0 else 0.0
        drift       = target_pct - current_pct                      # positive → underfunded (BUY)
        amount      = round(drift / 100 * total_value, 2)

        action = "BUY" if amount > 0 else "SELL"
        if round(amount, 2) == 0:
            action = "HOLD"

        post_rebalance_pct = target_pct

        results.append({
            "fund_id":            fid,
            "fund_name":          fname,
            "asset_class":        mf["asset_class"],
            "is_model_fund":      1,
            "target_pct":         round(target_pct, 2),
            "current_pct":        round(current_pct, 2),
            "drift":              round(drift, 2),
            "action":             action,
            "amount":             abs(round(amount, 2)),
            "current_value":      hv,
            "post_rebalance_pct": round(post_rebalance_pct, 2),
        })


    for h in holdings:
        if h["fund_id"] not in model_map:
            hv = h["current_value"]
            current_pct = (hv / total_value * 100) if total_value > 0 else 0.0
            results.append({
                "fund_id":            h["fund_id"],
                "fund_name":          h["fund_name"],
                "asset_class":        "—",
                "is_model_fund":      0,
                "target_pct":         None,
                "current_pct":        round(current_pct, 2),
                "drift":              None,
                "action":             "REVIEW",
                "amount":             hv,
                "current_value":      hv,
                "post_rebalance_pct": None,
            })


    total_to_buy  = sum(r["amount"] for r in results if r["action"] == "BUY")
    total_to_sell = sum(r["amount"] for r in results if r["action"] == "SELL")
    net_cash_needed = round(total_to_buy - total_to_sell, 2)

    return {
        "client_id":       client_id,
        "total_value":     total_value,
        "total_to_buy":    round(total_to_buy, 2),
        "total_to_sell":   round(total_to_sell, 2),
        "net_cash_needed": net_cash_needed,
        "funds":           results,
    }
