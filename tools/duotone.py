"""Blue duotone from me.jpg — the shipped hero portrait.

One palette, two stops: shadows to #163a6b (cobalt-deep), highlights to #dce7f4
(cobalt-soft). Palette-locked, so the portrait cannot drift away from the site's blues.

This replaces the whole dot pipeline (gen-dots.py / dotwave.js / the subject mask). Those
tools stay in the repo because they are inert and this decision has reversed before; only
their outputs are retired.

Output keeps the SOURCE's own size (528x704 as of writing). The hero renders it 1:1 via
`aspect-ratio: 1/1` + `object-fit: cover`, which crops centred at runtime - the same crop a
baked square would give, but it cannot disagree with the CSS, and the full frame survives
if the crop is ever wrong. (A face-centred crop was measured and rejected: the skin-tone
centroid sits 56% down the frame, so centring on it shifts the window DOWN and clips the
head.)

Run from repo root:
    python tools/duotone.py
"""
import os

import numpy as np
from PIL import Image, ImageOps

SRC = "assets/img/me.jpg"
OUT = "assets/img/me-duotone.webp"
BLACK = (22, 58, 107)      # #163a6b  cobalt-deep  -> shadows
WHITE = (220, 231, 244)    # #dce7f4  cobalt-soft  -> highlights
WIDTH = 900                # the hero displays ~449 CSS px wide, so 900 covers a 2x display
QUALITY, METHOD = 86, 6


def main():
    img = Image.open(SRC).convert("RGB")
    original = img.size
    if img.width > WIDTH:                      # source may be a full-resolution phone photo
        img = img.resize((WIDTH, round(img.height * WIDTH / img.width)), Image.LANCZOS)
    gray = ImageOps.grayscale(img)
    duo = ImageOps.colorize(gray, black=BLACK, white=WHITE).convert("RGB")
    duo.save(OUT, "WEBP", quality=QUALITY, method=METHOD)

    g = np.asarray(gray).astype(float)
    d = np.asarray(duo).astype(float)
    lum = d.mean(axis=2)
    lo, hi = np.percentile(g, 1), np.percentile(g, 99)

    print("%s: %dx%d" % (OUT, duo.size[0], duo.size[1])
          + ("  (downscaled from %dx%d)" % original if original != duo.size else ""))
    print("  file size        : %.1f KB" % (os.path.getsize(OUT) / 1024))
    print("  source grayscale : min %.0f  p1 %.0f  median %.0f  p99 %.0f  max %.0f"
          % (g.min(), lo, np.median(g), hi, g.max()))
    print("  output luminance : min %.1f  mean %.1f  max %.1f  std %.1f"
          % (lum.min(), lum.mean(), lum.max(), lum.std()))
    print("  shadow pixel     : %s   (target %s)" % (np.asarray(duo).reshape(-1, 3)[lum.argmin()].tolist(), list(BLACK)))
    print("  highlight pixel  : %s   (target %s)" % (np.asarray(duo).reshape(-1, 3)[lum.argmax()].tolist(), list(WHITE)))

    # Contrast against the section behind it. The page is porcelain (~245), so highlights
    # landing near it make the portrait dissolve into the page.
    page = 245.0
    print("  brightest highlight sits %.1f below the porcelain page (245) -> %s"
          % (page - lum.max(), "reads against it" if page - lum.max() > 8 else "washes into it"))
    if hi - lo < 90:
        print("  NOTE: the source's p1..p99 range is only %.0f/255 - the duotone will read flat;"
              " push the white stop darker or the black stop to #0f2f57." % (hi - lo))
    if lum.mean() > 165:
        print("  NOTE: mean luminance %.1f is bright - this source is light overall (median"
              " grayscale %.0f), so the duotone may read washed against the porcelain page."
              " The dial is the white stop." % (lum.mean(), np.median(g)))


if __name__ == "__main__":
    main()
