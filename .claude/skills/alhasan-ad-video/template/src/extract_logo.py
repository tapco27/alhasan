# Isolates the gold mark from the supplied logo image as a transparent PNG (original gold pixels kept).
import sys
import numpy as np
from PIL import Image, ImageFilter

src, out_png = sys.argv[1], sys.argv[2]

# Crop to the logo area (gold mark only, tagline is typeset separately)
im = Image.open(src).convert("RGB")
crop = im.crop((440, 440, 1010, 930))

# Upscale first so the matte edge is computed at output resolution
S = 3
big = crop.resize((crop.width * S, crop.height * S), Image.LANCZOS)
a = np.asarray(big).astype(np.float32)
r, g, b = a[..., 0], a[..., 1], a[..., 2]

# Gold key: red-over-blue difference separates gold from the grey-blue backdrop
k = np.clip((r - b - 38) / 50, 0, 1)
alpha = k * k * (3 - 2 * k)

# Drop isolated specks (anything not near a solid gold area)
solid = Image.fromarray(((alpha > 0.85) * 255).astype(np.uint8)).filter(ImageFilter.MaxFilter(9)).filter(ImageFilter.GaussianBlur(3))
alpha *= np.clip(np.asarray(solid).astype(np.float32) / 90, 0, 1)

# Keep original colour, lifted slightly at the edges where the backdrop bled in
rgb = a.copy()
edge = (alpha < 0.98)[..., None]
rgb = np.where(edge, np.clip(rgb * 1.08 + 6, 0, 255), rgb)
out = np.dstack([rgb, alpha * 255]).astype(np.uint8)
img = Image.fromarray(out, "RGBA")

# Trim to content
bbox = Image.fromarray((alpha * 255).astype(np.uint8)).point(lambda v: 255 if v > 20 else 0).getbbox()
pad = 18
bbox = (max(bbox[0] - pad, 0), max(bbox[1] - pad, 0), min(bbox[2] + pad, img.width), min(bbox[3] + pad, img.height))
img = img.crop(bbox)
img.save(out_png)
print("logo", img.size)
