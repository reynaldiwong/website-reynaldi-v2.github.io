"""Dot-matrix portrait generator, ported from personal/rey-website DotProfile.tsx.

The reference is a <canvas> + requestAnimationFrame loop. This reproduces it as
a static SVG so the same look ships with zero runtime JS; every constant below
is the reference's, not an approximation:

    gap = 6, baseRadius = 2, brightness = (r+g+b)/3/255
    cull brightness <= 0.1
    size = brightness * baseRadius * (0.8 + 0.4 * wave)
    wave = sin(x*0.02 + y*0.02 - t) * 0.5 + 0.5,  t += 0.03 per frame

The canvas is 528x704 — the SOURCE's own ratio, so the cover-fit crops nothing.
Set --size to any WxH: whenever the canvas ratio differs from the image's, the
reference's cover-fit centres the overflow, and --crop skin shifts that band to
the skin-tone mass instead of the geometric centre.

`t` freezes one frame of the wave. t=0 is the reference's first frame; scan t to
see what the living version would do.

The source is me.webp, the cutout from tools/cutout.py, NOT me.jpg — its ALPHA
CHANNEL is the subject mask, so dots are painted only where the subject is and the
background stays a clean cobalt field. dotwave.js reads the same file and the same
threshold, so the static plate and the canvas cannot disagree about what is subject.
Use --no-mask to see the unmasked dots for comparison.

Run from repo root:
  python tools/gen-dots.py --out assets/img --name me-dots.svg --size 528x528 \
         --fill "#f4f7fb" --dot "#163a6b" --gap 8
"""
import argparse
import os

import numpy as np
from PIL import Image

SRC = "assets/img/me.webp"   # the cutout: RGB for brightness, ALPHA for the mask
FILL = "#f4f7fb"      # pale plate  (swapped with DOT at the user's request)
DOT = "#163a6b"       # cobalt dots (swapped with FILL)
GRID = 6              # gap
BASE_R = 2.0          # baseRadius
WAVE_K = 0.02         # x*0.02 + y*0.02
CULL = 0.1            # brightness <= 0.1 is dropped
ALPHA_MIN = 128       # keep in step with tools/cutout.py and dotwave.js
BUCKETS = 24          # radius quantisation (the reference is continuous)


def cover_brightness(img, w, h, top=None):
    """Reference cover-fit, then per-cell brightness on the grid and the subject mask.

    Returns (brightness, mask). Both are produced with the SAME cover-fit offsets, so
    a dot is only ever painted where the mask says subject at that exact coordinate.

    Scales the image to COVER the canvas and centres the overflow — the
    reference's own behaviour. With a canvas matching the source's ratio the
    offsets are both 0 and nothing is cropped. `top` overrides off_y when a
    different band of the source is wanted.
    """
    iw, ih = img.size
    img_aspect, canvas_aspect = iw / ih, w / h
    if img_aspect > canvas_aspect:
        render_h, render_w = h, h * img_aspect
        off_x, off_y = -(render_w - w) / 2, 0.0
    else:
        render_w, render_h = w, w / img_aspect
        off_x, off_y = 0.0, -(render_h - h) / 2
    if top is not None:
        off_y = -float(top)
    ox, oy = int(round(off_x)), int(round(off_y))

    canvas = Image.new("RGB", (w, h), (0, 0, 0))
    canvas.paste(img.convert("RGB"), (ox, oy))
    a = np.asarray(canvas).astype(float)

    if "A" in img.getbands():
        m = Image.new("L", (w, h), 0)
        m.paste(img.getchannel("A"), (ox, oy))
        mask = np.asarray(m) >= ALPHA_MIN
    else:
        mask = np.ones((h, w), dtype=bool)   # no alpha: nothing to mask
    return a.mean(axis=2) / 255.0, mask


