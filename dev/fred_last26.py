"""
Pull 26 years of historical values for economic indicators from the FRED API
and store them in economic_indicators.db.

Setup:
    pip install requests python-dotenv
    export FRED_API_KEY="your_key_here"   # from fred.stlouisfed.org

Usage:
    python3 dev/fred.py
"""

import os
import sqlite3
import requests
from datetime import datetime, timedelta
from dotenv import load_dotenv

load_dotenv()

FRED_API_KEY = os.environ.get("FRED_API_KEY")
if not FRED_API_KEY:
    raise SystemExit("Set the FRED_API_KEY environment variable first.")

DB_PATH = "economic_indicators.db"
BASE_URL = "https://api.stlouisfed.org/fred/series/observations"

# Set cutoff date to 26 years prior to today
START_DATE = (datetime.now() - timedelta(days=26 * 365.25)).strftime("%Y-%m-%d")

FRED_MAP = {
    "Real GDP Growth Rate (annualized)": "A191RL1Q225SBEA",
    "Nominal GDP": "GDP",
    "Unemployment Rate": "UNRATE",
    "Nonfarm Payroll Employment Change": "PAYEMS",
    "Labor Force Participation Rate": "CIVPART",
    "Average Hourly Earnings (YoY)": "CES0500000003",
    "CPI Inflation Rate (headline, YoY)": "CPIAUCSL",
    "Core CPI Inflation Rate (ex food & energy, YoY)": "CPILFESL",
    "PCE Price Index (headline, YoY)": "PCEPI",
    "Core PCE Price Index (ex food & energy, YoY)": "PCEPILFE",
    "Federal Funds Rate (target range)": "DFEDTARU",
    "10-Year Treasury Yield": "DGS10",
    "Trade Balance (Goods & Services)": "BOPGSTB",
    "Personal Saving Rate": "PSAVERT",
    "Personal Income Change (m/m)": "PI",
    "M2 Money Supply": "M2SL",
    "University of Michigan Consumer Sentiment Index": "UMCSENT",
}


def fetch_history(series_id: str, start_date: str):
    """Return list of (date, value) tuples for series starting from start_date."""
    params = {
        "series_id": series_id,
        "api_key": FRED_API_KEY,
        "file_type": "json",
        "observation_start": start_date,
    }
    resp = requests.get(BASE_URL, params=params, timeout=30)
    resp.raise_for_status()
    observations = resp.json().get("observations", [])
    
    # Filter out missing observations (FRED marks missing data as '.')
    return [
        (obs["date"], obs["value"]) 
        for obs in observations 
        if obs["value"] != "."
    ]


def init_db(cur: sqlite3.Cursor):
    """Recreate schema to ensure composite UNIQUE constraint exists."""
    # Drop the existing table to reset constraints
    cur.execute("DROP TABLE IF EXISTS indicators")
    
    cur.execute(
        """
        CREATE TABLE indicators (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            indicator_name TEXT NOT NULL,
            value REAL,
            display_value TEXT,
            reference_period TEXT NOT NULL,
            retrieved_at TEXT,
            UNIQUE(indicator_name, reference_period)
        )
        """
    )

def main():
    conn = sqlite3.connect(DB_PATH)
    cur = conn.cursor()
    
    init_db(cur)
    retrieved_at = datetime.now().strftime("%Y-%m-%d")

    print(f"Fetching 26-year history (from {START_DATE})...")

    for indicator_name, series_id in FRED_MAP.items():
        try:
            records = fetch_history(series_id, START_DATE)
        except Exception as e:
            print(f"  FAILED   {indicator_name} ({series_id}): {e}")
            continue

        # Prepare batch dataset
        payload = [
            (indicator_name, val, val, ref_date, retrieved_at)
            for ref_date, val in records
        ]

        # Upsert entire history array for this indicator
        cur.executemany(
            """
            INSERT INTO indicators (
                indicator_name, 
                value, 
                display_value, 
                reference_period, 
                retrieved_at
            )
            VALUES (?, ?, ?, ?, ?)
            ON CONFLICT(indicator_name, reference_period) DO UPDATE SET
                value = excluded.value,
                display_value = excluded.display_value,
                retrieved_at = excluded.retrieved_at
            """,
            payload,
        )
        print(f"  OK       {indicator_name}: Inserted/Updated {len(records)} records")

    conn.commit()
    conn.close()
    print("Done.")


if __name__ == "__main__":
    main()
