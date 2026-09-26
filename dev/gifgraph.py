import glob
from PIL import Image

# Path pattern to your PNG files
path = "media/astronomy_graphs/celestial/*.png"

# Find and sort all matching PNG files
image_files = sorted(glob.glob(path))

if not image_files:
    print(f"No PNG files found in {path}")
else:
    # Open all frames
    frames = [Image.open(f) for f in image_files]

    # Save as animated GIF
    frames[0].save(
        "celestial_animation.gif",
        format="GIF",
        append_images=frames[1:],
        save_all=True,
        duration=300,  # Milliseconds per frame (100ms = 10 fps)
        loop=0,  # 0 means infinite loop
    )
    print("GIF saved successfully as celestial_animation.gif!")
