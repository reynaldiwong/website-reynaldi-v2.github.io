"""Generate the faceted cobalt background mesh (assets/img/bg-mesh.svg).

One-off generator — NOT shipped, NOT wired into the page. Stdlib only.
Jittered triangular grid, fixed seed so the asset is reproducible.
Run from repo root:  python tools/gen-mesh.py
"""
import math
import random

W, H = 1600, 1200
COLS, ROWS = 14, 10
SEED = 7

# Cobalt ramp: pale zones -> deep zones.
RAMP = ["#eef2f6", "#dce7f4", "#cbe0f9", "#a9c2e0",
        "#7b91b8", "#4c659b", "#1f4e8c", "#0f2f57"]


def radius(x, y):
    dx = (x - W / 2) / (W / 2)
    dy = (y - H / 2) / (H / 2)
    return math.hypot(dx, dy)


def main():
    rng = random.Random(SEED)
    cw, ch = W / COLS, H / ROWS
    verts = {}
    for r in range(ROWS + 1):
        for c in range(COLS + 1):
            x, y = c * cw, r * ch
            rad = radius(x, y)
            # more jitter toward the periphery -> larger, more irregular facets
            amp = 0.44 * min(cw, ch) * (0.45 + 0.85 * rad)
            jx = 0.0 if c in (0, COLS) else rng.uniform(-amp, amp)
            jy = 0.0 if r in (0, ROWS) else rng.uniform(-amp, amp)
            verts[(r, c)] = (x + jx, y + jy)

    tris = []
    for r in range(ROWS):
        for c in range(COLS):
            a, b = verts[(r, c)], verts[(r, c + 1)]
            d, e = verts[(r + 1, c)], verts[(r + 1, c + 1)]
            tris.append((a, b, d))
            tris.append((b, e, d))

    parts = [f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {W} {H}" '
             f'width="{W}" height="{H}">']
    facets = 0
    for t in tris:
        cx = sum(p[0] for p in t) / 3.0
        cy = sum(p[1] for p in t) / 3.0
        rad = radius(cx, cy)
        if rad < 0.34:            # central content column fades to nothing
            continue
        u = (rad - 0.34) / (1.15 - 0.34)
        u = max(0.0, min(1.0, u)) + rng.uniform(-0.18, 0.18)
        u = max(0.0, min(1.0, u))
        idx = min(len(RAMP) - 1, int(u * (len(RAMP) - 1) + 0.5))
        pts = " ".join(f"{px:.0f},{py:.0f}" for px, py in t)
        parts.append(f'<polygon points="{pts}" fill="{RAMP[idx]}"/>')
        facets += 1
    parts.append("</svg>")
    svg = "".join(parts)

    with open("assets/img/bg-mesh.svg", "w", encoding="utf-8") as f:
        f.write(svg)
    kb = len(svg) / 1024
    print(f"wrote assets/img/bg-mesh.svg ({len(svg)} bytes = {kb:.1f} KB, {facets} facets)")


if __name__ == "__main__":
    main()
