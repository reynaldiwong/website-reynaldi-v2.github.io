"""Generate the faceted cobalt background mesh (bg-mesh.svg).

Periphery-weighted Delaunay triangulation filled from the reference's blue ramp.
Run from the repo root:  python tools/mesh.py
Outputs assets/img/bg-mesh.svg
"""
import numpy as np
from scipy.spatial import Delaunay

# Reference ramp (light -> dark), from the extracted palette.
RAMP = ["#d5dee8", "#bfccda", "#a1b2cc", "#7b91b8", "#536d9e", "#223a71"]

W, H = 1600, 900
N = 155
SEED = 7


def main():
    rng = np.random.default_rng(SEED)
    pts = []
    # Periphery-weighted sampling: accept with probability ~ radius, so facets
    # concentrate at the edges/corners and thin out through the centre column.
    while len(pts) < N:
        x = rng.uniform(0, W)
        y = rng.uniform(0, H)
        dx = (x - W / 2) / (W / 2)
        dy = (y - H / 2) / (H / 2)
        r = np.hypot(dx, dy)  # 0 centre -> 1 corner
        if rng.random() < (0.12 + 0.88 * r ** 1.35):
            pts.append((x, y))
    # Pin corners + edge midpoints so the mesh always covers the viewport.
    pts += [(0, 0), (W, 0), (0, H), (W, H),
            (W / 2, 0), (W / 2, H), (0, H / 2), (W, H / 2)]
    pts = np.array(pts)
    tri = Delaunay(pts)

    parts = [f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {W} {H}" '
             f'width="{W}" height="{H}">']
    for s in tri.simplices:
        p = pts[s]
        cx, cy = p[:, 0].mean(), p[:, 1].mean()
        dx = (cx - W / 2) / (W / 2)
        dy = (cy - H / 2) / (H / 2)
        r = np.hypot(dx, dy)
        # Darker blues at the periphery, lighter (thinner) through the centre.
        idx = int(r * (len(RAMP) - 1) + rng.uniform(-0.6, 0.6))
        idx = max(0, min(len(RAMP) - 1, idx))
        coords = " ".join(f"{px:.1f},{py:.1f}" for px, py in p)
        parts.append(f'<polygon points="{coords}" fill="{RAMP[idx]}"/>')
    parts.append("</svg>")
    svg = "\n".join(parts)

    with open("assets/img/bg-mesh.svg", "w", encoding="utf-8") as f:
        f.write(svg)
    print(f"wrote assets/img/bg-mesh.svg ({len(svg)} bytes, {len(tri.simplices)} facets)")


if __name__ == "__main__":
    main()
