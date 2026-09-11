/* hero.js — the two parts of the hero intro that CSS cannot express on its own.
   1. The portrait starts frozen on the middle of the screen, then travels right. The
      distance is measured rather than derived from cqw, because "the middle of the screen"
      is a fact about the layout: cqw with no explicit query container resolves against the
      viewport (-360px at 1440) and would start the portrait well left of centre.
   2. The name types itself out. Typing makes text grow, so the h1's own height AND width are
      measured and pinned before the first character is removed - pinning width alone would
      still let the box collapse from two lines to one and drop the role text up the page.
   Both are skipped for prefers-reduced-motion. */
(function () {
  var reduce = window.matchMedia('(prefers-reduced-motion: reduce)').matches;
  var frame = document.querySelector('.hero__portrait-frame');
  var name = document.querySelector('.hero__name');

  /* 1. where "the middle of the screen" is, for the portrait's start */
  if (frame) {
    var place = function () {
      var host = frame.offsetParent || frame.parentElement;
      if (!host || !frame.offsetWidth) return;
      // offsetLeft/offsetWidth, not a rect: the frame already carries the animation's
      // transform, and a rect would report that transformed position back into the offset.
      var left = host.getBoundingClientRect().left + frame.offsetLeft;
      frame.style.setProperty('--portrait-from',
        Math.round((window.innerWidth / 2) - (left + frame.offsetWidth / 2)) + 'px');
    };
    place();
    window.addEventListener('resize', place);
  }

  if (!name) return;

  /* 2. the typewriter */
  var FULL = name.textContent.trim().replace(/\s+/g, ' ');
  if (reduce) { name.textContent = FULL; return; }        // static name, no caret

  var box = name.getBoundingClientRect();
  // Reserve the room the full name needs before typing shrinks it to nothing. Both axes:
  // pinning height alone still lets the box collapse from two lines to one, and pinning
  // width alone would let the box grow. min() keeps the reservation from forcing the h1
  // wider than its column if the window is later resized narrower.
  if (box.height) name.style.minHeight = Math.ceil(box.height) + 'px';
  name.style.minWidth = 'min(' + Math.ceil(name.offsetWidth) + 'px, 100%)';
  name.textContent = '';

  var START = 2300;   // begins as the portrait lands (2s freeze, then the travel)
  var STEP = 90;      // per character
  var i = 0;
  setTimeout(function tick() {
    name.textContent = FULL.slice(0, ++i);
    if (i < FULL.length) setTimeout(tick, STEP);
  }, START);
})();
