"""Generate the cobalt portrait assets (stipple dots + contour-traced lines).

One-off generator, Pillow + numpy + scipy — NOT shipped as runtime JS.
Transparent background, cobalt #1f4e8c only, so it drops into the porcelain
page instead of baking a background.

Run from repo root:  python tools/gen-stipple.py
Outputs assets/img/me-stipple.svg   (frozen option 2)
        assets/img/me-lines.svg     (hero — contour-traced)
        _lowpoly/*                  reference densities
"""
import math
import os

import numpy as np
from PIL import Image, ImageFilter
from scipy.ndimage import gaussian_filter
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


def svg_open():
    return (f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {W} {H}" '
            f'width="{W}" height="{H}">')


def write(path, svg):
    os.makedirs(os.path.dirname(path) or ".", exist_ok=True)
    with open(path, "w", encoding="utf-8") as f:
        f.write(svg)


def build(step, name, out=OUT, seed=SEED):
    """Stipple: tone-weighted dots on a jittered grid, grouped into radius
    buckets so each path carries one stroke-width (keeps the file small)."""
    tone = tone_curve(load())
    rng = np.random.default_rng(seed)
    jit = 0.4 * step
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

    parts = [svg_open()]
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
    write(f"{out}/{name}", svg)

    arr = np.array([(x, y) for b in bins for (x, y) in b], dtype=float)
    nn = cKDTree(arr).query(arr, k=2)[0][:, 1]
    radii = np.array(radii)
    print(f"{out}/{name}: {len(svg) / 1024:.1f} KB, {len(pts)} dots  "
          f"(radius {radii.min():.2f}-{radii.max():.2f}, NN {nn.mean():.2f})")


def build_lines(step, name, out=OUT, seed=SEED, max_edge=17.5, levels=7):
    """Contour-traced wireframe portrait.

    The lines follow the FACE, not a free triangulation: Sobel gradient on a
    blurred grayscale gives the feature ridges (jaw, hair, eyes, nose), points
    are sampled along those ridges, and each point is chained to its nearest
    neighbour in the local edge-tangent direction — so the strokes run along
    the contours instead of striking across empty space. A sparse interior fill
    anchors the dots. Edge opacity is modulated by local tone: dense/bright in
    shadow, faint over light skin."""
    lum = load()
    smooth = gaussian_filter(lum, 1.2)
    gy, gx = np.gradient(smooth * 255.0)
    mag = gaussian_filter(np.hypot(gx, gy), 0.6)
    tone = tone_curve(lum)
    thr = float(np.percentile(mag, 85.0))
    rng = np.random.default_rng(seed)

    pts, tones, on_edge = [], [], []
    for y in range(0, H, step):
        for x in range(0, W, step):
            px = x + step // 2 + int(round(rng.uniform(-0.35, 0.35) * step))
            py = y + step // 2 + int(round(rng.uniform(-0.35, 0.35) * step))
            if not (1 <= px < W - 1 and 1 <= py < H - 1):
                continue
            if mag[py, px] >= thr:
                pts.append((px, py)); tones.append(float(tone[py, px])); on_edge.append(True)
            elif tone[py, px] > 0.18 and rng.random() < 0.05:
                pts.append((px, py)); tones.append(float(tone[py, px])); on_edge.append(False)

    pts = np.array(pts, dtype=float)
    tones = np.array(tones)
    on_edge = np.array(on_edge)
    tree = cKDTree(pts)

    # local edge tangent = perpendicular to the luminance gradient
    tang = np.zeros_like(pts)
    for i, (px, py) in enumerate(pts):
        a, b = gx[int(py), int(px)], gy[int(py), int(px)]
        n = math.hypot(a, b) or 1.0
        tang[i] = (-b / n, a / n)

    dist, idx = tree.query(pts, k=10)
    edges = set()
    for i in range(len(pts)):
        for sign in (1.0, -1.0):
            best, bd = None, max_edge
            for d, j in zip(dist[i][1:], idx[i][1:]):
                if d >= bd:
                    continue
                v = pts[int(j)] - pts[i]
                nv = float(np.linalg.norm(v)) or 1.0
                if float(np.dot(v / nv, tang[i])) * sign > 0.72:
                    best, bd = int(j), float(d)
            if best is not None:
                edges.add((i, best) if i < best else (best, i))

    # keep only degree-<=2 vertices: short edges first, so what survives is a set
    # of polylines running along the contours rather than a junction spider
    pruned, deg = set(), {}
    for (a, b) in sorted(edges, key=lambda e: math.hypot(*(pts[e[0]] - pts[e[1]]))):
        if deg.get(a, 0) < 2 and deg.get(b, 0) < 2:
            pruned.add((a, b))
            deg[a] = deg.get(a, 0) + 1
            deg[b] = deg.get(b, 0) + 1
    edges = pruned

    # --- pack: walk the degree-<=2 graph into chains, so a run of along-contour
    # segments shares one relative 'l' command instead of restarting every
    # segment with a relative move (about 20% off the file, which buys density)
    adj = {}
    for (a, b) in edges:
        adj.setdefault(a, []).append(b)
        adj.setdefault(b, []).append(a)

    def bucket_of(t):
        return min(levels - 1, int(t * levels))

    seen = set()
    runs = [[] for _ in range(levels)]

    def walk(u, v):
        chain = [u, v]
        while len(adj[chain[-1]]) <= 2:
            nxt = [n for n in adj[chain[-1]]
                   if n != chain[-2] and (min(chain[-1], n), max(chain[-1], n)) not in seen]
            if not nxt:
                break
            n = nxt[0]
            seen.add((min(chain[-1], n), max(chain[-1], n)))
            chain.append(n)
        return chain

    for u in sorted(adj, key=lambda k: len(adj[k])):      # chain ends first
        for v in adj[u]:
            key = (min(u, v), max(u, v))
            if key in seen:
                continue
            seen.add(key)
            chain = walk(u, v)
            i = 0
            while i < len(chain) - 1:
                bk = bucket_of((tones[chain[i]] + tones[chain[i + 1]]) / 2)
                j = i + 1
                while (j < len(chain) - 1 and
                       bucket_of((tones[chain[j]] + tones[chain[j + 1]]) / 2) == bk):
                    j += 1
                runs[bk].append(chain[i:j + 1])
                i = j

    parts = [svg_open()]
    for i, rl in enumerate(runs):
        if not rl:
            continue
        op = 0.12 + (i + 0.5) / levels * 0.43
        d = []
        px = py = 0
        for chain in sorted(rl, key=lambda c: c[0]):
            x0, y0 = int(round(pts[chain[0]][0])), int(round(pts[chain[0]][1]))
            if d:
                d.append(f"m{x0 - px} {y0 - py}")
            else:
                d.append(f"M{x0} {y0}")
            px, py = x0, y0
            for n in chain[1:]:
                x, y = int(round(pts[n][0])), int(round(pts[n][1]))
                d.append(f"l{x - px} {y - py}")
                px, py = x, y
        parts.append(f'<path d="{"".join(d)}" stroke="{COBALT}" stroke-width="0.6" '
                     f'stroke-opacity="{op:.2f}" fill="none"/>')

    def dotset(mask, width):
        sub = pts[mask]
        if not len(sub):
            return ""
        vx, vy = int(round(sub[0][0])), int(round(sub[0][1]))
        seg = [f"M{vx} {vy}h0"]
        for (px_, py_) in sub[1:]:
            rx, ry = int(round(px_)), int(round(py_))
            seg.append(f"m{rx - vx} {ry - vy}h0")
            vx, vy = rx, ry
        return (f'<path d="{"".join(seg)}" stroke="{COBALT}" stroke-width="{width}" '
                f'stroke-linecap="round" fill="none"/>')

    parts.append(dotset(on_edge, 2.6))     # contour anchors — carry the shape
    parts.append(dotset(~on_edge, 1.7))    # sparse interior fill
    parts.append("</svg>")
    svg = "".join(parts)
    write(f"{out}/{name}", svg)

    deg = np.zeros(len(pts), dtype=int)
    for a, b in edges:
        deg[a] += 1
        deg[b] += 1
    print(f"{out}/{name}: {len(svg) / 1024:.1f} KB, {int(on_edge.sum())} contour pts "
          f"+ {int((~on_edge).sum())} interior, {len(edges)} edges, "
          f"chain degree mean {deg.mean():.2f}")


