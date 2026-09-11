"""Strip the near-white card field from the Credly CKAD badge to alpha.

Edge flood-fill so only the OUTER white field is cleared — the badge's own
white seal stays intact. One-off, not shipped.

Run from repo root:  python tools/gen-badge.py
"""
import os
from collections import deque

import numpy as np
from PIL import Image

SRC = "assets/img/badges/ckad-credly.png"
OUT = "assets/img/badges/ckad-credly-transparent"
WHITE = 232   # near-white threshold


def main():
    img = Image.open(SRC).convert("RGBA")
    a = np.array(img)
    h, w = a.shape[:2]
    white = (a[:, :, 0] >= WHITE) & (a[:, :, 1] >= WHITE) & (a[:, :, 2] >= WHITE)

    visited = np.zeros((h, w), bool)
    q = deque()
    for x in range(w):
        for y in (0, h - 1):
            if white[y, x] and not visited[y, x]:
                visited[y, x] = True
                q.append((y, x))
    for y in range(h):
        for x in (0, w - 1):
            if white[y, x] and not visited[y, x]:
                visited[y, x] = True
                q.append((y, x))
    while q:
        y, x = q.popleft()
        for dy, dx in ((1, 0), (-1, 0), (0, 1), (0, -1)):
            ny, nx = y + dy, x + dx
            if 0 <= ny < h and 0 <= nx < w and not visited[ny, nx] and white[ny, nx]:
                visited[ny, nx] = True
                q.append((ny, nx))

    a[visited, 3] = 0
    out = Image.fromarray(a)
    os.makedirs("_shots", exist_ok=True)
    out.save(OUT + ".webp", "WEBP", quality=90, method=6)
    out.save(OUT + ".png")

    # preview composited on porcelain
    bg = Image.new("RGBA", (w, h), (247, 246, 242, 255))
    bg.alpha_composite(out)
    bg.convert("RGB").save("_shots/badge-transparent-preview.png")
    print(f"cleared {int(visited.sum())} px of {h * w} "
          f"({visited.sum() / (h * w) * 100:.1f}%)")
    print(f"wrote {OUT}.webp ({os.path.getsize(OUT + '.webp') / 1024:.1f} KB) "
          f"and preview")


if __name__ == "__main__":
    main()
