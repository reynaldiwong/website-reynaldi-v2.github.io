"""Generate the cobalt stipple duotone portrait (two density variants).

One-off generator, Pillow + numpy + scipy — NOT shipped as runtime JS.
Transparent background, dots in cobalt #1f4e8c, so it drops into the
porcelain frame instead of baking a background.

Run from repo root:  python tools/gen-stipple.py
Outputs _lowpoly/me-stipple-6500.svg and _lowpoly/me-stipple-4000.svg
"""
import os

import numpy as np
from PIL import Image
from scipy.spatial import cKDTree

SRC = "assets/img/me.jpg"
OUT = "_lowpoly"
W, H = 528, 704
COBALT = "#1f4e8c"
SEED = 5
MAX_R = 2.4         # hard radius cap
MIN_R = 0.35        # cull anything smaller
BUCKETS = 12


def load():
    img = Image.open(SRC).convert("L").resize((W, H))
    return np.array(img).astype(float) / 255.0   # luminance 0..1


def tone_curve(lum):
    """tone = 1 - lum, then gentle levels (black/white point + gamma) so
    skin midtones land as visible-but-not-solid dots, not a silhouette."""
    tone = 1.0 - lum
    lo, hi, gamma = 0.06, 0.94, 1.12
    return np.clip((tone - lo) / (hi - lo), 0.0, 1.0) ** gamma


def build(step, name, seed=SEED):
    tone = tone_curve(load())
    rng = np.random.default_rng(seed)
    jit = 0.4 * step                                # +-40% of the cell
    pts = []
    for y in range(0, H, step):
        for x in range(0, W, step):
            cy = min(H - 1, y + step // 2)
            cx = min(W - 1, x + step // 2)
            r = 2.2 * tone[cy, cx] ** 0.7
            if r < MIN_R:
                continue
            r = min(r, MAX_R)
            px = x + step / 2 + rng.uniform(-jit, jit)
            py = y + step / 2 + rng.uniform(-jit, jit)
            pts.append((px, py, r))

    bins = [[] for _ in range(BUCKETS)]
    radii = []
    for (x, y, r) in pts:
        bi = min(BUCKETS - 1, int(r / MAX_R * BUCKETS))
        bins[bi].append((int(round(x)), int(round(y))))
        radii.append(r)

    parts = [f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {W} {H}" '
             f'width="{W}" height="{H}">']
    for i, bucket in enumerate(bins):
        if not bucket:
            continue
        r = (i + 0.5) / BUCKETS * MAX_R
        bucket.sort(key=lambda p: (p[1], p[0]))
        px, py = bucket[0]
        seg = [f"M{px} {py}h0"]
        for x, y in bucket[1:]:
            seg.append(f"m{x - px} {y - py}h0")
            px, py = x, y
        parts.append(f'<path d="{"".join(seg)}" stroke="{COBALT}" '
                     f'stroke-width="{2 * r:.2f}" stroke-linecap="round" fill="none"/>')
    parts.append("</svg>")
    svg = "".join(parts)

    os.makedirs(OUT, exist_ok=True)
    path = f"{OUT}/{name}"
    with open(path, "w", encoding="utf-8") as f:
        f.write(svg)

    arr = np.array([(x, y) for b in bins for (x, y) in b], dtype=float)
    nn = cKDTree(arr).query(arr, k=2)[0][:, 1]
    radii = np.array(radii)
    print(f"{path}: {len(svg)} B = {len(svg) / 1024:.1f} KB, {len(pts)} dots")
    print(f"   radius: min {radii.min():.2f}  max {radii.max():.2f}  (cap {MAX_R})")
    print(f"   buckets({BUCKETS}): {[len(b) for b in bins]}")
    print(f"   NN spread: min {nn.min():.2f}  mean {nn.mean():.2f}  "
          f"max {nn.max():.2f}  std {nn.std():.2f}")


def main():
    build(7, "me-stipple-6500.svg")   # denser
    build(9, "me-stipple-4000.svg")   # sparser


if __name__ == "__main__":
    main()
