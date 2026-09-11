"""Generate the underglaze-blue floral porcelain background.

One-off generator — not shipped as runtime JS. Cobalt ink only (#1f4e8c),
no new colours. Ornament sits at the rim; the centre column stays clear.

Run from repo root:  python tools/gen-porcelain.py
Outputs assets/img/bg-porcelain.svg (blooms + vine)
        assets/img/bg-porcelain-rim.svg (rim band, wide viewports)
"""
import math

W, H = 1600, 1200
COBALT = "#1f4e8c"


def ell(cx, cy, rx, ry, rot):
    return (f'<ellipse cx="{cx:.1f}" cy="{cy:.1f}" rx="{rx:.1f}" ry="{ry:.1f}" '
            f'transform="rotate({rot:.1f} {cx:.1f} {cy:.1f})"/>')


def blooming(cx, cy, s, fill_op=0.05, stroke_op=0.14):
    """Peony bloom: overlapping ellipse petals around a centre."""
    g = [f'<g fill="{COBALT}" fill-opacity="{fill_op}" stroke="{COBALT}" '
         f'stroke-opacity="{stroke_op}" stroke-width="1.2">']
    rings = [((6, 98, 52, 98), 0), ((7, 62, 36, 62), 22), ((5, 32, 22, 32), 10)]
    for (n, r, rx, ry), off in rings:
        for i in range(n):
            a = off + i * 360.0 / n
            rad = math.radians(a)
            px = cx + math.cos(rad) * r * s
            py = cy + math.sin(rad) * r * s
            g.append(ell(px, py, rx * s, ry * s, a))
    g.append(f'<circle cx="{cx:.1f}" cy="{cy:.1f}" r="{15 * s:.1f}"/>')
    g.append("</g>")
    return "".join(g)


def leaf(bx, by, ang, L, wdt):
    tipx = bx + math.cos(math.radians(ang)) * L
    tipy = by + math.sin(math.radians(ang)) * L
    mx = bx + math.cos(math.radians(ang)) * L / 2
    my = by + math.sin(math.radians(ang)) * L / 2
    px, py = -math.sin(math.radians(ang)) * wdt, math.cos(math.radians(ang)) * wdt
    return (f'M{bx:.0f} {by:.0f} Q{mx + px:.0f} {my + py:.0f} {tipx:.0f} {tipy:.0f} '
            f'Q{mx - px:.0f} {my - py:.0f} {bx:.0f} {by:.0f} Z')


def vine(d, leaves, stroke_op=0.12):
    """One curling cubic-bezier stem with small leaves."""
    g = [f'<g fill="none" stroke="{COBALT}" stroke-opacity="{stroke_op}" stroke-width="1.2">',
         f'<path d="{d}"/>']
    for (bx, by, ang) in leaves:
        g.append(f'<path d="{leaf(bx, by, ang, 74, 22)}" '
                 f'fill="{COBALT}" fill-opacity="0.04"/>')
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
        "M 34 150 C 210 330, -50 560, 118 742 S 40 1030, 168 1130",
        [(150, 300, 210), (30, 560, 160), (120, 800, 220), (60, 1010, 150)],
    )
    right_vine = vine(
        f"M {W - 26} 300 C {W - 210} 452, {W + 40} 640, {W - 150} 812 "
        f"S {W - 50} 1010, {W - 190} 1160",
        [(W - 150, 440, 330), (W - 30, 660, 300), (W - 170, 900, 340)],
    )
    body = (
        blooming(1480, 70, 1.5) +        # top-right, bleeding off the corner
        blooming(80, 1120, 1.15) +       # bottom-left
        blooming(1580, 1000, 0.8) +      # bottom-right sprig
        blooming(60, 60, 0.6) +          # top-left corner sprig
        blooming(1370, 470, 0.55) +      # right-edge mid sprig
        left_vine + right_vine
    )
    main_svg = wrap(body)
    rim_svg = wrap(rim())
    for path, svg in (("assets/img/bg-porcelain.svg", main_svg),
                      ("assets/img/bg-porcelain-rim.svg", rim_svg)):
        with open(path, "w", encoding="utf-8") as f:
            f.write(svg)
        print(f"{path}: {len(svg)} bytes = {len(svg) / 1024:.1f} KB")


if __name__ == "__main__":
    main()
