"""Streamlit dashboard for tracking an Adtran (ADTN) CFD position:
live price, transaction log, overnight financing cost, breakeven & target price.
"""
import time
from datetime import date, datetime, time as dtime
from pathlib import Path
from zoneinfo import ZoneInfo

import pandas as pd
import streamlit as st

import calc
import db
import pricing
from i18n import t

st.set_page_config(page_title="Adtran CFD Tracker", layout="wide")
db.init_db()

CURRENCY = "USD"
NY_TZ = ZoneInfo("America/New_York")
WARSAW_TZ = ZoneInfo("Europe/Warsaw")
MARKET_OPEN_T = dtime(9, 30)
MARKET_CLOSE_T = dtime(16, 0)
VERSION_FILE = Path(__file__).parent / "VERSION"


def app_version():
    """Reads the app version and its release date from the VERSION file
    (line 1: semantic version, line 2: release date)."""
    version, released = VERSION_FILE.read_text().strip().splitlines()
    return version, released


def market_status():
    """Regular NYSE/Nasdaq session (9:30-16:00 ET, Mon-Fri), converted to Warsaw
    local time. Does not account for exchange holidays."""
    now_ny = datetime.now(NY_TZ)
    is_open = now_ny.weekday() < 5 and MARKET_OPEN_T <= now_ny.time() < MARKET_CLOSE_T
    open_warsaw = datetime.combine(now_ny.date(), MARKET_OPEN_T, NY_TZ).astimezone(WARSAW_TZ)
    close_warsaw = datetime.combine(now_ny.date(), MARKET_CLOSE_T, NY_TZ).astimezone(WARSAW_TZ)
    return is_open, open_warsaw, close_warsaw


# --- Language (persisted setting, switchable per session) ---
lang_options = {"pl": "Polski", "en": "English"}
if "lang" not in st.session_state:
    saved_lang = db.get_setting("lang")
    st.session_state.lang = saved_lang if saved_lang in lang_options else "pl"

with st.sidebar:
    lang = st.selectbox(
        t(st.session_state.lang, "language_label"),
        options=list(lang_options.keys()),
        format_func=lambda code: lang_options[code],
        index=list(lang_options.keys()).index(st.session_state.lang),
    )
    if lang != st.session_state.lang:
        st.session_state.lang = lang
        db.set_setting("lang", lang)
        st.rerun()

lang = st.session_state.lang

st.title(t(lang, "page_title"))

# --- Settings sidebar ---
with st.sidebar:
    st.header(t(lang, "settings_header"))
    ticker = st.text_input(t(lang, "ticker_label"), value=db.get_setting("ticker"))
    overnight_rate = st.number_input(
        t(lang, "overnight_rate_label"),
        value=float(db.get_setting("overnight_rate_annual_pct")),
        step=0.1,
        help=t(lang, "overnight_rate_help"),
    )
    profit_target_pct = st.number_input(
        t(lang, "profit_target_label"),
        value=float(db.get_setting("profit_target_pct")),
        step=0.5,
    )
    refresh_interval = int(
        st.number_input(
            t(lang, "refresh_interval_label"),
            min_value=15,
            max_value=3600,
            value=int(float(db.get_setting("refresh_interval_sec"))),
            step=15,
            help=t(lang, "refresh_interval_help"),
        )
    )
    if st.button(t(lang, "save_settings_button")):
        db.set_setting("ticker", ticker)
        db.set_setting("overnight_rate_annual_pct", str(overnight_rate))
        db.set_setting("profit_target_pct", str(profit_target_pct))
        db.set_setting("refresh_interval_sec", str(refresh_interval))
        st.success(t(lang, "settings_saved"))

    st.caption(t(lang, "cfd_note"))

    app_ver, app_ver_date = app_version()
    st.caption(t(lang, "app_version_caption", version=app_ver, date=app_ver_date))


if "last_full_rerun" not in st.session_state:
    st.session_state.last_full_rerun = time.monotonic()


