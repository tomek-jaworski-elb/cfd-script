"""Cost/breakeven math for the CFD position.

Overnight financing fee assumption: charged nightly on each tranche's notional
value (quantity * current live price), at an annual rate the broker sets.
This is a simplification (real brokers mark-to-market and may triple-charge
over weekends) — good enough for tracking approximate accrued carry cost.
"""
from datetime import date, datetime


def _parse_date(value) -> date:
    if isinstance(value, date):
        return value
    return datetime.strptime(value, "%Y-%m-%d").date()


def nights_held(trade_date, as_of: date) -> int:
    d = _parse_date(trade_date)
    return max((as_of - d).days, 0)


def tranche_overnight_fee(quantity: float, current_price: float, rate_annual_pct: float, nights: int) -> float:
    return quantity * current_price * (rate_annual_pct / 100) / 365 * nights


def summarize(transactions: list[dict], current_price: float, rate_annual_pct: float, as_of: date = None) -> dict:
    as_of = as_of or date.today()

    total_qty = sum(t["quantity"] for t in transactions)
    total_cost_basis = sum(t["quantity"] * t["price"] for t in transactions)
    total_commission = sum(t["commission"] for t in transactions)

    total_overnight_fee = 0.0
    per_tranche = []
    for t in transactions:
        nights = nights_held(t["trade_date"], as_of)
        fee = tranche_overnight_fee(t["quantity"], current_price, rate_annual_pct, nights)
        total_overnight_fee += fee
        per_tranche.append({**t, "nights_held": nights, "overnight_fee": fee})

    total_invested = total_cost_basis + total_commission + total_overnight_fee
    avg_entry_price = total_cost_basis / total_qty if total_qty else 0.0
    breakeven_price = total_invested / total_qty if total_qty else 0.0

    return {
        "as_of": as_of,
        "total_qty": total_qty,
        "avg_entry_price": avg_entry_price,
        "total_commission": total_commission,
        "total_overnight_fee": total_overnight_fee,
        "total_invested": total_invested,
        "breakeven_price": breakeven_price,
        "per_tranche": per_tranche,
    }


def target_price_for_profit(breakeven_price: float, profit_pct: float) -> float:
    return breakeven_price * (1 + profit_pct / 100)


def unrealized_pnl(total_qty: float, current_price: float, breakeven_price: float) -> float:
    return total_qty * (current_price - breakeven_price)
