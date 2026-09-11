"""Generate the dot-matrix portrait asset (square, 1:1).

Recovered from d410fc5 (tools/gen-dots.py, deleted in dc6faeb) and re-scoped for
the square hero frame: the source is cropped to 1:1 around the band carrying the
most edge energy — on a portrait that is the face — then rendered as pale dots
on the cobalt-deep field, bucketed by brightness so ~5k dots stay a small SVG.

One-off generator, Pillow only — NOT shipped as runtime JS.

Run from repo root:  python tools/gen-dots.py [--out DIR] [--grid N] [--name F]
"""
import argparse
import os

import numpy as np
from PIL import Image
from scipy.ndimage import gaussian_filter

SRC = "assets/img/me.jpg"
FILL = "#0f2f57"   # cobalt-deep field (--field)
DOT = "#f4f7fb"    # pale dots (--on-cobalt)
MAX_R = 2.6        # max dot radius (px) at brightness 1.0
BUCKETS = 10


def pick_square(img):
    """Vertical offset for the 1:1 crop, from the skin-tone centroid.

    A square crop of a 3:4 portrait discards 176px of height and the choice
    decides whether the frame keeps the face. Edge energy does NOT discriminate
    here (background detail swamps it — every candidate scored 0.6%), so this
    uses a standard RGB skin heuristic and centres the window on that mass."""
    a = np.array(img).astype(float)
    r, g, b = a[..., 0], a[..., 1], a[..., 2]
    mx = np.maximum(r, np.maximum(g, b))
    mn = np.minimum(r, np.minimum(g, b))
    skin = ((r > 95) & (g > 40) & (b > 20) & (r > g) & (r > b) &
            ((mx - mn) > 15) & (np.abs(r - g) > 15))
    h, w = skin.shape
    side = w
    rows = skin.sum(axis=1)
    cy = (rows * np.arange(len(rows))).sum() / max(1.0, rows.sum())
    top = int(round(min(max(cy - side / 2, 0), h - side)))
    return top, side, skin.mean()


def generate(grid, out, name):
    img = Image.open(SRC).convert("RGB")
    top, side, skin_share = pick_square(img)
    box = (0, top, side, top + side)
    img = img.crop(box)
    a = np.array(img).astype(float)
    bright = a.mean(axis=2) / 255.0
    h, w = bright.shape

    buckets = [[] for _ in range(BUCKETS)]
    for y in range(grid // 2, h, grid):
        for x in range(grid // 2, w, grid):
            b = bright[y, x]
            if b <= 0.1:            # cull the dark (hair/shirt merge into cobalt)
                continue
            buckets[min(BUCKETS - 1, int(b * BUCKETS))].append((x, y))

    parts = [
        f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {w} {h}" '
        f'width="{w}" height="{h}">',
        f'<rect width="{w}" height="{h}" fill="{FILL}"/>',
    ]
    for i, pts in enumerate(buckets):
        if not pts:
            continue
        r = (i + 0.5) / BUCKETS * MAX_R
        pts = sorted(pts, key=lambda p: (p[1], p[0]))
        px, py = pts[0]
        seg = [f"M{px} {py}h0"]
        for x, y in pts[1:]:
            seg.append(f"m{x - px} {y - py}h0")
            px, py = x, y
        parts.append(f'<path d="{"".join(seg)}" stroke="{DOT}" '
                     f'stroke-width="{2 * r:.2f}" stroke-linecap="round"/>')
    parts.append("</svg>")
    svg = "".join(parts)
    path = os.path.join(out, name)
    os.makedirs(out, exist_ok=True)
    with open(path, "w", encoding="utf-8") as f:
        f.write(svg)
    n = sum(len(b) for b in buckets)
    print(f"{path}: {len(svg) / 1024:.1f} KB, {n} dots, grid {grid}px, "
          f"aspect 1:1 ({w}x{h}), crop box {box} (skin mass {skin_share * 100:.1f}%), "
          f"{FILL} field / {DOT} dots")
    return dict(path=path, dots=n, kb=len(svg) / 1024, box=box, grid=grid, side=side)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--out", default="assets/img")
    ap.add_argument("--grid", type=int, default=8)
    ap.add_argument("--name", default=None)
    args = ap.parse_args()
    name = args.name or f"me-dots-{args.grid}-square.svg"
    generate(args.grid, args.out, name)


if __name__ == "__main__":
    main()