@st.fragment(run_every=f"{refresh_interval}s")
def _autorefresh_tick():
    # A fragment's body also runs immediately on every normal (non-scheduled)
    # script execution, not just on its run_every timer - without this guard,
    # st.rerun() below would fire on every rerun and loop forever. Only escalate
    # to a full-app rerun once the configured interval has actually elapsed.
    if time.monotonic() - st.session_state.last_full_rerun >= refresh_interval:
        st.session_state.last_full_rerun = time.monotonic()
        st.rerun()  # default scope inside a fragment is a full-app rerun


_autorefresh_tick()


@st.fragment(run_every="1s")
def _live_clock(fetched_at, interval_sec, lang):
    # Fragment-scoped only (no st.rerun()) - ticks every second without
    # forcing a full-page rerun, so price/P/L stay put between real refreshes.
    elapsed = (datetime.now(WARSAW_TZ) - fetched_at).total_seconds()
    seconds_ago = max(0, int(elapsed))
    seconds_left = max(0, int(interval_sec - elapsed))
    c1, c2 = st.columns(2)
    c1.metric(
        t(lang, "as_of_metric_label"),
        f"{fetched_at.strftime('%H:%M:%S')} ({t(lang, 'seconds_ago_suffix', s=seconds_ago)})",
    )
    c2.metric(t(lang, "next_update_metric"), f"{seconds_left // 60:02d}:{seconds_left % 60:02d}")


@st.cache_data(ttl=refresh_interval)
def cached_price(tkr: str, _interval: int):
    data = pricing.get_current_price(tkr)
    data["fetched_at"] = datetime.now(WARSAW_TZ)
    return data


@st.cache_data(ttl=refresh_interval)
def cached_pln_rate(_interval: int):
    data = pricing.get_usd_pln_rate()
    data["fetched_at"] = datetime.now(WARSAW_TZ)
    return data


# --- Live price ---
st.subheader(t(lang, "live_price_header"))
try:
    price_data = cached_price(ticker, refresh_interval)
    fetched_at = price_data["fetched_at"]
    is_open, open_warsaw, close_warsaw = market_status()

    with st.container(border=True):
        col1, col2, col3 = st.columns([2, 1, 1])
        col1.metric(t(lang, "price_metric_label", ticker=ticker), f"{price_data['price']:.2f} {CURRENCY}")
        col2.metric(t(lang, "source_metric_label"), price_data["source"])
        with col3:
            st.badge(
                t(lang, "market_open") if is_open else t(lang, "market_closed"),
                icon="🟢" if is_open else "🔴",
                color="green" if is_open else "gray",
            )
            st.caption(
                t(
                    lang,
                    "market_hours_caption",
                    open=open_warsaw.strftime("%H:%M"),
                    close=close_warsaw.strftime("%H:%M"),
                )
            )

        _live_clock(fetched_at, refresh_interval, lang)

    current_price = price_data["price"]
except pricing.PriceFetchError as e:
    st.error(t(lang, "price_fetch_error", error=e))
    current_price = st.number_input(t(lang, "manual_price_label"), min_value=0.0, step=0.01)

def _refresh_price_and_rate():
    cached_price.clear()
    cached_pln_rate.clear()


st.button(t(lang, "refresh_price_button"), on_click=_refresh_price_and_rate)

# --- Add transaction ---
st.subheader(t(lang, "add_transaction_header"))
with st.form("add_transaction", clear_on_submit=True):
    c1, c2, c3, c4 = st.columns(4)
    trade_date = c1.date_input(t(lang, "date_label"), value=date.today())
    quantity = c2.number_input(t(lang, "quantity_label"), min_value=0.0, step=1.0)
    price = c3.number_input(t(lang, "price_per_share_label"), min_value=0.0, step=0.01)
    commission = c4.number_input(t(lang, "commission_label"), min_value=0.0, step=0.01)
    submitted = st.form_submit_button(t(lang, "add_button"))
    if submitted:
        if quantity <= 0 or price <= 0:
            st.error(t(lang, "qty_price_error"))
        else:
            db.add_transaction(trade_date.isoformat(), quantity, price, commission)
            st.success(t(lang, "transaction_added"))

