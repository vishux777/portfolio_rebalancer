from fastapi import FastAPI, HTTPException
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
from pydantic import BaseModel
from typing import List, Optional
import os

from database import (
    get_clients,
    get_model_funds,
    get_client_holdings,
    get_rebalance_history,
    save_rebalance_session,
    update_plan,
    update_session_status,
)
from rebalance import compute_rebalance

app = FastAPI(title="Portfolio Rebalancer")

# Serve static files
STATIC_DIR = os.path.join(os.path.dirname(__file__), "static")
app.mount("/static", StaticFiles(directory=STATIC_DIR), name="static")


@app.get("/", response_class=FileResponse)
def index():
    return FileResponse(os.path.join(STATIC_DIR, "index.html"))


# ─────────────────────────────────────────────
# READ endpoints
# ─────────────────────────────────────────────

@app.get("/clients")
def clients():
    return get_clients()


@app.get("/portfolio")
def portfolio(client_id: str = "C001"):
    return compute_rebalance(client_id)


@app.get("/holdings")
def holdings(client_id: str = "C001"):
    rows = get_client_holdings(client_id)
    total = sum(r["current_value"] for r in rows)
    return {"holdings": rows, "total_value": total}


@app.get("/history")
def history(client_id: str = "C001"):
    return get_rebalance_history(client_id)


@app.get("/plan")
def plan():
    return get_model_funds()


# ─────────────────────────────────────────────
# WRITE endpoints
# ─────────────────────────────────────────────

class SaveRebalanceRequest(BaseModel):
    client_id: str = "C001"


@app.post("/save_rebalance")
def save_rebalance(req: SaveRebalanceRequest):
    data = compute_rebalance(req.client_id)
    items = []
    for f in data["funds"]:
        items.append({
            "fund_id":            f["fund_id"],
            "fund_name":          f["fund_name"],
            "action":             f["action"],
            "amount":             f["amount"],
            "current_pct":        f["current_pct"],
            "target_pct":         f["target_pct"],
            "post_rebalance_pct": f["post_rebalance_pct"],
            "is_model_fund":      f["is_model_fund"],
        })
    session_id = save_rebalance_session(
        client_id=req.client_id,
        portfolio_value=data["total_value"],
        total_to_buy=data["total_to_buy"],
        total_to_sell=data["total_to_sell"],
        net_cash_needed=data["net_cash_needed"],
        items=items,
    )
    return {"success": True, "session_id": session_id}


class PlanAllocation(BaseModel):
    fund_id: str
    allocation_pct: float


class UpdatePlanRequest(BaseModel):
    allocations: List[PlanAllocation]


@app.post("/update_plan")
def update_model_plan(req: UpdatePlanRequest):
    total = sum(a.allocation_pct for a in req.allocations)
    if round(total, 2) != 100.0:
        raise HTTPException(status_code=400, detail=f"Allocations must sum to 100%. Got {total:.2f}%")
    update_plan([a.dict() for a in req.allocations])
    return {"success": True, "message": "Plan updated successfully"}


class StatusUpdate(BaseModel):
    session_id: int
    status: str


@app.post("/update_status")
def update_status(req: StatusUpdate):
    if req.status not in ("PENDING", "APPLIED", "DISMISSED"):
        raise HTTPException(status_code=400, detail="Invalid status")
    update_session_status(req.session_id, req.status)
    return {"success": True}
