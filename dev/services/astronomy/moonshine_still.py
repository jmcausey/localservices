import sqlite3
import numpy as np
import matplotlib.pyplot as plt
from matplotlib.patches import Polygon, Circle

# 1. Fetch latest data from database
conn = sqlite3.connect("data/flaskr.sqlite")  # Update with your .db file path
cursor = conn.cursor()

query = """
    SELECT timestamp, moon_illumination_percentage, moon_phase 
    FROM astronomy 
    ORDER BY id DESC 
    LIMIT 1
"""
cursor.execute(query)
row = cursor.fetchone()
conn.close()

if not row:
    raise ValueError("No records found in the astronomy table.")

timestamp, illumination, phase_name = row
illumination = illumination if illumination is not None else 0.0
phase_name = phase_name if phase_name else "UNKNOWN"

def get_moon_phase_polygon(illumination, phase_name):
    """
    Generates exact 2D polygon vertices for any phase percentage.
    """
    phase_upper = phase_name.upper()
    is_waxing = any(p in phase_upper for p in ["WAXING", "FIRST", "NEW"])

    # Number of points along the curve
    num_points = 100
    y = np.linspace(1, -1, num_points)
    
    # Scale illumination (0% -> -1.0, 50% -> 0.0, 100% -> +1.0)
    # k represents x-coordinate of the terminator at y=0
    k = (illumination / 50.0) - 1.0 
    
    # Outer edge boundary
    x_outer = np.sqrt(np.maximum(0, 1 - y**2))
    
    # Inner terminator boundary
    x_term = k * np.sqrt(np.maximum(0, 1 - y**2))

    if is_waxing:
        # Waxing: Lit area always fills the right edge (+x_outer)
        # Terminator (x_term) moves from -1 (New) to 0 (Quarter) to +1 (Full)
        x_coords = np.concatenate([x_outer, x_term[::-1]])
        y_coords = np.concatenate([y, y[::-1]])
    else:
        # Waning: Lit area always fills the left edge (-x_outer)
        # Terminator (-x_term) moves from +1 (Full) to 0 (Quarter) to -1 (New)
        x_coords = np.concatenate([-x_outer, (-x_term)[::-1]])
        y_coords = np.concatenate([y, y[::-1]])

    return np.column_stack([x_coords, y_coords])

# 2. Render plot
fig, ax = plt.subplots(figsize=(6, 6))

fig.patch.set_facecolor("#0b0d17")
ax.set_facecolor("#0b0d17")

# Dark background disk (unlit moon)
dark_moon = Circle((0, 0), 1, color="#2b2d38")
ax.add_patch(dark_moon)

# Draw lit portion
if illumination >= 99.5:
    # Full Moon (Solid Circle)
    full_moon = Circle((0, 0), 1, color="#fefcd7")
    ax.add_patch(full_moon)
elif illumination > 0.5:
    # Crescent / Quarter / Gibbous
    poly_verts = get_moon_phase_polygon(illumination, phase_name)
    moon_light = Polygon(poly_verts, color="#fefcd7", antialiased=True)
    ax.add_patch(moon_light)

# Aspect ratio and axis settings
ax.set_xlim(-1.5, 1.5)
ax.set_ylim(-1.5, 1.5)
ax.set_aspect("equal")
ax.axis("off")

# Labels
plt.title(
    f"Current Moon Phase\n{timestamp}",
    color="white",
    fontsize=14,
    pad=15,
    fontweight="bold"
)
ax.text(
    0,
    -1.3,
    f"Phase: {phase_name} ({illumination:.1f}%)",
    color="#fefcd7",
    fontsize=12,
    ha="center",
)

# Save image
output_file = "current_moon_phase.png"
plt.savefig(output_file, facecolor=fig.get_facecolor(), bbox_inches="tight", dpi=150)
plt.close(fig)

print(f"Saved: {output_file}")