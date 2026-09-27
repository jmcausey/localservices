import sqlite3
import pandas as pd
import matplotlib.pyplot as plt

# 1. Load data from SQLite database
conn = sqlite3.connect("economic_indicators.db")
query = """
    SELECT reference_period, display_value 
    FROM indicators 
    WHERE indicator_name = '10-Year Treasury Yield'
    ORDER BY reference_period ASC
"""
df = pd.read_sql_query(query, conn)
conn.close()

# 2. Convert data types
df["reference_period"] = pd.to_datetime(df["reference_period"])
df["display_value"] = pd.to_numeric(df["display_value"], errors="coerce")

# Drop any invalid/missing numeric entries
df = df.dropna(subset=["display_value"])

# 3. Build Matplotlib figure
plt.figure(figsize=(12, 6))
plt.plot(
    df["reference_period"], 
    df["display_value"], 
    color="#0055ff", 
    linewidth=1.5, 
    label="10-Year Treasury Yield (%)"
)

# 4. Styling & Labels
plt.title("10-Year Treasury Yield Time Series", fontsize=14, fontweight="bold", pad=15)
plt.xlabel("Date", fontsize=11, labelpad=10)
plt.ylabel("Yield (%)", fontsize=11, labelpad=10)
plt.grid(True, linestyle="--", alpha=0.5)
plt.legend(loc="upper right")

plt.tight_layout()
plt.savefig("10_year_treasury_yield.png", dpi=300)
plt.show()
