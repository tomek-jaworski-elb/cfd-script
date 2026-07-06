# Adtran (ADTN) CFD Tracker

Local Streamlit dashboard for tracking a CFD position on Adtran (ticker `ADTN`,
Nasdaq): live price, transaction log (tranches), overnight financing cost,
breakeven price, and target price for a given profit %.

## Setup (one-time)

**Windows (PowerShell):**
```powershell
python -m venv venv
.\venv\Scripts\pip.exe install -r requirements.txt
```

**Linux / WSL:**
```bash
python3 -m venv venv
venv/bin/pip install -r requirements.txt
```

## Run

**Windows (PowerShell):**
```powershell
.\start.ps1     # starts the app in the background, waits until it responds, prints the URL
.\stop.ps1      # stops it (kills the whole process tree)
```

Optional custom port: `.\start.ps1 -Port 8600`.

**Linux / WSL:**
```bash
chmod +x start.sh stop.sh   # one-time
./start.sh        # starts the app in the background, waits until it responds, prints the URL
./stop.sh         # stops it (kills the whole process group)
```

Optional custom port: `./start.sh 8600`. Requires `curl` (used to poll readiness).

Open the printed URL (default `http://localhost:8501`) in a browser.

Logs: `streamlit.log` / `streamlit.err.log`. PID: `streamlit.pid`.

**Warning:** `start.ps1`/`stop.ps1` (Windows) and `start.sh`/`stop.sh` (WSL) don't
see each other's processes — they're different PID namespaces. If you started
the app with one, stop it with the matching script, not the other. Mixing them
leaves a real process running while `stop` reports "already stopped".

## Using the app

- **Sidebar**: language (PL/EN), ticker, overnight financing rate (annual %,
  broker-specific), target profit %, auto-refresh interval (seconds, default
  60). Click "Save settings" to persist.
- **Live price** (grouped in one card): price, source, and an open/closed
  market badge with today's regular session hours converted to Warsaw local
  time (NYSE/Nasdaq regular session is 9:30-16:00 US Eastern, Mon-Fri;
  NYSE holidays and 13:00 ET early closes are accounted for, and the badge
  names the holiday when the market is closed for one). Below that, a live-ticking row
  shows "as of HH:MM:SS (Ns ago)" and a "next update in MM:SS" countdown,
  updating every second on their own without reloading the rest of the page.
  The actual price refetch (and P/L recalculation) happens on the configured
  auto-refresh interval — a full-page rerun. A manual "Refresh price" button
  is also available.
- **Add transaction**: date, quantity, price per share, commission — one row
  per tranche (you bought in two, so add both).
- **Tranches table**: shows nights held and accrued overnight fee per tranche.
- **Position summary**: total quantity, avg entry price, total commission,
  accrued overnight fee, breakeven price, target price, unrealized P/L at the
  current live price.

## Data & storage

- Transactions and settings persist in `cfd_tracker.db` (SQLite, in this
  folder). Restarting the app or the machine does not lose data.
- Live price: `yfinance` (primary), direct Yahoo chart HTTP endpoint
  (fallback if yfinance breaks). No API key needed for either.

## Important caveat

This tracks the **underlying exchange price** for ADTN, not your broker's
actual CFD quote. A real CFD price includes the broker's spread and financing
terms, so it will differ slightly from what this app shows. Breakeven/target
calculations are based on the exchange price as a proxy.

Overnight fee is also a simplification: it's computed as
`quantity × current price × annual rate% / 365 × nights held` per tranche.
Real brokers mark-to-market daily and some triple-charge over weekends — this
app does neither, so treat the accrued overnight fee as an approximation.
