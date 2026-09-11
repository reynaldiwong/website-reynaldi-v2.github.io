"""Add the three social marks to the inline logo sprite in index.html."""
import io
import re

P = "index.html"
s = io.open(P, encoding="utf-8").read()
m = re.search(r'<svg class="logo-sprite".*?</svg>', s, re.S)
block = m.group()
before = len(block)

add = []
for f, ident in (("linkedin", "logo-linkedin"), ("github", "logo-github"), ("discord", "logo-discord")):
    svg = io.open("_shots/icons/%s.svg" % f, encoding="utf-8").read()
    d = re.search(r'd="([^"]+)"', svg).group(1)
    add.append('<symbol id="%s" viewBox="0 0 24 24"><path d="%s"/></symbol>' % (ident, d))

new = block[: -len("</svg>")] + "".join(add) + "</svg>"
io.open(P, "w", encoding="utf-8", newline="\n").write(s.replace(block, new))
print("sprite: %d -> %d chars, +%d symbols" % (before, len(new), len(add)))
