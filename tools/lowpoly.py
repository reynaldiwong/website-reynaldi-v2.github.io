"""Generate the 3D low-poly portrait variants.

Pipeline: Sobel edge magnitude -> face/edge-weighted point sampling ->
Delaunay triangulation -> flat-fill each facet with its mean colour ->
directional shading (light-vector dot gradient, ~±8%) -> 1px separator.

Run from repo root:  python tools/lowpoly.py
Outputs into _lowpoly/ for the user to pick from (B1 natural / B2 palette-locked).
"""
import os
import numpy as np
from PIL import Image, ImageDraw
from scipy.spatial import Delaunay
from scipy.ndimage import sobel, gaussian_filter

SRC = "assets/img/me.jpg"
OUT = "_lowpoly"
FACET_COUNTS = [450, 800, 1400]
SEED = 42

# B2 palette (light -> dark) — porcelain + cobalt ramp.
PALETTE = [
    (247, 246, 242),  # porcelain
    (220, 231, 244),  # cobalt-soft
    (169, 194, 224),
    (123, 145, 184),
    (83, 109, 158),
    (31, 78, 140),    # cobalt
    (22, 58, 107),    # cobalt-deep
    (15, 47, 87),     # field
]


def rgb_to_hex(c):
    r, g, b = (int(np.clip(v, 0, 255)) for v in c)
    return f"#{r:02x}{g:02x}{b:02x}"


def sobel_fields(img):
    gray = 0.299 * img[:, :, 0] + 0.587 * img[:, :, 1] + 0.114 * img[:, :, 2]
    gx = sobel(gray, axis=1)
    gy = sobel(gray, axis=0)
    mag = np.hypot(gx, gy)
    return gray, gx, gy, mag


def sample_points(h, w, n, mag, rng):
    pts = [(0, 0), (w - 1, 0), (0, h - 1), (w - 1, h - 1),
           (w // 2, 0), (w // 2, h - 1), (0, h // 2), (w - 1, h // 2)]
    # Face gaussian (denser across the face, assumed upper-centre).
    yy, xx = np.mgrid[0:h, 0:w]
    face = np.exp(-(((xx - w * 0.5) / (w * 0.24)) ** 2 +
                    ((yy - h * 0.42) / (h * 0.26)) ** 2))
    # Edge-weighted + face-weighted probability field.
    prob = mag / (mag.max() + 1e-6) + 1.6 * face + 0.15
    prob = prob ** 1.4
    prob /= prob.sum()
    flat = prob.flatten()
    idx = rng.choice(h * w, size=n, replace=False, p=flat)
    pts += [(int(i % w), int(i // w)) for i in idx]
    return np.array(pts)


def facet_stats(img, tri_pts, gx, gy, w, h):
    xs = [p[0] for p in tri_pts]
    ys = [p[1] for p in tri_pts]
    x0, x1 = int(min(xs)), int(max(xs))
    y0, y1 = int(min(ys)), int(max(ys))
    mask = Image.new("L", (max(1, x1 - x0 + 1), max(1, y1 - y0 + 1)), 0)
    d = ImageDraw.Draw(mask)
    d.polygon([(x - x0, y - y0) for x, y in tri_pts], fill=255)
    m = np.array(mask) > 0
    region = img[y0:y1 + 1, x0:x1 + 1][m]
    if region.size == 0:
        return np.array([255.0, 255.0, 255.0]), (0.0, 0.0)
    mean = region.mean(axis=0)
    cx, cy = int(np.mean(xs)), int(np.mean(ys))
    cx = min(w - 1, max(0, cx))
    cy = min(h - 1, max(0, cy))
    grad = (gx[cy, cx], gy[cy, cx])
    return mean, grad


def lowpoly(img, gx, gy, mag, n_points, palette=None, shade=0.08, sep=0.15):
    h, w = img.shape[:2]
    rng = np.random.default_rng(SEED)
    pts = sample_points(h, w, n_points, mag, rng)
    tri = Delaunay(pts)
    out = Image.new("RGB", (w, h), (255, 255, 255))
    draw = ImageDraw.Draw(out)
    light = np.array([-0.5, -0.5])
    light = light / (np.linalg.norm(light) + 1e-6)

    for s in tri.simplices:
        tri_pts = [(int(x), int(y)) for x, y in pts[s]]
        mean, grad = facet_stats(img, tri_pts, gx, gy, w, h)
        if palette is not None:
            lum = 0.299 * mean[0] + 0.587 * mean[1] + 0.114 * mean[2]
            # map luminance (0..255) into palette index
            t = np.clip(lum / 255.0, 0.0, 1.0)
            idx = int(t * (len(palette) - 1) + rng.uniform(-0.4, 0.4))
            idx = max(0, min(len(palette) - 1, idx))
            color = np.array(palette[idx], dtype=float)
        else:
            color = mean
        # Directional shading from local gradient.
        gn = np.linalg.norm(grad) + 1e-6
        d = np.dot(np.array(grad) / gn, light)
        color = color * (1.0 + d * shade)
        fill = rgb_to_hex(color)
        # 1px separator at `sep` opacity: draw a slightly darker outline.
        sep_rgb = tuple(int(v * (1 - sep)) for v in color)
        draw.polygon(tri_pts, fill=fill, outline=sep_rgb)
    return out


def save_pair(img, base):
    img.save(f"{base}.png")
    img.save(f"{base}.webp", "WEBP", quality=88, method=6)
    return f"{base}.webp"


def main():
    os.makedirs(OUT, exist_ok=True)
    src = Image.open(SRC).convert("RGB")
    base = np.array(src).astype(np.float64)
    gray, gx, gy, mag = sobel_fields(base)
    h, w = base.shape[:2]

    for n in FACET_COUNTS:
        for variant, palette in [("b1", None), ("b2", PALETTE)]:
            img = lowpoly(base, gx, gy, mag, n, palette=palette)
            # 2x retina upscale
            img2x = img.resize((w * 2, h * 2), Image.LANCZOS)
            p = save_pair(img, f"{OUT}/lowpoly-{variant}-{n}")
            img2x.save(f"{OUT}/lowpoly-{variant}-{n}@2x.webp", "WEBP", quality=88, method=6)
            img2x.save(f"{OUT}/lowpoly-{variant}-{n}@2x.png")
            kb = os.path.getsize(p) / 1024
            print(f"{variant} n={n}: {p} ({kb:.1f} KB)")


if __name__ == "__main__":
    main()