def build_duotone(name="me-duotone.webp", out="assets/img", black=0.22, gamma=1.35,
                  max_alpha=0.50, scale=0.50, quality=80, blur=1.4):
    """Cobalt duotone underlay — the photo's TONE as transparent cobalt ink.

    A line network carries structure but no tone, and a face *is* tone, which is
    why the lines alone never quite read as a face. This sits behind
    me-lines.svg to supply the silhouette and the facial shadows, leaving the
    dots and lines as texture on top. The black point keeps light skin clear, so
    the ink reads as shading rather than a wash over the whole frame; it is
    rendered at half resolution and blurred, which is free visually (it is a
    smooth tone layer the CSS scales back up) and roughly a third of the bytes."""
    lum = np.array(Image.open(SRC).convert("L")).astype(float) / 255.0
    tone = np.clip((1.0 - lum - black) / (1.0 - black), 0.0, 1.0) ** gamma
    alpha = np.clip(tone * max_alpha, 0.0, 1.0)
    rgba = np.dstack([np.full_like(alpha, 0x1f), np.full_like(alpha, 0x4e),
                      np.full_like(alpha, 0x8c), alpha * 255]).astype(np.uint8)
    im = Image.fromarray(rgba, "RGBA").filter(ImageFilter.GaussianBlur(blur))
    im = im.resize((int(W * scale), int(H * scale)), Image.LANCZOS)
    path = f"{out}/{name}"
    im.save(path, "WEBP", quality=quality, method=6)
    a = np.array(im)[..., 3]
    print(f"{path}: {os.path.getsize(path) / 1024:.1f} KB, {im.size[0]}x{im.size[1]}, "
          f"alpha max {a.max() / 255:.2f} (cap {max_alpha}), "
          f"coverage {(a > 12).mean() * 100:.0f}%")


def main():
    build(9, "me-stipple.svg", out="assets/img")     # hero fallback: ~4.5k dots (frozen)
    build(7, "me-stipple-6500.svg")                  # reference densities
    build(11, "me-stipple-3000.svg")
    build_lines(5, "me-lines.svg", out="assets/img")  # hero: contour-traced
    build_lines(7, "me-lines-2500.svg")
    build_duotone()                                   # tone layer under the hero lines


if __name__ == "__main__":
    main()
