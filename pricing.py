"""Live price fetch for underlying stock behind the CFD.

Primary: yfinance (unofficial Yahoo Finance wrapper).
Fallback: direct HTTP call to Yahoo's chart endpoint (independent code path,
so a yfinance library regression doesn't take down both).

Note: the CFD quote a broker shows includes its own spread/financing terms and
will differ slightly from this underlying exchange price. This module tracks
the exchange price as a proxy for cost/breakeven calculations.
"""
from datetime import datetime, timedelta, timezone

import requests
import yfinance as yf

YAHOO_CHART_URL = "https://query1.finance.yahoo.com/v8/finance/chart/{ticker}"
_HEADERS = {"User-Agent": "Mozilla/5.0"}


class PriceFetchError(Exception):
    pass


def _fetch_via_yfinance(ticker: str) -> dict:
    info = yf.Ticker(ticker).fast_info
    price = info.get("lastPrice") if hasattr(info, "get") else info.last_price
    currency = info.get("currency") if hasattr(info, "get") else info.currency
    if price is None:
        raise PriceFetchError("yfinance returned no price")
    return {"price": float(price), "currency": currency or "USD", "source": "yfinance"}


def _fetch_via_yahoo_chart(ticker: str) -> dict:
    resp = requests.get(
        YAHOO_CHART_URL.format(ticker=ticker), headers=_HEADERS, timeout=10
    )
    resp.raise_for_status()
    meta = resp.json()["chart"]["result"][0]["meta"]
    return {
        "price": float(meta["regularMarketPrice"]),
        "currency": meta.get("currency", "USD"),
        "source": "yahoo-chart-fallback",
    }


def get_current_price(ticker: str) -> dict:
    """Return {price, currency, source}. Raises PriceFetchError if both sources fail."""
    try:
        return _fetch_via_yfinance(ticker)
    except Exception as primary_err:
        try:
            return _fetch_via_yahoo_chart(ticker)
        except Exception as fallback_err:
            raise PriceFetchError(
                f"yfinance failed ({primary_err}); fallback failed ({fallback_err})"
            ) from fallback_err


def _fetch_history_via_yfinance(ticker: str, start: datetime, interval: str) -> dict:
    df = yf.Ticker(ticker).history(start=start, interval=interval)
    closes = df["Close"].dropna() if not df.empty else df
    return {
        "points": [
            {"ts": ts.to_pydatetime(), "price": float(price)}
            for ts, price in closes.items()
        ],
        "source": "yfinance",
    }


def _fetch_history_via_yahoo_chart(ticker: str, start: datetime, interval: str) -> dict:
    resp = requests.get(
        YAHOO_CHART_URL.format(ticker=ticker),
        params={
            "period1": int(start.timestamp()),
            "period2": int(datetime.now(timezone.utc).timestamp()),
            "interval": interval,
        },
        headers=_HEADERS,
        timeout=10,
    )
    resp.raise_for_status()
    result = resp.json()["chart"]["result"][0]
    timestamps = result.get("timestamp") or []
    closes = result["indicators"]["quote"][0].get("close") or []
    points = [
        {"ts": datetime.fromtimestamp(ts, tz=timezone.utc), "price": float(price)}
        for ts, price in zip(timestamps, closes)
        if price is not None
    ]
    return {"points": points, "source": "yahoo-chart-fallback"}


def get_price_history(ticker: str, days: int, interval: str) -> dict:
    """Return {points: [{ts, price}, ...], source} covering the last `days` days
    at the given intraday interval (e.g. "5m", "15m", "30m"). Timestamps are
    timezone-aware. An empty `points` list means a source responded but the
    window holds no trades (weekend/holiday) — that is not a fetch failure.
    Raises PriceFetchError only when both sources fail outright."""
    start = datetime.now(timezone.utc) - timedelta(days=days)
    empty_result = None
    errors = []
    for fetch in (_fetch_history_via_yfinance, _fetch_history_via_yahoo_chart):
        try:
            result = fetch(ticker, start, interval)
        except Exception as err:
            errors.append(err)
            continue
        if result["points"]:
            return result
        empty_result = result
    if empty_result is not None:
        return empty_result
    raise PriceFetchError(
        f"yfinance failed ({errors[0]}); fallback failed ({errors[1]})"
    ) from errors[-1]


NBP_USD_RATE_URL = "https://api.nbp.pl/api/exchangerates/rates/a/usd/?format=json"


def _fetch_usd_pln_via_nbp() -> dict:
    resp = requests.get(NBP_USD_RATE_URL, headers=_HEADERS, timeout=10)
    resp.raise_for_status()
    rate = float(resp.json()["rates"][0]["mid"])
    return {"rate": rate, "source": "nbp"}


def _fetch_usd_pln_via_yfinance() -> dict:
    info = yf.Ticker("USDPLN=X").fast_info
    price = info.get("lastPrice") if hasattr(info, "get") else info.last_price
    if price is None:
        raise PriceFetchError("yfinance returned no USD/PLN rate")
    return {"rate": float(price), "source": "yfinance"}


def get_usd_pln_rate() -> dict:
    """Return {rate, source}. yfinance live market quote is primary (updates
    continuously); NBP's once-per-business-day reference rate is fallback."""
    try:
        return _fetch_usd_pln_via_yfinance()
    except Exception as primary_err:
        try:
            return _fetch_usd_pln_via_nbp()
        except Exception as fallback_err:
            raise PriceFetchError(
                f"yfinance failed ({primary_err}); NBP fallback failed ({fallback_err})"
            ) from fallback_err
