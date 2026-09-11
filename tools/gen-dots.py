"""Generate the dot-matrix portrait asset (assets/img/me-dots-*.svg).

One-off generator, Pillow only — NOT shipped as runtime JS. Reproduces the
old site's DotProfile language, recoloured: pale dots on a cobalt-deep field,
emitted as a bucketed tiny-SVG so ~5,800 dots don't become 260 KB of <circle>.

Run from repo root:  python tools/gen-dots.py
"""
import numpy as np
from PIL import Image

SRC = "assets/img/me.jpg"
W, H = 528, 704
FILL = "#0f2f57"   # cobalt-deep field (--field)
DOT = "#f4f7fb"    # pale dots (--on-cobalt)
MAX_R = 2.6        # max dot radius (px) at brightness 1.0
BUCKETS = 10


def generate(grid):
    img = Image.open(SRC).convert("RGB").resize((W, H))
    a = np.array(img).astype(float)
    bright = a.mean(axis=2) / 255.0  # per-pixel brightness 0..1

    buckets = [[] for _ in range(BUCKETS)]
    for y in range(grid // 2, H, grid):
        for x in range(grid // 2, W, grid):
            b = bright[y, x]
            if b <= 0.1:            # cull the dark (hair/shirt merge into cobalt)
                continue
            bi = min(BUCKETS - 1, int(b * BUCKETS))
            buckets[bi].append((x, y))

    parts = [
        f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {W} {H}" '
        f'width="{W}" height="{H}">',
        f'<rect width="{W}" height="{H}" fill="{FILL}"/>',
    ]
    for i, pts in enumerate(buckets):
        if not pts:
            continue
        r = (i + 0.5) / BUCKETS * MAX_R        # representative radius per bucket
        # Sort within the bucket and emit relative moves so the path stays compact
        # (absolute "M{x} {y}h0" per dot blows the size budget).
        pts = sorted(pts, key=lambda p: (p[1], p[0]))
        px, py = pts[0]
        seg = [f"M{px} {py}h0"]
        for x, y in pts[1:]:
            seg.append(f"m{x - px} {y - py}h0")
            px, py = x, y
        d = "".join(seg)
        parts.append(
            f'<path d="{d}" stroke="{DOT}" stroke-width="{2 * r:.2f}" '
            f'stroke-linecap="round"/>'
        )
    parts.append("</svg>")
    return "".join(parts), buckets


def main():
    for grid in (6, 8):
        svg, buckets = generate(grid)
        path = f"assets/img/me-dots-{grid}.svg"
        with open(path, "w", encoding="utf-8") as f:
            f.write(svg)
        n = sum(len(b) for b in buckets)
        hist = " ".join(f"{len(b)}" for b in buckets)
        sws = " ".join(f"{2 * ((i + 0.5) / BUCKETS * MAX_R):.2f}" for i in range(BUCKETS))
        print(f"{path}: {len(svg)} bytes = {len(svg) / 1024:.1f} KB, {n} dots, "
              f"grid {grid}px, {BUCKETS} buckets")
        print(f"   radius histogram (small->large): [{hist}]")
        print(f"   stroke-widths: [{sws}]")


if __name__ == "__main__":
    main()
