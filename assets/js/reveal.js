/* reveal.js — scroll-triggered reveal via IntersectionObserver.
   Elements with [data-reveal] fade/slide in when they enter the viewport.
   Optional [data-reveal-delay="120"] staggers siblings (ms). */
(function () {
  var els = Array.prototype.slice.call(document.querySelectorAll('[data-reveal]'));

  if (!('IntersectionObserver' in window)) {
    els.forEach(function (el) { el.classList.add('in-view'); });
    return;
  }

  var reduceMotion = window.matchMedia('(prefers-reduced-motion: reduce)').matches;

  var start = function () {
  var observer = new IntersectionObserver(function (entries, obs) {
    entries.forEach(function (entry) {
      if (entry.isIntersecting) {
        var el = entry.target;
        var delay = el.getAttribute('data-reveal-delay');
        if (delay) el.style.setProperty('--reveal-delay', delay + 'ms');
        el.classList.add('in-view');
        obs.unobserve(el);
      }
    });
  }, { threshold: 0.12, rootMargin: '0px 0px -8% 0px' });

  els.forEach(function (el) {
    if (reduceMotion) {
      el.classList.add('in-view');
    } else {
      observer.observe(el);
    }
  });

  // P3: pause looping media for reduced-motion users
  if (reduceMotion) {
    Array.prototype.forEach.call(document.querySelectorAll('video[autoplay]'), function (v) {
      v.pause();
      v.removeAttribute('autoplay');
    });
  }
  };

  /* While the boot splash covers the page, observing is pointless: everything in the
     viewport would reveal behind the overlay and the hero would have already played
     by the time it lifts. Wait for the splash to hand over, then start. */
  if (document.documentElement.classList.contains('boot')) {
    window.addEventListener('boot:done', start, { once: true });
  } else {
    start();
  }
})();
