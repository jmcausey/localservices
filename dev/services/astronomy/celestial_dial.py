import os
import sqlite3
import matplotlib.pyplot as plt
import numpy as np
from datetime import datetime

# --- 1. Fetch Astronomy Data ---
def fetch_latest_astronomy_data(db_path="~/local/data/flaskr.sqlite"):
    expanded_path = os.path.expanduser(db_path)
    conn = sqlite3.connect(expanded_path)
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()
    
    query = """
        SELECT sunrise, sunset, solar_noon, day_length, 
               sun_altitude, sun_azimuth, sun_distance,
               moon_phase, moonrise, moonset, moon_altitude, 
               moon_illumination_percentage, timestamp
        FROM astronomy 
        ORDER BY id DESC 
        LIMIT 1
    """
    cursor.execute(query)
    row = cursor.fetchone()
    conn.close()
    
    if not row:
        raise ValueError("No records found in the 'astronomy' table.")
    return dict(row)

def time_to_rad(time_str):
    if not time_str:
        return 0.0
    parts = time_str.split(':')
    return ((int(parts[0]) + int(parts[1]) / 60.0) / 24.0) * 2 * np.pi

# --- 2. Generate and Save Dial Chart ---
data = fetch_latest_astronomy_data()

sunrise_rad = time_to_rad(data['sunrise'])
sunset_rad = time_to_rad(data['sunset'])
solar_noon_rad = time_to_rad(data['solar_noon'])
moonrise_rad = time_to_rad(data['moonrise'])
moonset_rad = time_to_rad(data['moonset'])
sun_azimuth_rad = np.radians(data['sun_azimuth'])

fig, ax = plt.subplots(figsize=(9, 9), subplot_kw={'projection': 'polar'})
ax.set_theta_zero_location('N')
ax.set_theta_direction(-1)

r_inner, r_outer = 0.72, 1.0

# Arcs
theta_day = np.linspace(sunrise_rad, sunset_rad, 200)
ax.fill_between(theta_day, r_inner, r_outer, color='#FFA726', alpha=0.9, label=f"Daylight ({data['day_length']})")

theta_night = np.linspace(sunset_rad, sunrise_rad + 2*np.pi, 200)
ax.fill_between(theta_night, r_inner, r_outer, color='#1A237E', alpha=0.9, label='Night')

# Markers
ax.plot([solar_noon_rad, solar_noon_rad], [r_inner - 0.05, r_outer + 0.05], color='#E65100', lw=2.5, linestyle='--')
ax.plot(sunrise_rad, 0.86, 'o', color='#FFF176', markersize=10, markeredgecolor='#E65100')
ax.plot(sunset_rad, 0.86, 'o', color='#FF7043', markersize=10, markeredgecolor='#B71C1C')
ax.plot(moonrise_rad, 0.58, '^', color='#E0E0E0', markersize=9, markeredgecolor='#333333')
ax.plot(moonset_rad, 0.58, 'v', color='#9E9E9E', markersize=9, markeredgecolor='#333333')
ax.plot(sun_azimuth_rad, 1.1, '*', color='#FFD700', markersize=15, markeredgecolor='#FF6F00')

# Clock configuration
hours = np.arange(0, 24, 3)
ax.set_xticks((hours / 24.0) * 2 * np.pi)
ax.set_xticklabels([f'{h:02d}:00' for h in hours], fontsize=11, fontweight='bold')
ax.set_yticks([])
ax.set_ylim(0, 1.25)
ax.grid(True, linestyle='--', alpha=0.4, color='#757575')

summary_text = (
    "CELESTIAL DATA\n"
    "──────────────\n"
    f"Day Length: {data['day_length']}\n"
    f"Moon Phase: {data['moon_phase']}\n"
    f"Illumination: {data['moon_illumination_percentage']:.2f}%\n"
    f"Sun Altitude: {data['sun_altitude']:.2f}°\n"
    f"Sun Distance: {data['sun_distance'] / 1e6:.2f} M km\n"
    f"Moon Altitude: {data['moon_altitude']:.2f}°"
)
ax.text(0, 0, summary_text, ha='center', va='center', fontsize=9.5, fontweight='medium',
        bbox=dict(boxstyle='round,pad=0.7', facecolor='#FAFAFA', edgecolor='#B0BEC5', alpha=0.95))

plt.title("24-Hour Solar & Lunar Cycle Dial", fontsize=15, fontweight='bold', pad=25, color='#1A237E')
plt.legend(loc='upper right', bbox_to_anchor=(1.38, 1.08), fontsize=9, framealpha=0.9)
plt.tight_layout()

# Save Image
output_dir = os.path.expanduser("~/local/media/astronomy_graphs")
os.makedirs(output_dir, exist_ok=True)
filename = f"celestial_dial_{datetime.now().strftime('%Y%m%d_%H%M%S')}.png"
save_path = os.path.join(output_dir, filename)

plt.savefig(save_path, dpi=75, bbox_inches='tight')
plt.close()

# --- 3. Insert Post with BLOB Payload ---
def publish_to_flaskr_blob(image_name, db_path="~/local/data/flaskr.sqlite", author_id=1):
    expanded_path = os.path.expanduser(db_path)
    
    # HTML formatted image post
    web_image_path = f"/static/media/{image_name}"
    html_content = (
        f'<p><img src="{web_image_path}" alt="Celestial Dial" style="max-width:100%; height:auto;"></p>'
        f'<p>Automated daily astronomy visualization generated from system data.</p>'
    )
    
    # Convert string to UTF-8 binary bytes for BLOB insertion
    body_blob = html_content.encode('utf-8')
    title = f"Daily Celestial Dial: {datetime.now().strftime('%B %d, %Y')}"

    conn = sqlite3.connect(expanded_path)
    cursor = conn.cursor()
    
    cursor.execute(
        "INSERT INTO post (author_id, title, body) VALUES (?, ?, ?)",
        (author_id, title, body_blob)
    )
    conn.commit()
    conn.close()
    print("Successfully inserted BLOB post into Flaskr database!")

#publish_to_flaskr_blob(filename)
