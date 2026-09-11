"""Generate the underglaze-blue floral porcelain background.

One-off generator — not shipped as runtime JS. Cobalt ink only (#1f4e8c).

The ornament is ONE connected plant: a serpentine main stem entering and leaving
off-canvas, with a lower stem, two rim stems and three side-shoots all rooted on
it at computed points. Nothing floats — every path starts on another path, so
there are no dangling ends. All stems are cubic-bezier chains with real control
points (no straight runs); leaves are rooted on the sampled stem polyline and
turned to its local tangent, so they visibly attach.

Run from repo root:  python tools/gen-porcelain.py
Outputs assets/img/bg-porcelain.svg
        assets/img/bg-porcelain-rim.svg
"""
import math
import random

W, H = 1600, 1200
COBALT = "#1f4e8c"
LINE_OP = 0.17          # line-work opacity
FILL_OP = 0.08          # leaf fill opacity
SEED = 11
rng = random.Random(SEED)


def sw():
    """A hand-painted stroke width, 0.9-1.6px."""
    return rng.uniform(0.9, 1.6)


def bez(p0, p1, p2, p3, t):
    """Point on a cubic bezier at parameter t."""
    mt = 1 - t
    return (mt ** 3 * p0[0] + 3 * mt * mt * t * p1[0] + 3 * mt * t * t * p2[0] + t ** 3 * p3[0],
            mt ** 3 * p0[1] + 3 * mt * mt * t * p1[1] + 3 * mt * t * t * p2[1] + t ** 3 * p3[1])


def chain(segs, per=26):
    """Sample a chain of cubic segments into a polyline."""
    pts = []
    for (p0, p1, p2, p3) in segs:
        for k in range(per):
            pts.append(bez(p0, p1, p2, p3, k / per))
        pts.append(p3)
    return pts


def path_d(segs):
    d = [f"M {segs[0][0][0]:.1f} {segs[0][0][1]:.1f}"]
    for (_, p1, p2, p3) in segs:
        d.append(f"C {p1[0]:.1f} {p1[1]:.1f} {p2[0]:.1f} {p2[1]:.1f} {p3[0]:.1f} {p3[1]:.1f}")
    return " ".join(d)


def at(pts, u):
    """Point and tangent at normalised arclength u along a polyline."""
    seg = [math.hypot(pts[i + 1][0] - pts[i][0], pts[i + 1][1] - pts[i][1])
           for i in range(len(pts) - 1)]
    target, acc = u * sum(seg), 0.0
    for i, L in enumerate(seg):
        if acc + L >= target or i == len(seg) - 1:
            t = (target - acc) / L if L else 0.0
            p = (pts[i][0] + (pts[i + 1][0] - pts[i][0]) * t,
                 pts[i][1] + (pts[i + 1][1] - pts[i][1]) * t)
            return p, math.atan2(pts[i + 1][1] - pts[i][1], pts[i + 1][0] - pts[i][0])
        acc += L
    return pts[-1], 0.0


def leaf(bx, by, ang, L, width_f=0.30, vein=True):
    """A pointed-oval leaf rooted at (bx,by), pointing along ang."""
    tx, ty = bx + math.cos(ang) * L, by + math.sin(ang) * L
    mx, my = (bx + tx) / 2, (by + ty) / 2
    w = L * width_f
    px, py = -math.sin(ang) * w, math.cos(ang) * w
    shape = (f"M{bx:.1f} {by:.1f} Q{mx + px:.1f} {my + py:.1f} {tx:.1f} {ty:.1f} "
             f"Q{mx - px:.1f} {my - py:.1f} {bx:.1f} {by:.1f} Z")
    out = [f'<path d="{shape}" fill="{COBALT}" fill-opacity="{FILL_OP}" '
           f'stroke="{COBALT}" stroke-opacity="{LINE_OP}" stroke-width="{sw():.2f}"/>']
    if vein:
        out.append(f'<path d="M{bx:.1f} {by:.1f} L{tx:.1f} {ty:.1f}" fill="none" '
                   f'stroke="{COBALT}" stroke-opacity="{LINE_OP}" stroke-width="0.5"/>')
    return "".join(out)


def branch(segs, leaves, width=1.2):
    """A stem (cubic chain) with leaves rooted on it at arclength positions."""
    pts = chain(segs)
    g = [f'<g fill="none" stroke="{COBALT}" stroke-opacity="{LINE_OP}" stroke-width="{width}">',
         f'<path d="{path_d(segs)}"/>', "</g>"]
    for (u, off, L) in leaves:
        (x, y), tan = at(pts, u)
        g.append(leaf(x, y, tan + math.radians(off), L))
    return "".join(g)


