"""Streamlit dashboard for tracking an Adtran (ADTN) CFD position:
live price, transaction log, overnight financing cost, breakeven & target price.
"""
import time
from datetime import date, datetime, time as dtime
from pathlib import Path
from zoneinfo import ZoneInfo

import altair as alt
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
HISTORY_MAX_POINTS = 60
CHART_COLOR = "#2563EB"
CHART_BREAKEVEN_COLOR = "#DC2626"
# Range label -> how far back to fetch and at which intraday interval.
# Intervals grow with the span to keep the point count (and page weight) low.
CHART_RANGES = {
    "24h": {"days": 1, "interval": "5m"},
    "2D": {"days": 2, "interval": "15m"},
    "3D": {"days": 3, "interval": "15m"},
    "5D": {"days": 5, "interval": "30m"},
    "7D": {"days": 7, "interval": "30m"},
}


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


def track_history(key: str, fetched_at, value: float):
    """Record fetched values in session state, appending a point only when the
    value actually differs from the last recorded one — repeated fetches of an
    unchanged value are ignored. Returns (history_values, prev_value,
    prev_fetched_at) where the prev_* pair describes the last value different
    from the current one, or (.., None, None) when no change has been seen yet."""
    hist = st.session_state.setdefault(key, [])
    if not hist or hist[-1]["value"] != value:
        hist.append({"fetched_at": fetched_at, "value": value})
        del hist[:-HISTORY_MAX_POINTS]
    values = [point["value"] for point in hist]
    if len(hist) >= 2:
        prev = hist[-2]
        return values, prev["value"], prev["fetched_at"]
    return values, None, None


def delta_args(lang: str, current: float, prev: float | None, decimals: int, unit: str = ""):
    """Build st.metric delta kwargs for the change vs the last different value.
    No previous value -> no delta; a change too small to show at the requested
    precision -> neutral gray 'no change' marker."""
    if prev is None:
        return {}
    diff = current - prev
    if abs(diff) < (10 ** -decimals) / 2:
        return {"delta": t(lang, "no_change_delta"), "delta_color": "off"}
    pct = (diff / prev * 100.0) if prev else 0.0
    unit_suffix = f" {unit}" if unit else ""
    return {"delta": f"{diff:+.{decimals}f}{unit_suffix} ({pct:+.2f}%)"}


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


@st.cache_data(ttl=refresh_interval)
def cached_history(tkr: str, days: int, interval: str, _interval: int):
    return pricing.get_price_history(tkr, days, interval)


@st.fragment(run_every=f"{refresh_interval}s")
def _autorefresh_tick():
    # A fragment's body also runs immediately on every normal (non-scheduled)
    # script execution, not just on its run_every timer - without this guard,
    # st.rerun() below would fire on every rerun and loop forever. Only escalate
    # to a full-app rerun once the configured interval has actually elapsed.
    if time.monotonic() - st.session_state.last_full_rerun >= refresh_interval:
        st.session_state.last_full_rerun = time.monotonic()
        # The TTL cache gets populated slightly AFTER last_full_rerun is
        # stamped, so at this point the cached entry can still look fresh and
        # would serve the same stale price for one more whole interval. Clear
        # explicitly so the full-app rerun below always refetches.
        cached_price.clear()
        cached_pln_rate.clear()
        cached_history.clear()
        st.rerun()  # default scope inside a fragment is a full-app rerun


_autorefresh_tick()


@st.fragment(run_every="1s")
def _live_clock(fetched_at, interval_sec, lang):
    # Fragment-scoped only (no st.rerun()) - ticks every second without
    # forcing a full-page rerun, so price/P/L stay put between real refreshes.
    elapsed = (datetime.now(WARSAW_TZ) - fetched_at).total_seconds()
    seconds_ago = max(0, int(elapsed))
    seconds_left = max(0, int(interval_sec - elapsed))
    st.progress(
        min(1.0, max(0.0, elapsed / interval_sec)) if interval_sec else 1.0,
        text=t(
            lang,
            "live_clock_text",
            time=fetched_at.strftime("%H:%M:%S"),
            ago=t(lang, "seconds_ago_suffix", s=seconds_ago),
            left=f"{seconds_left // 60:02d}:{seconds_left % 60:02d}",
        ),
    )


