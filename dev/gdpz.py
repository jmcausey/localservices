import sqlite3
import pandas as pd
import matplotlib.pyplot as plt

# 1. Fetch Nominal GDP and Real GDP Growth Rate from SQLite
conn = sqlite3.connect("economic_indicators.db")
query = """
    SELECT indicator_name, reference_period, display_value 
    FROM indicators 
    WHERE indicator_name IN ('Nominal GDP', 'Real GDP Growth Rate (annualized)')
    ORDER BY reference_period ASC
"""
df = pd.read_sql_query(query, conn)
conn.close()

# 2. Data Cleaning & Reshaping
df["reference_period"] = pd.to_datetime(df["reference_period"])
df["display_value"] = pd.to_numeric(df["display_value"], errors="coerce")

# Pivot table so each indicator gets its own column indexed by date
pivot_df = df.pivot(
    index="reference_period", 
    columns="indicator_name", 
    values="display_value"
).dropna()

# 3. Create Plot with Dual Y-Axes
fig, ax1 = plt.subplots(figsize=(12, 6))

# Plot Nominal GDP on the primary (left) axis
color_nom = "#1f77b4"  # Blue
ax1.set_xlabel("Date", fontsize=11, labelpad=10)
ax1.set_ylabel("Nominal GDP (Billions $)", color=color_nom, fontsize=11)
line1 = ax1.plot(
    pivot_df.index, 
    pivot_df["Nominal GDP"], 
    color=color_nom, 
    linewidth=2, 
    label="Nominal GDP ($B)"
)
ax1.tick_params(axis="y", labelcolor=color_nom)

# Create twin axis for Real GDP Growth Rate on the secondary (right) axis
ax2 = ax1.twinx()
color_real = "#ff7f0e"  # Orange
ax2.set_ylabel("Real GDP Growth Rate (Annualized %)", color=color_real, fontsize=11)
line2 = ax2.plot(
    pivot_df.index, 
    pivot_df["Real GDP Growth Rate (annualized)"], 
    color=color_real, 
    linewidth=1.5, 
    linestyle="--", 
    label="Real GDP Growth Rate (%)"
)
ax2.tick_params(axis="y", labelcolor=color_real)

# 4. Combine Legends and Apply Formatting
lines = line1 + line2
labels = [l.get_label() for l in lines]
ax1.legend(lines, labels, loc="upper left")

plt.title("Nominal GDP vs. Real GDP Growth Rate Time Series", fontsize=14, fontweight="bold", pad=15)
ax1.grid(True, linestyle=":", alpha=0.6)

plt.tight_layout()
plt.savefig("gdp_comparison.png", dpi=300)
plt.show()