# --- Transactions & summary ---
transactions = db.get_transactions()

if not transactions:
    st.info(t(lang, "no_transactions_info"))
else:
    summary = calc.summarize(transactions, current_price, overnight_rate)

    st.subheader(t(lang, "tranches_header"))
    tranche_df = pd.DataFrame(summary["per_tranche"])[
        ["id", "trade_date", "quantity", "price", "commission", "nights_held", "overnight_fee"]
    ]
    tranche_df["overnight_fee"] = tranche_df["overnight_fee"].round(2)
    tranche_df = tranche_df.rename(
        columns={
            "id": t(lang, "id_col"),
            "trade_date": t(lang, "date_label"),
            "quantity": t(lang, "quantity_label"),
            "price": t(lang, "price_per_share_label"),
            "commission": t(lang, "commission_label"),
            "nights_held": t(lang, "nights_held_col"),
            "overnight_fee": t(lang, "overnight_fee_col"),
        }
    )
    st.dataframe(tranche_df, width="stretch", hide_index=True)

    del_id = st.selectbox(
        t(lang, "delete_select_label"),
        options=[None] + [tx["id"] for tx in transactions],
    )
    if del_id and st.button(t(lang, "delete_button")):
        db.delete_transaction(del_id)
        st.rerun()

    st.subheader(t(lang, "summary_header"))
    breakeven = summary["breakeven_price"]
    target = calc.target_price_for_profit(breakeven, profit_target_pct)
    pnl = calc.unrealized_pnl(summary["total_qty"], current_price, breakeven)
    pnl_pct = (pnl / summary["total_invested"] * 100) if summary["total_invested"] else 0.0

    with st.container(border=True):
        st.caption(t(lang, "position_group_header"))
        m1, m2 = st.columns(2)
        m1.metric(t(lang, "total_qty_metric"), f"{summary['total_qty']:.2f}", border=True)
        m2.metric(t(lang, "avg_entry_price_metric"), f"{summary['avg_entry_price']:.4f} {CURRENCY}", border=True)

    with st.container(border=True):
        st.caption(t(lang, "costs_group_header"))
        m3, m4, m5 = st.columns(3)
        m3.metric(t(lang, "total_commission_metric"), f"{summary['total_commission']:.2f} {CURRENCY}", border=True)
        m4.metric(t(lang, "overnight_fee_metric"), f"{summary['total_overnight_fee']:.2f} {CURRENCY}", border=True)
        m5.metric(t(lang, "total_invested_metric"), f"{summary['total_invested']:.2f} {CURRENCY}", border=True)

    with st.container(border=True):
        st.caption(t(lang, "price_levels_group_header"))
        m6, m7 = st.columns(2)
        m6.metric(t(lang, "breakeven_metric"), f"{breakeven:.4f} {CURRENCY}", border=True)
        m7.metric(
            t(lang, "target_price_metric", pct=profit_target_pct), f"{target:.4f} {CURRENCY}", border=True
        )

    with st.container(border=True):
        st.caption(t(lang, "pnl_group_header"))
        m8, m9 = st.columns(2)
        m8.metric(
            t(lang, "pnl_metric"),
            f"{pnl:+.2f} {CURRENCY}",
            delta=f"{pnl_pct:+.2f}%",
            help=f"{current_price:.2f} vs {breakeven:.4f}",
            border=True,
        )
        try:
            pln_rate_data = cached_pln_rate(refresh_interval)
            pln_rate = pln_rate_data["rate"]
            pnl_pln = pnl * pln_rate
            m9.metric(
                t(lang, "pnl_pln_metric"),
                f"{pnl_pln:+.2f} PLN",
                delta=f"{pnl_pct:+.2f}%",
                border=True,
            )
            st.caption(
                t(
                    lang,
                    "usd_pln_rate_caption",
                    rate=f"{pln_rate:.4f}",
                    source=pln_rate_data["source"],
                    time=pln_rate_data["fetched_at"].strftime("%H:%M:%S"),
                )
            )
        except pricing.PriceFetchError as e:
            st.warning(t(lang, "pln_rate_fetch_error", error=e))