def render_price_chart(lang: str, tkr: str, breakeven: float | None):
    """Intraday price chart with a range selector (24h-7D). Interactive Altair
    area chart: hover tooltip, drag to pan, scroll to zoom (x-axis only),
    double-click to reset. Optional dashed breakeven rule when it falls inside
    the visible price range."""
    range_labels = list(CHART_RANGES)
    selected = (
        st.segmented_control(
            t(lang, "chart_range_label"),
            range_labels,
            default=range_labels[0],
            key="chart_range",
            label_visibility="collapsed",
        )
        or range_labels[0]
    )
    cfg = CHART_RANGES[selected]
    try:
        hist = cached_history(tkr, cfg["days"], cfg["interval"], refresh_interval)
    except pricing.PriceFetchError as e:
        st.warning(t(lang, "history_fetch_error", error=e))
        return
    if not hist["points"]:
        st.info(t(lang, "chart_no_data"))
        return

    df = pd.DataFrame(hist["points"])
    # Vega renders naive timestamps as-is, so convert to Warsaw time up front
    # instead of trusting the browser's timezone.
    df["ts"] = pd.to_datetime(df["ts"], utc=True).dt.tz_convert(WARSAW_TZ).dt.tz_localize(None)

    lo, hi = float(df["price"].min()), float(df["price"].max())
    pad = (hi - lo) * 0.08 or hi * 0.002
    y_scale = alt.Scale(domain=[lo - pad, hi + pad], nice=False)
    x_axis = alt.Axis(title=None, format="%H:%M" if cfg["days"] == 1 else "%d.%m %H:%M")
    tooltip = [
        alt.Tooltip("ts:T", title=t(lang, "chart_time_label"), format="%d.%m %H:%M"),
        alt.Tooltip("price:Q", title=t(lang, "chart_price_label"), format=".2f"),
    ]

    area = (
        alt.Chart(df)
        .mark_area(
            interpolate="monotone",
            line={"color": CHART_COLOR, "strokeWidth": 2},
            color=alt.Gradient(
                gradient="linear",
                stops=[
                    alt.GradientStop(color="rgba(37, 99, 235, 0.02)", offset=0),
                    alt.GradientStop(color="rgba(37, 99, 235, 0.30)", offset=1),
                ],
                x1=1, x2=1, y1=1, y2=0,
            ),
        )
        .encode(
            x=alt.X("ts:T", axis=x_axis),
            y=alt.Y("price:Q", scale=y_scale, axis=alt.Axis(title=None, format=".2f")),
        )
    )
    hover_points = (
        alt.Chart(df)
        .mark_point(size=90, opacity=0)
        .encode(x="ts:T", y=alt.Y("price:Q", scale=y_scale), tooltip=tooltip)
    )
    layers = [area, hover_points]
    if breakeven and lo - pad <= breakeven <= hi + pad:
        rule_df = pd.DataFrame(
            {"price": [breakeven], "label": [t(lang, "chart_breakeven_label")]}
        )
        layers.append(
            alt.Chart(rule_df)
            .mark_rule(strokeDash=[6, 4], strokeWidth=1.5, color=CHART_BREAKEVEN_COLOR, clip=True)
            .encode(
                y=alt.Y("price:Q", scale=y_scale),
                tooltip=[
                    alt.Tooltip("label:N", title=" "),
                    alt.Tooltip("price:Q", title=t(lang, "chart_price_label"), format=".4f"),
                ],
            )
        )

    chart = alt.layer(*layers).properties(height=260).interactive(bind_y=False)
    st.altair_chart(chart, width="stretch")
    st.caption(t(lang, "chart_caption", source=hist["source"], interval=cfg["interval"]))


