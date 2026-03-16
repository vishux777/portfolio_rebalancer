# Portfolio Rebalancer — Wealth Builder 2025

A full-stack web application that helps financial advisors and clients compare their current mutual fund portfolio against a recommended model plan, calculate buy/sell actions, and save rebalancing history.

---

## Problem Statement

Over time, a client's portfolio drifts from the advisor's recommended allocation as different funds grow at different rates. This app automatically computes the exact amount to buy or sell in each fund to realign the portfolio with the target plan.

---

## Tech Stack

| Layer     | Technology                        |
|-----------|-----------------------------------|
| Backend   | Python 3 · FastAPI · Uvicorn      |
| Database  | SQLite (raw SQL — no ORM)         |
| Frontend  | HTML5 · CSS3 · Vanilla JavaScript |
| Fonts     | Google Fonts (Syne, DM Mono, Inter)|

---

## Project Structure

```
portfolio_app/
├── main.py              ← FastAPI app — all API routes
├── database.py          ← Raw SQL queries — reads & writes
├── rebalance.py         ← Core rebalancing calculation logic
├── static/
│   └── index.html       ← Single-page app (4 screens)
├── model_portfolio.db   ← SQLite database (pre-loaded)
└── requirements.txt
```

---

## How to Run

```bash
# Step 1 — Install dependencies
pip install -r requirements.txt

# Step 2 — Start the server
uvicorn main:app --reload

# Step 3 — Open in browser
# http://localhost:8000
```

---

## API Endpoints

| Method | Endpoint         | Description                                  |
|--------|-----------------|----------------------------------------------|
| GET    | `/clients`       | List all clients                             |
| GET    | `/portfolio`     | Compute full rebalance for a client          |
| GET    | `/holdings`      | Current holdings with portfolio weights      |
| GET    | `/history`       | All saved rebalance sessions for a client    |
| GET    | `/plan`          | Current model fund allocations               |
| POST   | `/save_rebalance`| Save a rebalance session to DB               |
| POST   | `/update_plan`   | Update model fund target percentages         |
| POST   | `/update_status` | Mark a session as APPLIED or DISMISSED       |

All endpoints accept `client_id` as a query parameter (default: `C001` — Amit Sharma).

---

## Database Schema

### Tables Read From
- **clients** — `client_id`, `client_name`, `total_invested`
- **model_funds** — `fund_id`, `fund_name`, `asset_class`, `allocation_pct`
- **client_holdings** — `holding_id`, `client_id`, `fund_id`, `fund_name`, `current_value`

### Tables Written To
- **rebalance_sessions** — one row per save event (`session_id`, `client_id`, `created_at`, `portfolio_value`, `total_to_buy`, `total_to_sell`, `net_cash_needed`, `status`)
- **rebalance_items** — one row per fund per session (`fund_id`, `action`, `amount`, `current_pct`, `target_pct`, `post_rebalance_pct`, `is_model_fund`)

---

## Rebalancing Logic

```
total_value     = sum of all current_value in client_holdings

current_pct     = (fund_current_value / total_value) × 100

drift           = target_pct − current_pct

amount          = (drift / 100) × total_value

action = BUY   if amount > 0   (fund is below target)
action = SELL  if amount < 0   (fund is above target)
action = REVIEW if fund is not in model_funds
```

---

## Expected Output for Amit Sharma (C001)

Total portfolio value = **₹5,80,000** (includes off-plan Axis Bluechip fund)

| Fund                       | Plan % | Today % | Drift    | Action | Amount     |
|----------------------------|--------|---------|----------|--------|------------|
| Mirae Asset Large Cap      | 30%    | 15.5%   | +14.5%   | BUY    | ₹84,000    |
| Parag Parikh Flexi Cap     | 25%    | 26.7%   | −1.7%    | SELL   | ₹10,000    |
| HDFC Mid Cap Opportunities | 20%    | 0.0%    | +20.0%   | BUY    | ₹1,16,000  |
| ICICI Prudential Bond      | 15%    | 19.0%   | −4.0%    | SELL   | ₹23,000    |
| Nippon India Gold ETF      | 10%    | 25.0%   | −15.0%   | SELL   | ₹87,000    |
| Axis Bluechip Fund         | —      | 13.8%   | —        | REVIEW | ₹80,000    |

**Total to BUY: ₹2,00,000 · Total to SELL: ₹1,20,000 · Fresh Money Needed: ₹80,000**

---

## Application Screens

### Screen 1 — Portfolio Analysis
The main dashboard. Shows stat cards (total value, buy total, sell total, fresh money needed), a fund-by-fund comparison table with drift indicators and action badges, and an alert for off-plan funds. The "Save Rebalancing" button inserts a session into the database.

### Screen 2 — Current Holdings
Lists all funds the client currently holds with their current value, portfolio weight (with a visual bar), and whether the fund is part of the recommended plan.

### Screen 3 — Rebalance History
Shows all past saved sessions. Each session is expandable to reveal individual fund actions. Sessions can be marked as APPLIED or DISMISSED.

### Screen 4 — Edit Recommended Plan
An editable form showing the five model funds and their target percentages. The total must equal exactly 100% before saving is allowed. On save, the `model_funds` table is updated and the portfolio analysis recalculates automatically.

---

## Edge Cases Handled

1. **Fund with ₹0 value (F003 — HDFC Mid Cap)** — treated as 0% current allocation; full target amount flagged as BUY.
2. **Off-plan fund (F006 — Axis Bluechip)** — not in `model_funds`; shown with REVIEW action, no buy/sell computed.
3. **Total value includes off-plan funds** — ₹5,80,000 not ₹5,00,000; all percentage calculations use the true current total.
4. **Plan validation** — `update_plan` endpoint returns HTTP 400 if percentages don't sum to exactly 100%.
5. **Multi-client support** — all endpoints are parameterised by `client_id`; the UI lets you switch between Amit Sharma, Priya Nair, and Rohan Mehta.

---

## Design Decisions

- **No ORM** — all database access uses Python's built-in `sqlite3` module with raw SQL. Queries are explicit and readable.
- **Single HTML file** — the entire frontend lives in `static/index.html`. No build step, no bundler, no framework.
- **Dark theme dashboard** — designed to feel like a professional fintech tool (Syne display font, DM Mono for numbers, dark background with subtle grid).
- **Separation of concerns** — `database.py` handles only SQL, `rebalance.py` handles only math, `main.py` handles only HTTP routing.

---

## Author

Just the one who likes to code and debug with love. Loves to be pentester  
Stack: FastAPI · SQLite · Vanilla JS · Python 3