"""Streamlit dashboard for tracking an Adtran (ADTN) CFD position:
live price, transaction log, overnight financing cost, breakeven & target price.
"""
from datetime import date

import pandas as pd
import streamlit as st

import calc
import db
import pricing
from i18n import t

st.set_page_config(page_title="Adtran CFD Tracker", layout="wide")
db.init_db()

CURRENCY = "USD"

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
    if st.button(t(lang, "save_settings_button")):
        db.set_setting("ticker", ticker)
        db.set_setting("overnight_rate_annual_pct", str(overnight_rate))
        db.set_setting("profit_target_pct", str(profit_target_pct))
        st.success(t(lang, "settings_saved"))

    st.caption(t(lang, "cfd_note"))


@st.cache_data(ttl=30)
def cached_price(tkr: str):
    return pricing.get_current_price(tkr)


@st.cache_data(ttl=3600)
def cached_pln_rate():
    return pricing.get_usd_pln_rate()


# --- Live price ---
st.subheader(t(lang, "live_price_header"))
try:
    price_data = cached_price(ticker)
    col1, col2, col3 = st.columns(3)
    col1.metric(t(lang, "price_metric_label", ticker=ticker), f"{price_data['price']:.2f} {CURRENCY}")
    col2.metric(t(lang, "source_metric_label"), price_data["source"])
    col3.metric(t(lang, "as_of_metric_label"), date.today().isoformat())
    current_price = price_data["price"]
except pricing.PriceFetchError as e:
    st.error(t(lang, "price_fetch_error", error=e))
    current_price = st.number_input(t(lang, "manual_price_label"), min_value=0.0, step=0.01)

st.button(t(lang, "refresh_price_button"), on_click=cached_price.clear)

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
    st.dataframe(tranche_df, use_container_width=True, hide_index=True)

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

    m1, m2, m3 = st.columns(3)
    m1.metric(t(lang, "total_qty_metric"), f"{summary['total_qty']:.2f}")
    m2.metric(t(lang, "avg_entry_price_metric"), f"{summary['avg_entry_price']:.4f} {CURRENCY}")
    m3.metric(t(lang, "total_commission_metric"), f"{summary['total_commission']:.2f} {CURRENCY}")

    m4, m5, m6 = st.columns(3)
    m4.metric(t(lang, "overnight_fee_metric"), f"{summary['total_overnight_fee']:.2f} {CURRENCY}")
    m5.metric(t(lang, "total_invested_metric"), f"{summary['total_invested']:.2f} {CURRENCY}")
    m6.metric(t(lang, "breakeven_metric"), f"{breakeven:.4f} {CURRENCY}")

    m7, m8 = st.columns(2)
    m7.metric(t(lang, "target_price_metric", pct=profit_target_pct), f"{target:.4f} {CURRENCY}")
    m8.metric(
        t(lang, "pnl_metric"),
        f"{pnl:+.2f} {CURRENCY}",
        delta=f"{pnl_pct:+.2f}%",
        help=f"{current_price:.2f} vs {breakeven:.4f}",
    )

    try:
        pln_rate_data = cached_pln_rate()
        pln_rate = pln_rate_data["rate"]
        pnl_pln = pnl * pln_rate
        m9, m10 = st.columns(2)
        m9.metric(
            t(lang, "pnl_pln_metric"),
            f"{pnl_pln:+.2f} PLN",
            delta=f"{pnl_pct:+.2f}%",
        )
        m10.metric(
            t(lang, "usd_pln_rate_metric"),
            f"{pln_rate:.4f}",
            delta=pln_rate_data["source"],
        )
    except pricing.PriceFetchError as e:
        st.warning(t(lang, "pln_rate_fetch_error", error=e))