# --- Live price ---
st.subheader(t(lang, "live_price_header"))
try:
    price_data = cached_price(ticker, refresh_interval)
    fetched_at = price_data["fetched_at"]
    current_price = price_data["price"]
    is_open, open_warsaw, close_warsaw = market_status()
    price_hist, prev_price, prev_price_at = track_history(
        f"price_history_{ticker}", fetched_at, current_price
    )

    with st.container(border=True):
        col_price, col_status = st.columns([3, 2], vertical_alignment="center")
        with col_price:
            st.metric(
                t(lang, "price_metric_label", ticker=ticker),
                f"{current_price:.2f} {CURRENCY}",
                chart_data=price_hist if len(price_hist) >= 2 else None,
                chart_type="area",
                **delta_args(lang, current_price, prev_price, decimals=2, unit=CURRENCY),
            )
            if prev_price is not None:
                st.caption(
                    t(
                        lang,
                        "prev_value_caption",
                        value=f"{prev_price:.2f} {CURRENCY}",
                        time=prev_price_at.strftime("%H:%M:%S"),
                    )
                )
        with col_status:
            st.badge(
                t(lang, "market_open") if is_open else t(lang, "market_closed"),
                icon="🟢" if is_open else "🔴",
                color="green" if is_open else "gray",
            )
            st.badge(price_data["source"], icon="📡", color="blue")
            st.caption(
                t(
                    lang,
                    "market_hours_caption",
                    open=open_warsaw.strftime("%H:%M"),
                    close=close_warsaw.strftime("%H:%M"),
                )
            )

        _live_clock(fetched_at, refresh_interval, lang)
except pricing.PriceFetchError as e:
    st.error(t(lang, "price_fetch_error", error=e))
    current_price = st.number_input(t(lang, "manual_price_label"), min_value=0.0, step=0.01)

def _refresh_price_and_rate():
    cached_price.clear()
    cached_pln_rate.clear()
    cached_history.clear()

st.button(t(lang, "refresh_price_button"), on_click=_refresh_price_and_rate)

transactions = db.get_transactions()
summary = calc.summarize(transactions, current_price, overnight_rate) if transactions else None

# --- Price chart ---
with st.container(border=True):
    st.caption(t(lang, "chart_header"))
    render_price_chart(lang, ticker, summary["breakeven_price"] if summary else None)

# --- Position summary ---
if summary:
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
        m8, m9, m10 = st.columns(3)
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
            rate_hist, prev_rate, _prev_rate_at = track_history(
                "usd_pln_history", pln_rate_data["fetched_at"], pln_rate
            )
            pnl_pln = pnl * pln_rate
            m9.metric(
                t(lang, "pnl_pln_metric"),
                f"{pnl_pln:+.2f} PLN",
                delta=f"{pnl_pct:+.2f}%",
                border=True,
            )
            m10.metric(
                t(lang, "usd_pln_rate_metric"),
                f"{pln_rate:.4f}",
                chart_data=rate_hist if len(rate_hist) >= 2 else None,
                chart_type="area",
                border=True,
                **delta_args(lang, pln_rate, prev_rate, decimals=4),
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

# --- Tranches ---
st.divider()
st.subheader(t(lang, "tranches_header"))

if not summary:
    st.info(t(lang, "no_transactions_info"))
else:
    @st.dialog(t(lang, "edit_tranche_title"))
    def edit_tranche_dialog(tx):
        trade_date = st.date_input(t(lang, "date_label"), value=date.fromisoformat(tx["trade_date"]))
        quantity = st.number_input(
            t(lang, "quantity_label"), min_value=0.0, step=1.0, value=float(tx["quantity"])
        )
        price = st.number_input(
            t(lang, "price_per_share_label"), min_value=0.0, step=0.01, value=float(tx["price"])
        )
        commission = st.number_input(
            t(lang, "commission_label"), min_value=0.0, step=0.01, value=float(tx["commission"])
        )
        if st.button(t(lang, "save_button")):
            if quantity <= 0 or price <= 0:
                st.error(t(lang, "qty_price_error"))
            else:
                db.update_transaction(tx["id"], trade_date.isoformat(), quantity, price, commission)
                st.rerun()

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
    event = st.dataframe(
        tranche_df,
        width="stretch",
        hide_index=True,
        on_select="rerun",
        selection_mode="single-row",
        key="tranche_table",
    )
    selected_rows = event.selection.rows
    if selected_rows and selected_rows[0] < len(summary["per_tranche"]):
        tx = summary["per_tranche"][selected_rows[0]]
        edit_col, del_col, _ = st.columns([1, 1, 4])
        if edit_col.button(f"✏️ {t(lang, 'edit_button')}", width="stretch"):
            edit_tranche_dialog(tx)
        if del_col.button(f"🗑️ {t(lang, 'delete_button')}", width="stretch"):
            db.delete_transaction(tx["id"])
            st.session_state.pop("tranche_table", None)
            st.rerun()
    else:
        st.caption(t(lang, "select_row_hint"))

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
            st.rerun()
