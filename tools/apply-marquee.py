"""One-off: replace the text marquee with monochrome inline tool logos.

Reads simple-icons SVGs from _si/ (MIT — single currentColor path each),
builds a hidden <symbol> sprite, and splices it + the logo marquee into
index.html. Run from repo root:  python tools/apply-marquee.py
"""
import re

SLUGS = ["kubernetes", "docker", "jenkins", "argo", "googlecloud",
         "ansible", "n8n", "sonarqube", "python"]


def main():
    symbols = []
    for slug in SLUGS:
        svg = open(f"_si/{slug}.svg", encoding="utf-8").read()
        d = re.search(r'<path d="([^"]+)"', svg).group(1)
        symbols.append(f'<symbol id="logo-{slug}" viewBox="0 0 24 24"><path d="{d}"/></symbol>')

    sprite = ('<svg class="logo-sprite" aria-hidden="true" focusable="false">'
              + "".join(symbols) + '</svg>')

    uses = "".join(
        f'<svg class="marquee__logo" viewBox="0 0 24 24"><use href="#logo-{s}"/></svg>'
        for s in SLUGS
    )
    marquee = (
        '    <!-- ============ MARQUEE (monochrome tool logos) ============ -->\n'
        '    <div class="marquee" aria-hidden="true">\n'
        f'      <div class="marquee__track">{uses}{uses}</div>\n'
        '    </div>\n\n'
    )

    html = open("index.html", encoding="utf-8").read()
    html = html.replace("<body>\n", "<body>\n  " + sprite + "\n", 1)
    start = html.index("    <!-- ============ MARQUEE")
    end = html.index("    <!-- ============ OFF-DUTY")
    html = html[:start] + marquee + html[end:]
    open("index.html", "w", encoding="utf-8").write(html)
    print(f"sprite {len(sprite)} B | index.html now {len(html)} B")


if __name__ == "__main__":
    main()
