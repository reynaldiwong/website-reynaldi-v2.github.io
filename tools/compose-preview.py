"""Compose the room deliverables from the raw captures.

A-portrait.png — the eye-gate: previous point set / sparser base / the vertex
pulse at its peak, then a zoomed trough-vs-peak pair so the twinkle is visible
in a still.
B-changes.png  — the four numerically-verified changes.
"""
import io
import re

from PIL import Image, ImageDraw, ImageFont

S = "_shots"
INK = (31, 78, 140)
SOFT = (110, 128, 152)
PAPER = (250, 250, 252)


def font(size, bold=True):
    for n in (("seguisb.ttf", "segoeui.ttf") if bold else ("segoeui.ttf",)):
        try:
            return ImageFont.truetype("C:/Windows/Fonts/" + n, size)
        except OSError:
            continue
    return ImageFont.load_default()


def box(im, w=3, color=(214, 224, 238)):
    ImageDraw.Draw(im).rectangle([0, 0, im.width - 1, im.height - 1], outline=color, width=w)
    return im


def svg_stats(path):
    s = io.open(path, encoding="utf-8").read()
    return len(re.findall(r"h0", s)), len(re.findall(r"l-?\d", s)), len(s) / 1024


def portrait_sheet():
    old_d, old_l, old_kb = svg_stats(f"{S}/old-lines.svg")
    new_d, new_l, new_kb = svg_stats("assets/img/me-lines.svg")

    panels = [
        ("panel-before.png", "BEFORE", f"{old_d:,} dots · all opaque · static"),
        ("panel-after.png", "AFTER", f"{new_d:,} dots · base at 0.30 · strokes longer"),
        ("panel-twinkle.png", "ANIMATED", "vertex layer at its peak (0.70)"),
    ]
    ims = [Image.open(f"{S}/{n}").convert("RGB") for n, _, _ in panels]
    h = 700
    ims = [im.resize((int(im.width * h / im.height), h), Image.LANCZOS) for im in ims]
    gap, side, top = 36, 40, 100
    W = side * 2 + sum(i.width for i in ims) + gap * 2
    row1 = top + h

    # zoom row: the same face crop at the two ends of the pulse
    zoom_h = 430
    def crop(name):
        im = Image.open(f"{S}/{name}").convert("RGB")
        c = im.crop((int(im.width * 0.30), int(im.height * 0.08), int(im.width * 0.72), int(im.height * 0.58)))
        return c.resize((int(c.width * zoom_h / c.height), zoom_h), Image.LANCZOS)
    ztr, zpk = crop("panel-trough.png"), crop("panel-twinkle.png")

    H = row1 + 96 + zoom_h + 46
    canvas = Image.new("RGB", (W, H), PAPER)
    d = ImageDraw.Draw(canvas)
    x = side
    for (_, tag, sub), im in zip(panels, ims):
        d.text((x, 22), tag, font=font(34), fill=INK)
        d.text((x, 62), sub, font=font(22, bold=False), fill=SOFT)
        canvas.paste(box(im), (x, top))
        x += im.width + gap
    d.text((side, row1 + 6), f"dots {old_d:,} -> {new_d:,}   ·   line segments {old_l:,} -> {new_l:,}   ·   hero asset {old_kb:.1f} KB -> {new_kb:.1f} KB + 14.4 KB pulse layer",
           font=font(23, bold=False), fill=SOFT)
    d.text((side, row1 + 44), "Zoomed, same crop: pulse trough (left) vs pulse peak (right) — vertices swing ~0.34 -> ~0.78 combined opacity",
           font=font(23, bold=False), fill=SOFT)
    canvas.paste(box(ztr), (side, row1 + 88))
    canvas.paste(box(zpk), (side + ztr.width + gap, row1 + 88))
    canvas.save(f"{S}/A-portrait.png", optimize=True)
    print("A-portrait.png", canvas.size, f"(dots {old_d}->{new_d}, segs {old_l}->{new_l})")


def change_sheet():
    items = [
        ("G-selection.png", "Selection block: square corners, 0.12em/0.2em padding, and the lead phrase now carries it too — all 8.31:1"),
        ("F-spotify-match.png", "Spotify column matches the video by ratio (3:2): 312px vs 312px at 1440, 223px vs 223px at 375"),
        ("H-numerals.png", "Section numerals are ui-monospace now — editor line numbers instead of display serif"),
    ]
    W = 1120
    tiles = []
    for name, cap in items:
        im = Image.open(f"{S}/{name}").convert("RGB")
        im = im.resize((W, max(120, int(im.height * W / im.width))), Image.LANCZOS)
        if im.height > 700:
            im = im.crop((0, 0, W, 700))
        tiles.append((box(im), cap))
    top, gap, pad = 78, 34, 40
    H = top + sum(t.height + 60 for t, _ in tiles) + pad
    canvas = Image.new("RGB", (W + pad * 2, H), PAPER)
    d = ImageDraw.Draw(canvas)
    d.text((pad, 26), "Shipped this round · verified in-browser at 1440px and 375px", font=font(32), fill=INK)
    y = top
    for im, cap in tiles:
        canvas.paste(im, (pad, y)); y += im.height + 10
        d.text((pad, y), cap, font=font(24, bold=False), fill=SOFT); y += 50 + gap
    canvas.save(f"{S}/D-this-round.png", optimize=True)
    print("D-this-round.png", canvas.size)


change_sheet()
