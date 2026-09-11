/* DotProfile from personal/rey-website, ported to plain JS. The reference was already
   a bare canvas + rAF loop; only the Preact wrapper was framework. Constants unchanged:
   gap 8, baseRadius 2, brightness (r+g+b)/3/255, cull <=0.1,
   radius = brightness*2*(0.8+0.4*wave), wave = sin(0.02x+0.02y-t)/2+0.5, t += 0.03/frame.
   Progressive enhancement: the static me-dots.svg plate stays in the markup; this swaps
   in a canvas only when motion is welcome, so no-JS and reduced-motion keep the plate.

   SRC (me.webp) is the rembg cutout from tools/cutout.py, and its ALPHA CHANNEL is the
   subject mask — dots are drawn only where alpha >= ALPHA_MIN, so the background stays a
   clean cobalt field. gen-dots.py reads the same file at the same threshold, which is
   what stops the plate and the canvas from drifting apart. */
(() => {
  'use strict';
  const img = document.querySelector('.hero__portrait-frame img');
  if (!img || !window.requestAnimationFrame) return;
  if (window.matchMedia('(prefers-reduced-motion: reduce)').matches) return;

  const GAP = 8, BASE_R = 2, CULL = 0.1, K = 0.02, STEP = 0.03, TAU = Math.PI * 2;
  const ALPHA_MIN = 128;                 // in step with tools/cutout.py and gen-dots.py
  const FILL = '#163a6b', DOT = '#f4f7fb', SRC = 'assets/img/me.webp';
  const w = img.getAttribute('width') | 0 || 528;
  const h = img.getAttribute('height') | 0 || 528;

  // sample off-screen: never read back from the visible canvas, that forces software raster
  const off = document.createElement('canvas');
  off.width = w; off.height = h;
  const octx = off.getContext('2d', { willReadFrequently: true });

  const canvas = document.createElement('canvas');
  canvas.width = w; canvas.height = h;
  canvas.setAttribute('role', 'img');
  canvas.setAttribute('aria-label', img.alt || 'Portrait');
  const ctx = canvas.getContext('2d');

  let px = null, t = 0, running = false, raf = 0;

  const draw = () => {
    ctx.fillStyle = FILL;
    ctx.fillRect(0, 0, w, h);
    ctx.fillStyle = DOT;
    for (let y = 0; y < h; y += GAP) {
      for (let x = 0; x < w; x += GAP) {
        const i = (y * w + x) * 4;
        if (px[i + 3] < ALPHA_MIN) continue;          // outside the subject: leave the field
        const b = (px[i] + px[i + 1] + px[i + 2]) / 765;
        if (b <= CULL) continue;
        const wave = Math.sin(x * K + y * K - t) * 0.5 + 0.5;
        ctx.beginPath();
        ctx.arc(x, y, b * BASE_R * (0.8 + 0.4 * wave), 0, TAU);
        ctx.fill();
      }
    }
  };

  const frame = () => { draw(); t += STEP; raf = running ? requestAnimationFrame(frame) : 0; };
  const start = () => { if (px && !running) { running = true; raf = requestAnimationFrame(frame); } };
  const stop = () => { running = false; if (raf) cancelAnimationFrame(raf); };

  const src = new Image();
  src.onload = () => {
    const ia = src.width / src.height, ca = w / h;      // the reference's cover-fit
    let rw, rh, ox, oy;
    if (ia > ca) { rh = h; rw = h * ia; ox = -(rw - w) / 2; oy = 0; }
    else { rw = w; rh = w / ia; ox = 0; oy = -(rh - h) / 2; }
    octx.drawImage(src, ox, oy, rw, rh);
    px = octx.getImageData(0, 0, w, h).data;

    img.hidden = true;                                  // swap only when the canvas is ready
    img.parentNode.insertBefore(canvas, img);
    draw();

    if ('IntersectionObserver' in window) {
      new IntersectionObserver(es => es.forEach(e => (e.isIntersecting ? start() : stop())),
        { threshold: 0 }).observe(canvas);
      document.addEventListener('visibilitychange', () => (document.hidden ? stop() : start()));
    } else {
      start();
    }
  };
  src.src = SRC;
})();