def sprig(pts, u, off, scale, n=6):
    """A bowed side-shoot rooted on the parent stem at arclength u."""
    (bx, by), tan = at(pts, u)
    a = tan + math.radians(off)
    length = 150 * scale
    ex, ey = bx + math.cos(a) * length, by + math.sin(a) * length
    bow = 0.20 * length
    mx = (bx + ex) / 2 - math.sin(a) * bow
    my = (by + ey) / 2 + math.cos(a) * bow
    parts = [f'<g fill="none" stroke="{COBALT}" stroke-opacity="{LINE_OP}" stroke-width="1.1">',
             f'<path d="M{bx:.1f} {by:.1f} Q{mx:.1f} {my:.1f} {ex:.1f} {ey:.1f}"/>', "</g>"]
    for i in range(n):
        t = 0.18 + 0.76 * i / max(1, n - 1)
        sx = (1 - t) ** 2 * bx + 2 * (1 - t) * t * mx + t * t * ex
        sy = (1 - t) ** 2 * by + 2 * (1 - t) * t * my + t * t * ey
        side = -1 if i % 2 == 0 else 1
        parts.append(leaf(sx, sy, a + math.radians(side * 58 - 10), (54 - 4 * i) * scale))
    return "".join(parts)


def rim():
    """Thin double rule plus a repeating petal band near the outer edge."""
    g = [f'<g fill="none" stroke="{COBALT}" stroke-opacity="{LINE_OP}">',
         f'<rect x="18" y="18" width="{W - 36}" height="{H - 36}" rx="26" stroke-width="1"/>',
         f'<rect x="30" y="30" width="{W - 60}" height="{H - 60}" rx="18" stroke-width="0.6"/>',
         "</g>",
         f'<g fill="none" stroke="{COBALT}" stroke-opacity="{LINE_OP}" stroke-width="0.8">']
    for x in range(90, W - 60, 92):
        for y in (40, H - 40):
            g.append(f'<path d="M{x} {y} q14 -14 28 0 q-14 14 -28 0 Z"/>')
    g.append("</g>")
    return "".join(g)


def wrap(body):
    return (f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {W} {H}" '
            f'width="{W}" height="{H}">{body}</svg>')


def main():
    # serpentine main stem — enters off-canvas left, sweeps the middle, exits right
    main_segs = [
        ((-70, 262), (240, 148), (430, 330), (665, 432)),
        ((665, 432), (900, 536), (1085, 566), (1295, 498)),
        ((1295, 498), (1495, 430), (1598, 628), (1700, 556)),
    ]
    main_pts = chain(main_segs)

    # lower stem branches off the main one at a shared junction point
    jx, jy = bez(*main_segs[2], 0.60)
    lower_segs = [
        ((jx, jy), (jx - 250, jy + 190), (1230, 892), (925, 916)),
        ((925, 916), (620, 940), (400, 1042), (150, 1108)),
        ((150, 1108), (-80, 1160), (-140, 970), (-210, 1036)),
    ]
    lower_pts = chain(lower_segs)

    # rim stems take off from points on the main stem — they meet, not merge
    lx, ly = bez(*main_segs[0], 0.20)
    left_segs = [
        ((lx, ly), (lx - 210, ly + 170), (58, 640), (100, 826)),
        ((100, 826), (140, 1006), (30, 1130), (156, 1192)),
    ]
    rx, ry = bez(*main_segs[2], 0.90)
    right_segs = [
        ((rx, ry), (rx - 60, ry + 150), (1480, 700), (1404, 872)),
        ((1404, 872), (1330, 1042), (1610, 1084), (1566, 1195)),
    ]

    body = (
        branch(main_segs, [(0.06, 38, 62), (0.22, -42, 68), (0.38, 40, 64),
                           (0.55, -44, 70), (0.72, 42, 62), (0.88, -40, 66)], width=1.5) +
        branch(lower_segs, [(0.14, -40, 62), (0.36, 42, 66),
                            (0.58, -42, 62), (0.80, 40, 64)]) +
        branch(left_segs, [(0.18, 46, 64), (0.44, -46, 60), (0.70, 48, 62)]) +
        branch(right_segs, [(0.20, -46, 62), (0.48, 46, 60), (0.76, -44, 62)]) +
        sprig(main_pts, 0.30, 58, 1.45, 6) +     # upper side-shoot, reaching inward
        sprig(main_pts, 0.66, -62, 1.15, 5) +    # lower side-shoot
        sprig(lower_pts, 0.46, 60, 1.05, 5)      # lower stem side-shoot
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
