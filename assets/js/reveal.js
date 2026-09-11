/* reveal.js — scroll-triggered reveal via IntersectionObserver.
   Elements with [data-reveal] fade/slide/focus in when they enter the viewport, and
   reverse back out when the page scrolls up past them.
   Optional [data-reveal-delay="120"] staggers siblings (ms). */
(function () {
  var els = Array.prototype.slice.call(document.querySelectorAll('[data-reveal]'));

  if (!('IntersectionObserver' in window)) {
    els.forEach(function (el) { el.classList.add('in-view'); });
    return;
  }

  var reduceMotion = window.matchMedia('(prefers-reduced-motion: reduce)').matches;
  if (reduceMotion) {
    els.forEach(function (el) { el.classList.add('in-view'); });
    // P3: pause looping media for reduced-motion users
    Array.prototype.forEach.call(document.querySelectorAll('video[autoplay]'), function (v) {
      v.pause();
      v.removeAttribute('autoplay');
    });
    return;
  }

  function reveal(el) {
    var delay = el.getAttribute('data-reveal-delay');
    if (delay) el.style.setProperty('--reveal-delay', delay + 'ms');
    el.classList.add('in-view');
  }
  function hide(el) {
    el.classList.remove('in-view');
  }

  // Reveal on entry. This is the only thing IntersectionObserver can do here: once an
  // element has left the viewport its intersection state stops changing, so the observer
  // never fires again for it and can NOT drive the reverse.
  var observer = new IntersectionObserver(function (entries) {
    entries.forEach(function (entry) {
      if (entry.isIntersecting) reveal(entry.target);
    });
  }, { threshold: 0.12, rootMargin: '0px 0px -8% 0px' });

  els.forEach(function (el) { observer.observe(el); });

  // The reverse: on an upward scroll, hand back everything already above the viewport.
  // Done as a sweep rather than through the observer, because (above) the observer is
  // silent for those elements. Scrolling down only ever reveals, so a downward pass can
  // never un-reveal something you have already read - that asymmetry is the whole effect.
  var lastY = window.pageYOffset;
  var goingUp = false;
  var queued = false;

  function onFrame() {
    queued = false;
    var y = window.pageYOffset;
    goingUp = y < lastY;
    lastY = y;
    if (!goingUp) return;
    // Read every rect before touching any class, so this costs one layout, not N.
    var above = els.filter(function (el) {
      return el.classList.contains('in-view') && el.getBoundingClientRect().bottom <= 0;
    });
    for (var i = 0; i < above.length; i++) hide(above[i]);
  }

  window.addEventListener('scroll', function () {
    if (queued) return;
    queued = true;
    requestAnimationFrame(onFrame);
  }, { passive: true });
})();
