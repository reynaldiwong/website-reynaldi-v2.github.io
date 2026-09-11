"""Dot-matrix portrait generator, ported from personal/rey-website DotProfile.tsx.

The reference is a <canvas> + requestAnimationFrame loop. This reproduces it as
a static SVG so the same look ships with zero runtime JS; every constant below
is the reference's, not an approximation:

    gap = 6, baseRadius = 2, brightness = (r+g+b)/3/255
    cull brightness <= 0.1
    size = brightness * baseRadius * (0.8 + 0.4 * wave)
    wave = sin(x*0.02 + y*0.02 - t) * 0.5 + 0.5,  t += 0.03 per frame

Two deliberate deviations, both required by this site:
  * the canvas is 1:1 here (the reference is 432x576 = 3:4) because the hero
    frame was asked to be square;
  * the palette is #f4f7fb dots on #0f2f57 (the reference draws #ffffffff on
    #16181D) so the portrait belongs to the porcelain palette.

`t` freezes one frame of the wave. t=0 is the reference's first frame; scan t to
see what the living version would do.

Run from repo root:  python tools/gen-dots.py --out DIR --name F [--frame 0] [--crop centre|skin]
"""
import argparse
import os

import numpy as np
from PIL import Image

SRC = "assets/img/me.jpg"
FILL = "#0f2f57"      # cobalt-deep field (--field)
DOT = "#f4f7fb"       # pale dots (--on-cobalt)
GRID = 6              # gap
BASE_R = 2.0          # baseRadius
WAVE_K = 0.02         # x*0.02 + y*0.02
CULL = 0.1            # brightness <= 0.1 is dropped
BUCKETS = 24          # radius quantisation (the reference is continuous)


def cover_brightness(img, side, top=None):
    """Reference cover-fit, then per-cell brightness on the grid.

    The reference scales the image to COVER a 3:4 canvas and centres the
    overflow. For a square canvas that means the 3:4 source loses 2*side/8 px of
    height, centred — `top` overrides that if a different band is wanted."""
    w, h = img.size
    img_aspect, canvas_aspect = w / h, 1.0
    if img_aspect > canvas_aspect:
        render_h, render_w = side, side * img_aspect
        off_x, off_y = -(render_w - side) / 2, 0.0
    else:
        render_w, render_h = side, side / img_aspect
        off_x, off_y = 0.0, -(render_h - side) / 2
    if top is not None:
        off_y = -float(top)
    canvas = Image.new("RGB", (side, side), (0, 0, 0))
    canvas.paste(img, (int(round(off_x)), int(round(off_y))))
    a = np.asarray(canvas).astype(float)
    return a.mean(axis=2) / 255.0


def skin_top(img, side):
    """Alternative crop: centre the square on the skin-tone mass instead of the
    geometric centre, in case the cover-fit clips the face."""
    a = np.asarray(img).astype(float)
    r, g, b = a[..., 0], a[..., 1], a[..., 2]
    mx = np.maximum(r, np.maximum(g, b))
    mn = np.minimum(r, np.minimum(g, b))
    skin = ((r > 95) & (g > 40) & (b > 20) & (r > g) & (r > b) &
            ((mx - mn) > 15) & (np.abs(r - g) > 15))
    rows = skin.sum(axis=1)
    cy = (rows * np.arange(len(rows))).sum() / max(1.0, rows.sum())
    h = img.size[1]
    return int(round(min(max(cy - side / 2, 0), h - side)))


def render(bright, t):
    """One frozen frame as SVG, bucketed by radius so 7k dots stay one path per
    bucket instead of 7k <circle> elements."""
    side = bright.shape[0]
    buckets = [[] for _ in range(BUCKETS)]
    coords = np.arange(0, side, GRID)          # reference starts at 0, not gap/2
    for y in coords:
        for x in coords:
            b = bright[y, x]
            if b <= CULL:
                continue
            wave = np.sin(x * WAVE_K + y * WAVE_K - t) * 0.5 + 0.5
            size = b * BASE_R * (0.8 + 0.4 * wave)
            bi = min(BUCKETS - 1, int(size / (BASE_R * 1.2) * BUCKETS))
            buckets[bi].append((int(x), int(y)))

    parts = [f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {side} {side}" '
             f'width="{side}" height="{side}">',
             f'<rect width="{side}" height="{side}" fill="{FILL}"/>']
    for i, pts in enumerate(buckets):
        if not pts:
            continue
        size = (i + 0.5) / BUCKETS * BASE_R * 1.2     # representative radius
        pts = sorted(pts, key=lambda p: (p[1], p[0]))
        px, py = pts[0]
        seg = [f"M{px} {py}h0"]
        for x, y in pts[1:]:
            seg.append(f"m{x - px} {y - py}h0")
            px, py = x, y
        parts.append(f'<path d="{"".join(seg)}" stroke="{DOT}" '
                     f'stroke-width="{2 * size:.2f}" stroke-linecap="round"/>')
    parts.append("</svg>")
    return "".join(parts), sum(len(b) for b in buckets)


def main():
    global FILL, DOT
    ap = argparse.ArgumentParser()
    ap.add_argument("--out", default="_shots")
    ap.add_argument("--name", default="dotprofile-square.svg")
    ap.add_argument("--side", type=int, default=528)
    ap.add_argument("--frame", type=float, default=0.0, help="wave phase t")
    ap.add_argument("--crop", choices=("centre", "skin"), default="centre")
    ap.add_argument("--fill", default=FILL, help="field colour (the reference's own is #16181d)")
    ap.add_argument("--dot", default=DOT, help="dot colour")
    args = ap.parse_args()

    FILL, DOT = args.fill, args.dot
    img = Image.open(SRC).convert("RGB")
    top = skin_top(img, args.side) if args.crop == "skin" else None
    bright = cover_brightness(img, args.side, top)
    svg, dots = render(bright, args.frame)
    os.makedirs(args.out, exist_ok=True)
    path = os.path.join(args.out, args.name)
    with open(path, "w", encoding="utf-8") as f:
        f.write(svg)
    print(f"{path}: {len(svg) / 1024:.1f} KB, {dots} dots, side {args.side}, "
          f"grid {GRID}, frame t={args.frame}, crop {args.crop}"
          + (f" (top {top})" if top is not None else ""))


if __name__ == "__main__":
    main()
