"""
Pull current values for economic indicators from the FRED API and
update economic_indicators.db.

Setup:
    pip install requests
    export FRED_API_KEY="your_key_here"   # from fred.stlouisfed.org

Usage:
    python3 update_from_fred.py
"""

import os
import sqlite3
import requests
from datetime import datetime

FRED_API_KEY = os.environ.get("FRED_API_KEY")
if not FRED_API_KEY:
    raise SystemExit("Set the FRED_API_KEY environment variable first.")

DB_PATH = "economic_indicators.db"
BASE_URL = "https://api.stlouisfed.org/fred/series/observations"

# indicator_name (must match the 'indicator_name' column) -> FRED series id
FRED_MAP = {
    "Real GDP Growth Rate (annualized)": "A191RL1Q225SBEA",
    "Nominal GDP": "GDP",
    "Unemployment Rate": "UNRATE",
    "Nonfarm Payroll Employment Change": "PAYEMS",       # note: level, not monthly change
    "Labor Force Participation Rate": "CIVPART",
    "Average Hourly Earnings (YoY)": "CES0500000003",     # level; compute YoY yourself
    "CPI Inflation Rate (headline, YoY)": "CPIAUCSL",     # level; compute YoY yourself
    "Core CPI Inflation Rate (ex food & energy, YoY)": "CPILFESL",
    "PCE Price Index (headline, YoY)": "PCEPI",
    "Core PCE Price Index (ex food & energy, YoY)": "PCEPILFE",
    "Federal Funds Rate (target range)": "DFEDTARU",
    "10-Year Treasury Yield": "DGS10",
    "Trade Balance (Goods & Services)": "BOPGSTB",
    "Personal Saving Rate": "PSAVERT",
    "Personal Income Change (m/m)": "PI",                 # level; compute % change yourself
    "M2 Money Supply": "M2SL",
    "University of Michigan Consumer Sentiment Index": "UMCSENT",
}


def fetch_latest(series_id: str):
    """Return (date, value) for the most recent observation of a FRED series."""
    params = {
        "series_id": series_id,
        "api_key": FRED_API_KEY,
        "file_type": "json",
        "sort_order": "desc",
        "limit": 1,
    }
    resp = requests.get(BASE_URL, params=params, timeout=15)
    resp.raise_for_status()
    obs = resp.json()["observations"][0]
    return obs["date"], obs["value"]


def main():
    conn = sqlite3.connect(DB_PATH)
    cur = conn.cursor()
    retrieved_at = datetime.now().strftime("%Y-%m-%d")

    for indicator_name, series_id in FRED_MAP.items():
        try:
            date, value = fetch_latest(series_id)
        except Exception as e:
            print(f"  FAILED  {indicator_name} ({series_id}): {e}")
            continue

        cur.execute(
            """
            UPDATE indicators
            SET value = ?,
                display_value = ?,
                reference_period = ?,
                retrieved_at = ?
            WHERE indicator_name = ?
            """,
            (value, value, date, retrieved_at, indicator_name),
        )
        print(f"  OK      {indicator_name}: {value} (as of {date})")

    conn.commit()
    conn.close()
    print("Done.")


if __name__ == "__main__":
    main()
