"""Dev server that actually serves 404.html for missing paths.

`python -m http.server` answers a missing path with its own plain-text error page, so
the custom 404 never appears locally — which makes "my 404 page doesn't work" a
property of the dev server, not of the page. Cloudflare, GitHub Pages and Netlify all
serve 404.html automatically, so this exists purely so wrong paths behave locally the
way they will once deployed.

    python tools/serve.py 8123        # then open http://localhost:8123/
    curl -i http://localhost:8123/nope/whatever

Run it from the repo root: SimpleHTTPRequestHandler serves the current directory.
"""
import sys
from http.server import SimpleHTTPRequestHandler, ThreadingHTTPServer

PAGE = "404.html"


class Handler(SimpleHTTPRequestHandler):
    def send_error(self, code, message=None, explain=None):
        if code != 404:
            return super().send_error(code, message, explain)
        try:
            body = open(PAGE, "rb").read()
        except OSError:                       # no 404.html: fall back to the default
            return super().send_error(code, message, explain)
        self.send_response(404)               # a real 404 status, not a 200 with a page
        self.send_header("Content-Type", "text/html; charset=utf-8")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        if self.command != "HEAD":
            self.wfile.write(body)

    def log_message(self, fmt, *args):        # quieter, but keep the status visible
        sys.stderr.write("  %s %s\n" % (self.command, self.path))


if __name__ == "__main__":
    port = int(sys.argv[1]) if len(sys.argv) > 1 else 8123
    print("serving http://localhost:%d/  (404.html wired for missing paths)" % port)
    ThreadingHTTPServer(("127.0.0.1", port), Handler).serve_forever()