def skin_top(img, h):
    """Alternative crop: centre the visible band on the skin-tone mass instead
    of the geometric centre, in case the cover-fit clips the face."""
    a = np.asarray(img).astype(float)
    r, g, b = a[..., 0], a[..., 1], a[..., 2]
    mx = np.maximum(r, np.maximum(g, b))
    mn = np.minimum(r, np.minimum(g, b))
    skin = ((r > 95) & (g > 40) & (b > 20) & (r > g) & (r > b) &
            ((mx - mn) > 15) & (np.abs(r - g) > 15))
    rows = skin.sum(axis=1)
    cy = (rows * np.arange(len(rows))).sum() / max(1.0, rows.sum())
    return int(round(min(max(cy - h / 2, 0), img.size[1] - h)))


def render(bright, mask, t):
    """One frozen frame as SVG, bucketed by radius so ~9k dots stay one path per
    bucket instead of 9k <circle> elements. A cell is painted only if the subject
    mask covers it, so the background stays a clean field."""
    h, w = bright.shape
    buckets = [[] for _ in range(BUCKETS)]
    coords_y, coords_x = np.arange(0, h, GRID), np.arange(0, w, GRID)
    for y in coords_y:
        for x in coords_x:
            if not mask[y, x]:
                continue
            b = bright[y, x]
            if b <= CULL:
                continue
            wave = np.sin(x * WAVE_K + y * WAVE_K - t) * 0.5 + 0.5
            size = b * BASE_R * (0.8 + 0.4 * wave)
            bi = min(BUCKETS - 1, int(size / (BASE_R * 1.2) * BUCKETS))
            buckets[bi].append((int(x), int(y)))

    parts = [f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {w} {h}" '
             f'width="{w}" height="{h}">',
             f'<rect width="{w}" height="{h}" fill="{FILL}"/>']
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
    global FILL, DOT, GRID
    ap = argparse.ArgumentParser()
    ap.add_argument("--out", default="_shots")
    ap.add_argument("--name", default="dotprofile.svg")
    ap.add_argument("--size", default="528x704", help="WxH canvas")
    ap.add_argument("--frame", type=float, default=0.0, help="wave phase t")
    ap.add_argument("--crop", choices=("centre", "skin"), default="centre")
    ap.add_argument("--fill", default=FILL, help="field colour (reference: #16181d)")
    ap.add_argument("--dot", default=DOT, help="dot colour")
    ap.add_argument("--gap", type=int, default=GRID, help="grid gap (reference: 6)")
    ap.add_argument("--no-mask", action="store_true",
                    help="ignore the subject mask (paint every cell; for comparison)")
    args = ap.parse_args()

    FILL, DOT, GRID = args.fill, args.dot, args.gap
    w, h = (int(v) for v in args.size.lower().split("x"))
    img = Image.open(SRC)
    top = skin_top(img.convert("RGB"), h) if args.crop == "skin" else None
    bright, mask = cover_brightness(img, w, h, top)
    if args.no_mask:
        mask = np.ones_like(mask)
    svg, dots = render(bright, mask, args.frame)
    os.makedirs(args.out, exist_ok=True)
    path = os.path.join(args.out, args.name)
    with open(path, "w", encoding="utf-8") as f:
        f.write(svg)
    grid_cells = len(range(0, h, GRID)) * len(range(0, w, GRID))
    print(f"{path}: {len(svg) / 1024:.1f} KB, {dots} dots, {w}x{h}, "
          f"grid {GRID}, t={args.frame}, crop {args.crop}, "
          f"field {FILL}, dots {DOT}"
          + (f" (band top {top})" if top is not None else " (no crop)"))
    print(f"  subject mask: {100 * mask.sum() / mask.size:.1f}% of the frame "
          f"({mask.sum()} of {mask.size} px), {grid_cells} grid cells, "
          f"alpha >= {ALPHA_MIN}"
          + ("  [MASK DISABLED]" if args.no_mask else ""))


if __name__ == "__main__":
    main()
