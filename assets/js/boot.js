/* boot.js — the terminal splash.
   Types the short transcript in the markup, then lifts the overlay and marks the
   session booted. A click or any key skips it, and skipping still marks the session
   so the splash doesn't return on the next page.
   
   Nothing here is load-bearing: the overlay is only visible while `html.boot` is set,
   which the inline <head> gate removes on its own after 6s if this file never runs.
   No-JS and prefers-reduced-motion never see the splash at all. */
(() => {
  const splash = document.getElementById('splash');
  if (!splash) return;
  const pre = splash.querySelector('pre');

  const release = () => {
    document.documentElement.classList.remove('boot');
    window.dispatchEvent(new Event('boot:done'));   // reveal.js starts here
    try { sessionStorage.setItem('booted', '1'); } catch (e) {}
  };

  if (!pre || !window.requestAnimationFrame) { release(); return; }

  const CMD = /^([^\s$]+@[^\s:]+:[^\s$]*\$)\s+(.*)$/;   // "user@host:~$ command"
  const OK = /^[✓✔]/;                                    // the closing connected line
  const src = pre.textContent.split('\n');
  const esc = s => s.replace(/[&<>]/g, c => ({ '&': '&amp;', '<': '&lt;', '>': '&gt;' }[c]));
  const CUR = '<span class="cursor" aria-hidden="true"></span>';
  const wait = ms => new Promise(r => setTimeout(r, ms));

  const out = [];
  const render = live => { pre.innerHTML = out.join('') + live + CUR; };

  let over = false;
  const finish = () => {
    if (over) return;
    over = true;
    release();                                   // the site fades in behind the splash
    splash.classList.add('splash--out');
    setTimeout(() => splash.remove(), 400);
  };

  async function play() {
    // reserve the finished height so the card doesn't grow line by line
    pre.style.minHeight = pre.getBoundingClientRect().height + 'px';
    for (const line of src) {
      if (over) return;
      const m = line.match(CMD);
      if (m) {
        for (let i = 1; i <= line.length; i++) {
          if (over) return;
          render('<span class="prompt">' + esc(m[1]) + '</span> ' + esc(line.slice(m[1].length + 1, i)));
          await wait(12);
        }
        out.push('<span class="prompt">' + esc(m[1]) + '</span> ' + esc(m[2]));
        render('');
      } else {
        out.push('<span class="' + (OK.test(line) ? 'ok' : 'out') + '">' + esc(line) + '</span>');
        render('');
      }
      await wait(line ? 90 : 50);
      out.push('\n');
    }
    if (out[out.length - 1] === '\n') out.pop();   // no trailing blank line
    render('');
    await wait(250);
    finish();
  }

  window.addEventListener('keydown', finish);
  window.addEventListener('pointerdown', finish);
  play();
})();
