"""SQLite storage for CFD transactions and app settings."""
import sqlite3
from pathlib import Path

DB_PATH = Path(__file__).parent / "cfd_tracker.db"

DEFAULT_SETTINGS = {
    "ticker": "ADTN",
    "overnight_rate_annual_pct": "6.8",
    "profit_target_pct": "5.0",
    "lang": "pl",
    "refresh_interval_sec": "60",
}


def get_connection():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn


def init_db():
    conn = get_connection()
    conn.execute(
        """
        CREATE TABLE IF NOT EXISTS transactions (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            trade_date TEXT NOT NULL,
            quantity REAL NOT NULL,
            price REAL NOT NULL,
            commission REAL NOT NULL DEFAULT 0
        )
        """
    )
    conn.execute(
        """
        CREATE TABLE IF NOT EXISTS settings (
            key TEXT PRIMARY KEY,
            value TEXT NOT NULL
        )
        """
    )
    for key, value in DEFAULT_SETTINGS.items():
        conn.execute(
            "INSERT OR IGNORE INTO settings (key, value) VALUES (?, ?)", (key, value)
        )
    conn.commit()
    conn.close()


def add_transaction(trade_date: str, quantity: float, price: float, commission: float):
    conn = get_connection()
    conn.execute(
        "INSERT INTO transactions (trade_date, quantity, price, commission) VALUES (?, ?, ?, ?)",
        (trade_date, quantity, price, commission),
    )
    conn.commit()
    conn.close()


def update_transaction(tx_id: int, trade_date: str, quantity: float, price: float, commission: float):
    conn = get_connection()
    conn.execute(
        "UPDATE transactions SET trade_date = ?, quantity = ?, price = ?, commission = ? WHERE id = ?",
        (trade_date, quantity, price, commission, tx_id),
    )
    conn.commit()
    conn.close()


def delete_transaction(tx_id: int):
    conn = get_connection()
    conn.execute("DELETE FROM transactions WHERE id = ?", (tx_id,))
    conn.commit()
    conn.close()


def get_transactions():
    conn = get_connection()
    rows = conn.execute("SELECT * FROM transactions ORDER BY trade_date").fetchall()
    conn.close()
    return [dict(row) for row in rows]


def get_setting(key: str) -> str:
    conn = get_connection()
    row = conn.execute("SELECT value FROM settings WHERE key = ?", (key,)).fetchone()
    conn.close()
    return row["value"] if row else DEFAULT_SETTINGS.get(key, "")


def set_setting(key: str, value: str):
    conn = get_connection()
    conn.execute(
        "INSERT INTO settings (key, value) VALUES (?, ?) "
        "ON CONFLICT(key) DO UPDATE SET value = excluded.value",
        (key, value),
    )
    conn.commit()
    conn.close()
