# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## What this is

Single-page Streamlit dashboard for tracking a CFD position on Adtran (ADTN): live price, transaction log (tranches), overnight financing cost, breakeven/target price, unrealized P/L (USD + PLN). Python, SQLite, no tests, no linter configured.

## Commands

Two separate venvs exist and the start scripts hardcode them: `venv` (Windows) and `venv_wsl_test` (WSL/Linux, Python 3.12). Setup:

```powershell
# Windows
python -m venv venv
.\venv\Scripts\pip.exe install -r requirements.txt
```

```bash
# WSL/Linux
python3 -m venv venv_wsl_test
venv_wsl_test/bin/pip install -r requirements.txt
```

Run (background, waits for readiness, prints URL; default port 8501):

```powershell
.\start.ps1          # optional: -Port 8600
.\stop.ps1
```

```bash
./start.sh           # optional: ./start.sh 8600
./stop.sh
```

**Do not mix them**: the PS and WSL scripts live in different PID namespaces — stop with the same variant you started with, or a stray process keeps running. Logs: `streamlit.log` / `streamlit.err.log`, PID in `streamlit.pid`.

`start.sh` passes `--server.fileWatcherType none` because the repo sits on a Windows drive mounted into WSL (DrvFs) where Streamlit's watcher stalls startup ~50s — code changes under WSL therefore require an app restart, not just a browser reload.

## Architecture

Flat modules, `app.py` is the only Streamlit-aware file; the rest are plain Python:

- `app.py` — all UI. Reads settings from DB, renders sidebar/metrics/tranche table/add form.
- `calc.py` — pure position math (breakeven, overnight fee, P/L). No I/O, no Streamlit.
- `db.py` — SQLite (`cfd_tracker.db` in repo root): `transactions` and `settings` (key/value, defaults in `DEFAULT_SETTINGS`). Opens/closes a connection per call.
- `pricing.py` — price fetch with primary/fallback pairs, no API keys: stock price and intraday history via yfinance → raw Yahoo chart endpoint; USD/PLN via yfinance → NBP API. All raise `PriceFetchError` only when both paths fail; `app.py` catches it (manual price entry for the spot price, warning for history/FX).
- `.streamlit/config.toml` — native theming only (light palette + `[theme.dark]` variant, follows system preference). No CSS injection — keep it that way.
- `i18n.py` — `STRINGS` dict with `pl` and `en`; access via `t(lang, key, **fmt)`. **Every new UI string must be added to both languages.**

### Refresh model (the tricky part of app.py)

Two `@st.fragment` functions coexist:
- `_autorefresh_tick` (`run_every=refresh_interval`) escalates to a full-app `st.rerun()`, guarded by `st.session_state.last_full_rerun` — a fragment body also runs on every normal rerun, so without the guard it would loop forever.
- `_live_clock` (`run_every="1s"`) ticks the "as of / next update" progress bar fragment-scoped only — no `st.rerun()`, so price/P/L stay put between real refreshes.

Price, FX and chart-history data go through `@st.cache_data(ttl=refresh_interval)`; `_autorefresh_tick` and the manual "Refresh price" button clear all three caches explicitly (TTL alone races with the tick and would serve a stale price for a whole interval). Price-change deltas/sparklines come from `track_history()` in `st.session_state` (a point is appended only when the value actually changes, so deltas compare against the last *different* value, not the last fetch).

The intraday chart (`render_price_chart`) is Altair (bundled with Streamlit — do not add Plotly or chart components; the app must stay light). Range selector maps labels to fetch spans/intervals via `CHART_RANGES`; intervals grow with the span to cap point counts. Timestamps are converted to Warsaw time and made tz-naive before hitting Vega (browser-tz independence).

## Conventions

- `cfd_tracker.db` contains the user's real position data (gitignored). Never delete or reset it.
- `VERSION` file: line 1 = semver, line 2 = release date (YYYY-MM-DD). The app displays it in the sidebar — bump both lines when shipping a user-visible change.
- Money/dates: prices in USD, dates stored as ISO strings (`YYYY-MM-DD`) in SQLite; timezone math uses `zoneinfo` (`America/New_York` for market hours, `Europe/Warsaw` for display).
- Financial caveats are intentional simplifications documented in README.md and module docstrings (exchange price as CFD proxy, flat 365-day overnight fee, no weekend triple-charge, no exchange holidays) — don't "fix" them silently.
