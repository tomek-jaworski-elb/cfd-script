"""Live price fetch for underlying stock behind the CFD.

Primary: yfinance (unofficial Yahoo Finance wrapper).
Fallback: direct HTTP call to Yahoo's chart endpoint (independent code path,
so a yfinance library regression doesn't take down both).

Note: the CFD quote a broker shows includes its own spread/financing terms and
will differ slightly from this underlying exchange price. This module tracks
the exchange price as a proxy for cost/breakeven calculations.
"""
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
