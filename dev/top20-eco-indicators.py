import sqlite3
from datetime import datetime

DB_PATH = "economic_indicators.db"

conn = sqlite3.connect(DB_PATH)
cur = conn.cursor()

cur.executescript("""
DROP TABLE IF EXISTS indicators;
CREATE TABLE indicators (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    rank INTEGER NOT NULL,
    indicator_name TEXT NOT NULL,
    category TEXT NOT NULL,
    value REAL,
    display_value TEXT NOT NULL,
    unit TEXT NOT NULL,
    reference_period TEXT NOT NULL,
    release_date TEXT,
    source_agency TEXT NOT NULL,
    source_url TEXT,
    notes TEXT,
    retrieved_at TEXT NOT NULL
);
""")

retrieved_at = datetime.utcnow().strftime("%Y-%m-%d")

rows = [
    # rank, name, category, value(float, signed, base unit), display_value, unit, period, release_date, agency, url, notes
    (1, "Real GDP Growth Rate (annualized)", "Growth", 1.5, "1.5%", "percent, annualized q/q",
     "Q2 2026", "2026-08-26", "Bureau of Economic Analysis (BEA)",
     "https://www.bea.gov/news/2026/gdp-second-estimate-and-corporate-profits-2nd-quarter-2026",
     "Second estimate; down from 2.1% in Q1 2026"),

    (2, "Nominal GDP", "Growth", 32486.0, "$32.486 trillion", "USD, current dollars, annualized",
     "Q2 2026", "2026-08-26", "Bureau of Economic Analysis (BEA) / JEC", None,
     "Current-dollar GDP up 8.02% annualized ($620.3B) from Q1"),

    (3, "Unemployment Rate", "Labor Market", 4.1, "4.1%", "percent",
     "August 2026", "2026-09-04", "Bureau of Labor Statistics (BLS)",
     "https://www.bls.gov/news.release/empsit.nr0.htm",
     "Unchanged from July; 7.0 million unemployed"),

    (4, "Nonfarm Payroll Employment Change", "Labor Market", 162000, "+162,000 jobs", "jobs added, monthly",
     "August 2026", "2026-09-04", "Bureau of Labor Statistics (BLS)",
     "https://www.bls.gov/news.release/empsit.nr0.htm",
     "Far exceeded consensus forecast of ~53,000-56,000"),

    (5, "Labor Force Participation Rate", "Labor Market", 61.6, "61.6%", "percent",
     "August 2026", "2026-09-04", "Bureau of Labor Statistics (BLS)", None,
     "Down 0.5 pp since January 2026"),

    (6, "Average Hourly Earnings (YoY)", "Labor Market", 3.1, "3.1%", "percent change, year-over-year",
     "August 2026", "2026-09-04", "Bureau of Labor Statistics (BLS)", None,
     "Average hourly earnings $37.75, +$0.10 (0.3%) m/m"),

    (7, "CPI Inflation Rate (headline, YoY)", "Inflation", 3.4, "3.4%", "percent change, year-over-year",
     "July 2026", "2026-08-12", "Bureau of Labor Statistics (BLS)",
     "https://www.bls.gov/news.release/cpi.nr0.htm",
     "Down from 3.5% in June; +0.1% m/m"),

    (8, "Core CPI Inflation Rate (ex food & energy, YoY)", "Inflation", 2.5, "2.5%", "percent change, year-over-year",
     "July 2026", "2026-08-12", "Bureau of Labor Statistics (BLS)", None,
     "+0.2% m/m"),

    (9, "PCE Price Index (headline, YoY)", "Inflation", 3.7, "3.7%", "percent change, year-over-year",
     "July 2026", "2026-08-26", "Bureau of Economic Analysis (BEA)",
     "https://www.bea.gov/news/2026/personal-income-and-outlays-july-2026",
     "Fed's preferred inflation gauge; hotter than expected"),

    (10, "Core PCE Price Index (ex food & energy, YoY)", "Inflation", 3.3, "3.3%", "percent change, year-over-year",
     "July 2026", "2026-08-26", "Bureau of Economic Analysis (BEA)", None,
     "In line with consensus"),

    (11, "Federal Funds Rate (target range)", "Monetary Policy", 3.75, "3.50%-3.75% (upper bound shown)",
     "percent, target range",
     "As of Sep 2026 (held since Dec 2025)", "2026-04-29 (last FOMC hold)", "Federal Reserve (FOMC)",
     "https://fred.stlouisfed.org/series/DFEDTARU",
     "Third consecutive hold in 2026 after three 25bp cuts in late 2025"),

    (12, "10-Year Treasury Yield", "Interest Rates", 4.79, "4.79%", "percent, daily close",
     "September 4, 2026", "2026-09-04", "U.S. Treasury / Federal Reserve",
     "https://tradingeconomics.com/united-states/government-bond-yield",
     "Rose ~3bps after strong August jobs report"),

    (13, "ISM Manufacturing PMI", "Business Activity", 54.6, "54.6", "index (50 = breakeven)",
     "August 2026", "2026-09-01", "Institute for Supply Management (ISM)",
     "https://www.prnewswire.com/news-releases/manufacturing-pmi-at-54-6-august-2026-ism-manufacturing-pmi-report-302865127.html",
     "8th consecutive month of expansion; down 1.0 pt from July's 55.6"),

    (14, "ISM Services PMI", "Business Activity", 55.4, "55.4", "index (50 = breakeven)",
     "August 2026", "2026-09-03", "Institute for Supply Management (ISM)",
     "https://www.prnewswire.com/news-releases/services-pmi-at-55-4-august-2026-ism-services-pmi-report-302868046.html",
     "26th consecutive month of expansion"),

    (15, "Conference Board Consumer Confidence Index", "Sentiment", 89.4, "89.4 (1985=100)", "index",
     "August 2026", "2026-08-25", "The Conference Board",
     "http://www.prnewswire.com/news-releases/us-consumer-confidence-edged-down-slightly-in-august-302859371.html",
     "Down 0.8 pt from July's 90.2"),

    (16, "University of Michigan Consumer Sentiment Index", "Sentiment", 51.7, "51.7 (final)", "index",
     "August 2026", "2026-08-28", "University of Michigan Surveys of Consumer Research", None,
     "Revised up from preliminary 51.0; down from 55.2 in July"),

    (17, "Trade Balance (Goods & Services)", "Trade", -88.6, "-$88.6 billion (deficit)", "USD billions, monthly",
     "July 2026", "2026-09-03", "Census Bureau / Bureau of Economic Analysis (BEA)",
     "https://bea.gov/news/2026/us-international-trade-goods-and-services-july-2026",
     "Deficit widened $17.4B from June's $71.2B; exports $310.7B, imports $399.3B"),

    (18, "Personal Saving Rate", "Income & Spending", 3.0, "3.0%", "percent of disposable personal income",
     "July 2026", "2026-08-26", "Bureau of Economic Analysis (BEA)", None,
     "Personal saving was $712.0 billion in July"),

    (19, "Personal Income Change (m/m)", "Income & Spending", 0.4, "+0.4% ($115.1B)", "percent change, monthly",
     "July 2026", "2026-08-26", "Bureau of Economic Analysis (BEA)", None,
     "Disposable personal income rose 0.5% ($125.9B)"),

    (20, "M2 Money Supply", "Monetary Policy", 23050.0, "~$23.05 trillion", "USD, billions/trillions",
     "May 2026", "2026-06-25", "Federal Reserve (H.6 release) / FRED", None,
     "Broad measure of money supply including cash, checking, savings, and money market funds"),
]

cur.executemany("""
    INSERT INTO indicators (
        rank, indicator_name, category, value, display_value, unit,
        reference_period, release_date, source_agency, source_url, notes, retrieved_at
    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
""", [r + (retrieved_at,) for r in rows])

conn.commit()

# Sanity check output
cur.execute("SELECT COUNT(*) FROM indicators")
count = cur.fetchone()[0]
print(f"Inserted {count} rows into {DB_PATH}")

cur.execute("SELECT rank, indicator_name, display_value, reference_period, source_agency FROM indicators ORDER BY rank")
for row in cur.fetchall():
    print(row)

conn.close()
