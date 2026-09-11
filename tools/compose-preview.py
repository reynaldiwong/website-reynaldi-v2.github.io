"""Compose the deliverable previews for the room: portrait before/after, and a
single contact sheet of the four verified changes."""
from PIL import Image, ImageDraw, ImageFont

S = "_shots"
INK = (31, 78, 140)
SOFT = (110, 128, 152)
PAPER = (250, 250, 252)


def font(size, bold=True):
    for name in (("seguisb.ttf", "segoeui.ttf") if bold else ("segoeui.ttf",)):
        try:
            return ImageFont.truetype("C:/Windows/Fonts/" + name, size)
        except OSError:
            continue
    return ImageFont.load_default()


def label(im, text, size=30, color=INK, pad=(0, 0)):
    d = ImageDraw.Draw(im)
    d.text(pad, text, font=font(size), fill=color)
    return im


def box(im, w=3, color=(214, 224, 238)):
    d = ImageDraw.Draw(im)
    d.rectangle([0, 0, im.width - 1, im.height - 1], outline=color, width=w)
    return im


# ---- 1. portrait before / after -------------------------------------------------
def portrait_pair():
    a = Image.open(f"{S}/lines-only.png").convert("RGB")
    b = Image.open(f"{S}/portrait-1440.png").convert("RGB")
    h = 880
    a = a.resize((int(a.width * h / a.height), h), Image.LANCZOS)
    b = b.resize((int(b.width * h / b.height), h), Image.LANCZOS)
    top, gap, side = 96, 44, 40
    W = side * 2 + a.width + gap + b.width
    canvas = Image.new("RGB", (W, top + h + 46), PAPER)
    d = ImageDraw.Draw(canvas)
    f = font(34)
    d.text((side, 30), "BEFORE  ·  lines only, no tone", font=f, fill=SOFT)
    d.text((side + a.width + gap, 30), "AFTER  ·  + cobalt duotone under the lines", font=f, fill=INK)
    canvas.paste(box(a), (side, top))
    canvas.paste(box(b), (side + a.width + gap, top))
    canvas.save("A-portrait.png", optimize=True)
    print("A-portrait.png", canvas.size)


# ---- 2. change sheet ------------------------------------------------------------
def change_sheet():
    items = [
        ("contact-1440.png", "Email me stays the only CTA · email text removed · LinkedIn / GitHub / Discord as cobalt marks, label under"),
        ("about-1440.png", "Bold copy gets the marker highlight · body text now --ink-soft (8.9:1)"),
        ("sectionhead-1440.png", "Numeral nudged back to -0.4em / -0.25em"),
        ("rim-1440.png", "Left/right rim now rides the same two inks as the leaves"),
    ]
    scale_w = 1080
    tiles = []
    for name, cap in items:
        im = Image.open(f"{S}/{name}").convert("RGB")
        im = im.resize((scale_w, max(120, int(im.height * scale_w / im.width))), Image.LANCZOS).crop((0, 0, scale_w, min(im.height, 560)))
        tiles.append((box(im), cap))
    top, gap, pad = 74, 34, 40
    H = top + sum(t.height + 30 + 34 for t, _ in tiles) + pad
    canvas = Image.new("RGB", (scale_w + pad * 2, H), PAPER)
    d = ImageDraw.Draw(canvas)
    d.text((pad, 24), "Verified in-browser at 1440px", font=font(32), fill=INK)
    y = top
    for im, cap in tiles:
        canvas.paste(im, (pad, y)); y += im.height + 8
        d.text((pad, y), cap, font=font(24, bold=False), fill=SOFT); y += 30 + gap
    canvas.save("B-changes.png", optimize=True)
    print("B-changes.png", canvas.size)


portrait_pair()
change_sheet()
