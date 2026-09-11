"""Generate the cobalt stipple duotone portrait (two density variants).

One-off generator, Pillow + numpy + scipy — NOT shipped as runtime JS.
Transparent background, dots in cobalt #1f4e8c, so it drops into the
porcelain frame instead of baking a background.

Run from repo root:  python tools/gen-stipple.py
Outputs _lowpoly/me-stipple-6500.svg and _lowpoly/me-stipple-4000.svg
"""
import math
import os

import numpy as np
from PIL import Image
from scipy.spatial import cKDTree, Delaunay

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


def build(step, name, out=OUT, seed=SEED):
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

    os.makedirs(out, exist_ok=True)
    path = f"{out}/{name}"
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


def build_lines(step, name, out=OUT, seed=SEED, max_edge=17.5, levels=7):
    """Delaunay wireframe: tone-weighted points, edges drawn as thin cobalt
    lines with opacity modulated by local tone (dense/bright in shadow,
    sparse/faint over light skin). Cull long edges; dot each vertex."""
    tone = tone_curve(load())
    rng = np.random.default_rng(seed)
    jit = 0.4 * step
    pts, tones = [], []
    for y in range(0, H, step):
        for x in range(0, W, step):
            cy = min(H - 1, y + step // 2)
            cx = min(W - 1, x + step // 2)
            t = tone[cy, cx]
            if 2.2 * t ** 0.7 < MIN_R:
                continue
            pts.append((x + step / 2 + rng.uniform(-jit, jit),
                        y + step / 2 + rng.uniform(-jit, jit)))
            tones.append(t)
    pts = np.array(pts)
    tones = np.array(tones)
    tri = Delaunay(pts)

    edges = set()
    for s in tri.simplices:
        for i in range(3):
            a, b = int(s[i]), int(s[(i + 1) % 3])
            edges.add((a, b) if a < b else (b, a))

    buckets = [[] for _ in range(levels)]
    kept = 0
    for (a, b) in edges:
        x1, y1 = pts[a]
        x2, y2 = pts[b]
        if math.hypot(x2 - x1, y2 - y1) > max_edge:
            continue
        op = 0.12 + 0.43 * (tones[a] + tones[b]) / 2
        li = min(levels - 1, int((op - 0.12) / 0.43 * levels))
        buckets[li].append((x1, y1, x2, y2))
        kept += 1

    parts = [f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {W} {H}" '
             f'width="{W}" height="{H}">']
    for i, b in enumerate(buckets):
        if not b:
            continue
        op = 0.12 + (i + 0.5) / levels * 0.43
        d = []
        px = py = 0
        for x1, y1, x2, y2 in sorted(b):
            ix1, iy1 = int(round(x1)), int(round(y1))
            ix2, iy2 = int(round(x2)), int(round(y2))
            d.append(f"m{ix1 - px} {iy1 - py}l{ix2 - ix1} {iy2 - iy1}")
            px, py = ix2, iy2
        parts.append(f'<path d="{"".join(d)}" stroke="{COBALT}" stroke-width="0.6" '
                     f'stroke-opacity="{op:.2f}" fill="none"/>')
    # vertex dots (relative moves — keeps them compact)
    vx, vy = int(round(pts[0][0])), int(round(pts[0][1]))
    seg = [f"M{vx} {vy}h0"]
    for (px, py) in pts[1:]:
        rx, ry = int(round(px)), int(round(py))
        seg.append(f"m{rx - vx} {ry - vy}h0")
        vx, vy = rx, ry
    parts.append(f'<path d="{"".join(seg)}" stroke="{COBALT}" stroke-width="1.6" '
                 f'stroke-linecap="round" fill="none"/>')
    parts.append("</svg>")
    svg = "".join(parts)

    os.makedirs(out, exist_ok=True)
    path = f"{out}/{name}"
    with open(path, "w", encoding="utf-8") as f:
        f.write(svg)
    print(f"{path}: {len(svg)} B = {len(svg) / 1024:.1f} KB, "
          f"{len(pts)} nodes, {kept} edges kept of {len(edges)}")


def main():
    build(9, "me-stipple.svg", out="assets/img")    # hero: ~4.5k dots (frozen)
    build(7, "me-stipple-6500.svg")                 # reference densities
    build(11, "me-stipple-3000.svg")
    build_lines(15, "me-lines.svg", out="assets/img")   # hero line variant
    build_lines(12, "me-lines-2500.svg")


if __name__ == "__main__":
    main()
