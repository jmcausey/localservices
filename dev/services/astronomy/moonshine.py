import os
import sqlite3
import numpy as np
import matplotlib.pyplot as plt
from matplotlib.patches import Polygon, Circle
from PIL import Image

# 1. Fetch data from SQLite
conn = sqlite3.connect("data/flaskr.sqlite")
cursor = conn.cursor()

query = """
    SELECT timestamp, moon_illumination_percentage, moon_phase 
    FROM astronomy 
    ORDER BY timestamp ASC
"""
cursor.execute(query)
rows = cursor.fetchall()
conn.close()

frames_dir = "temp_frames"
os.makedirs(frames_dir, exist_ok=True)
frame_paths = []

# Helper function to generate shape points for moon phases
def get_moon_phase_polygon(illumination, phase_name):
    """
    Generates a 2D polygon representing the illuminated portion of the moon.
    """
    phase_upper = phase_name.upper() if phase_name else ""
    is_waxing = "WAXING" in phase_upper or "FIRST" in phase_upper or "NEW" in phase_upper
    
    # Transform illumination (0-100) to fraction (-1 to 1) for the terminator curve
    # 0% = -1 (New), 50% = 0 (Quarter), 100% = +1 (Full)
    k = (illumination / 50.0) - 1.0 
    
    # Generate right-side arc (limb)
    y_limb = np.linspace(-1, 1, 100)
    x_limb = np.sqrt(1 - y_limb**2) if is_waxing else -np.sqrt(1 - y_limb**2)
    
    # Generate terminator curve
    y_term = np.linspace(1, -1, 100)
    x_term = k * np.sqrt(1 - y_term**2) if is_waxing else -k * np.sqrt(1 - y_term**2)
    
    # Combine into a continuous loop path
    x_coords = np.concatenate([x_limb, x_term])
    y_coords = np.concatenate([y_limb, y_term])
    
    return np.column_stack([x_coords, y_coords])

# 2. Render frames
for idx, (timestamp, illumination, phase_name) in enumerate(rows):
    illumination = illumination if illumination is not None else 0.0
    phase_name = phase_name if phase_name else "UNKNOWN"

    fig, ax = plt.subplots(figsize=(6, 6))
    fig.patch.set_facecolor("#0b0d17")
    ax.set_facecolor("#0b0d17")

    # Base dark moon disk
    dark_moon = Circle((0, 0), 1, color="#2b2d38")
    ax.add_patch(dark_moon)

    # Illuminated shape rendering
    if illumination > 0.5:
        poly_verts = get_moon_phase_polygon(illumination, phase_name)
        moon_light = Polygon(poly_verts, color="#fefcd7", antialiased=True)
        ax.add_patch(moon_light)

    # Frame bounds & layout
    ax.set_xlim(-1.5, 1.5)
    ax.set_ylim(-1.5, 1.5)
    ax.set_aspect("equal")
    ax.axis("off")

    plt.title(
        f"Time: {timestamp}\nPhase: {phase_name}",
        color="white",
        fontsize=12,
        pad=15,
    )
    ax.text(
        0,
        -1.3,
        f"Illumination: {illumination:.1f}%",
        color="#fefcd7",
        fontsize=12,
        ha="center",
    )

    frame_path = os.path.join(frames_dir, f"frame_{idx:04d}.png")
    plt.savefig(
        frame_path, facecolor=fig.get_facecolor(), bbox_inches="tight", dpi=100
    )
    plt.close(fig)
    frame_paths.append(frame_path)

# 3. Create GIF
images = [Image.open(p) for p in frame_paths]
output_gif = "moon_illumination.gif"
images[0].save(
    output_gif,
    format="GIF",
    append_images=images[1:],
    save_all=True,
    duration=150,
    loop=0,
)

# Cleanup
for p in frame_paths:
    os.remove(p)
os.rmdir(frames_dir)

print(f"GIF rendered with accurate moon phases: '{output_gif}'")