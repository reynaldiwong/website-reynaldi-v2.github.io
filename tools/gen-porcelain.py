"""Generate the underglaze-blue floral porcelain background.

One-off generator — not shipped as runtime JS. Cobalt ink only (#1f4e8c).
Ornament is foliage: sprigs (stem + alternating veined leaves) and trailing
vines, at the rim, with the centre column clear. Stroke widths vary
0.9-1.6px so it reads hand-painted rather than stamped.

Run from repo root:  python tools/gen-porcelain.py
Outputs assets/img/bg-porcelain.svg
        assets/img/bg-porcelain-rim.svg
"""
import math
import random

W, H = 1600, 1200
COBALT = "#1f4e8c"
SEED = 11
rng = random.Random(SEED)


def sw():
    """A hand-painted stroke width, 0.9-1.6px."""
    return rng.uniform(0.9, 1.6)


def leaf(bx, by, tx, ty, width, vein=True):
    """An elongated pointed-oval leaf (two arcs) with a thin centre vein."""
    mx, my = (bx + tx) / 2, (by + ty) / 2
    dx, dy = tx - bx, ty - by
    L = math.hypot(dx, dy) or 1.0
    px, py = -dy / L, dx / L
    c1x, c1y = mx + px * width, my + py * width
    c2x, c2y = mx - px * width, my - py * width
    shape = (f'M{bx:.1f} {by:.1f} Q{c1x:.1f} {c1y:.1f} {tx:.1f} {ty:.1f} '
             f'Q{c2x:.1f} {c2y:.1f} {bx:.1f} {by:.1f} Z')
    out = [f'<path d="{shape}" fill="{COBALT}" fill-opacity="0.05" '
           f'stroke-width="{sw():.2f}"/>']
    if vein:
        out.append(f'<path d="M{bx:.1f} {by:.1f} L{tx:.1f} {ty:.1f}" '
                   f'fill="none" stroke-width="0.5"/>')
    return "".join(out)


def sprig(cx, cy, angle, scale, n=6):
    """A short bowed stem with alternating veined leaves — a leaf sprig."""
    length = 175 * scale
    rad = math.radians(angle)
    ex = cx + math.cos(rad) * length
    ey = cy + math.sin(rad) * length
    nx, ny = -math.sin(rad), math.cos(rad)
    bow = 0.16 * length
    mx = (cx + ex) / 2 + nx * bow
    my = (cy + ey) / 2 + ny * bow
    parts = [f'<path d="M{cx:.1f} {cy:.1f} Q{mx:.1f} {my:.1f} {ex:.1f} {ey:.1f}" '
             f'fill="none" stroke="{COBALT}" stroke-opacity="0.12" '
             f'stroke-width="{sw():.2f}"/>']
    for i in range(n):
        t = 0.16 + 0.78 * i / max(1, n - 1)
        sx = (1 - t) ** 2 * cx + 2 * (1 - t) * t * mx + t * t * ex
        sy = (1 - t) ** 2 * cy + 2 * (1 - t) * t * my + t * t * ey
        side = -1 if i % 2 == 0 else 1
        lang = math.radians(angle + side * 56 - 12)
        llen = (56 - 5 * i) * scale
        tipx = sx + math.cos(lang) * llen
        tipy = sy + math.sin(lang) * llen
        parts.append(leaf(sx, sy, tipx, tipy, llen * 0.26))
    return "".join(parts)


def vine(d, leaves, stroke_op=0.12):
    """One curling cubic-bezier stem trailing leaves."""
    g = [f'<g fill="none" stroke="{COBALT}" stroke-opacity="{stroke_op}" stroke-width="1.2">',
         f'<path d="{d}"/>']
    for (bx, by, ang, L) in leaves:
        tipx = bx + math.cos(math.radians(ang)) * L
        tipy = by + math.sin(math.radians(ang)) * L
        g.append(leaf(bx, by, tipx, tipy, L * 0.26))
    g.append("</g>")
    return "".join(g)


def rim():
    """Thin double rule plus a repeating petal band near the outer edge."""
    g = [f'<g fill="none" stroke="{COBALT}" stroke-opacity="0.08">',
         f'<rect x="18" y="18" width="{W - 36}" height="{H - 36}" rx="26" stroke-width="1"/>',
         f'<rect x="30" y="30" width="{W - 60}" height="{H - 60}" rx="18" stroke-width="0.6"/>',
         "</g>",
         f'<g fill="none" stroke="{COBALT}" stroke-opacity="0.08" stroke-width="0.8">']
    for x in range(90, W - 60, 92):
        for y in (40, H - 40):
            g.append(f'<path d="M{x} {y} q14 -14 28 0 q-14 14 -28 0 Z"/>')
    g.append("</g>")
    return "".join(g)


def wrap(body):
    return (f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {W} {H}" '
            f'width="{W}" height="{H}">{body}</svg>')


def main():
    left_vine = vine(
        "M 34 130 C 210 330, -50 560, 118 742 S 40 1030, 168 1130",
        [(150, 290, 205, 66), (28, 470, 150, 58), (60, 620, 215, 62),
         (120, 800, 220, 66), (40, 940, 155, 58), (70, 1050, 150, 62)],
    )
    right_vine = vine(
        f"M {W - 26} 280 C {W - 210} 452, {W + 40} 640, {W - 150} 812 "
        f"S {W - 50} 1010, {W - 190} 1160",
        [(W - 150, 420, 330, 64), (W - 40, 560, 300, 58),
         (W - 30, 660, 300, 62), (W - 170, 900, 340, 66),
         (W - 90, 1030, 320, 58)],
    )
    upper_branch = vine(
        "M 250 330 C 600 235, 980 305, 1345 220",
        [(470, 258, 250, 54), (700, 266, 246, 56),
         (960, 278, 242, 52), (1185, 240, 240, 54)],
    )
    lower_branch = vine(
        "M 260 935 C 620 1010, 980 895, 1335 980",
        [(490, 970, 66, 54), (720, 966, 66, 56),
         (965, 938, 66, 52), (1185, 988, 66, 54)],
    )
    body = (
        sprig(1430, 210, -150, 1.35, 6) +    # upper right
        sprig(180, 1080, -28, 1.2, 6) +      # lower left
        sprig(1520, 620, 168, 0.95, 5) +     # right edge
        upper_branch + lower_branch +        # long branches through the middle
        left_vine + right_vine
    )
    svg = wrap(body)
    rim_svg = wrap(rim())
    for path, content in (("assets/img/bg-porcelain.svg", svg),
                          ("assets/img/bg-porcelain-rim.svg", rim_svg)):
        with open(path, "w", encoding="utf-8") as f:
            f.write(content)
        print(f"{path}: {len(content)} bytes = {len(content) / 1024:.1f} KB")


if __name__ == "__main__":
    main()
