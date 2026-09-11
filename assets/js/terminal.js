/* Types the terminal card out when it first scrolls into view, then leaves the
   finished transcript on screen. The transcript lives in the <pre>, so no-JS and
   prefers-reduced-motion both show the completed card with no animation at all.
   This is an animation ONLY - it never navigates. */
(() => {
  const pre = document.querySelector('.terminal pre');
  if (!pre || !window.requestAnimationFrame || !('IntersectionObserver' in window)) return;
  if (window.matchMedia('(prefers-reduced-motion: reduce)').matches) return;

  const CMD = /^([^\s$]+@[^\s:]+:[^\s$]*\$)\s+(.*)$/;   // "user@host:~$ command"
  const OK = /^[✓✔]/;                                    // the closing connected line
  const src = pre.textContent.split('\n');
  const esc = s => s.replace(/[&<>]/g, c => ({ '&': '&amp;', '<': '&lt;', '>': '&gt;' }[c]));
  const CUR = '<span class="cursor" aria-hidden="true"></span>';
  const wait = ms => new Promise(r => setTimeout(r, ms));

  const done = [];
  const render = live => { pre.innerHTML = done.join('') + live + CUR; };

  async function play() {
    // reserve the card's finished height before the first paint, otherwise the
    // card grows line by line as it types and pushes the page below it
    pre.style.minHeight = pre.getBoundingClientRect().height + 'px';
    for (const line of src) {
      const m = line.match(CMD);
      if (m) {
        for (let i = 1; i <= line.length; i++) {
          render('<span class="prompt">' + esc(m[1]) + '</span> ' + esc(line.slice(m[1].length + 1, i)));
          await wait(20);
        }
        done.push('<span class="prompt">' + esc(m[1]) + '</span> ' + esc(m[2]));
        render('');
      } else {
        done.push('<span class="' + (OK.test(line) ? 'ok' : 'out') + '">' + esc(line) + '</span>');
        render('');
      }
      await wait(line ? 240 : 90);
      done.push('\n');
    }
    if (done[done.length - 1] === '\n') done.pop();   // no trailing blank line
    render('');
  }

  const io = new IntersectionObserver((entries, self) => {
    if (!entries.some(e => e.isIntersecting)) return;
    self.disconnect();       // once
    play();
  }, { threshold: 0.35 });
  io.observe(pre);
})();
