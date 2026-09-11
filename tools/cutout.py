"""Cut the subject out of me.jpg into an RGBA me.webp.

The point is the ALPHA CHANNEL: it is the subject mask, and because dotwave.js already
loads this exact file as its canvas source, both renderers read one mask from one file.
That is deliberate — the SVG plate and the animated canvas literally cannot drift,
which is the bug class that bit us when the plate was grid 8 / radius 2 while the
canvas was still 6 / 6.

Alpha is binarised at ALPHA_CUT. rembg returns a soft matte, but a dot matrix wants a
hard yes/no per cell; 128 is the standard midpoint and matches the canvas's own gate in
dotwave.js (ALPHA_MIN), so the two agree cell for cell.

Run from repo root, in the segmentation venv (the model downloads on first use, ~176 MB):
    .venv-seg/Scripts/python.exe tools/cutout.py
"""
import numpy as np
from PIL import Image
from rembg import remove

SRC = "assets/img/me.jpg"
OUT = "assets/img/me.webp"
ALPHA_CUT = 128          # keep in step with dotwave.js's ALPHA_MIN
QUALITY, METHOD = 82, 6  # the same encode settings the plain re-encode used


def main():
    img = Image.open(SRC).convert("RGB")
    cut = np.asarray(remove(img)).copy()          # RGBA, soft matte
    soft = cut[..., 3]
    hard = (soft >= ALPHA_CUT).astype(np.uint8) * 255
    cut[..., 3] = hard
    Image.fromarray(cut, "RGBA").save(OUT, "WEBP", quality=QUALITY, method=METHOD)

    h, w = hard.shape
    subject = int((hard > 0).sum())
    # bounding box of the subject, as a share of the frame
    rows, cols = np.where(hard > 0)
    print(f"{OUT}: {w}x{h}, subject {subject} px ({100 * subject / (w * h):.1f}% of frame), "
          f"alpha cut {ALPHA_CUT}, soft alpha kept: {(soft < 128).sum() - (soft < 1).sum()} px")
    if len(rows):
        print("  subject bbox: x %d..%d  y %d..%d  (%d%% of the frame wide, %d%% tall)"
              % (cols.min(), cols.max(), rows.min(), rows.max(),
                 100 * (cols.max() - cols.min()) / w, 100 * (rows.max() - rows.min()) / h))


if __name__ == "__main__":
    main()
