/* reveal.js — scroll-triggered reveal via IntersectionObserver.
   Elements with [data-reveal] fade/slide in once when they enter the viewport and stay
   revealed. Optional [data-reveal-delay="120"] staggers siblings (ms).
   The hero and portrait do not use this — they carry no [data-reveal], because their
   entrance is load-time (see home.css), not scroll-driven. */
(function () {
  var els = Array.prototype.slice.call(document.querySelectorAll('[data-reveal]'));

  if (!('IntersectionObserver' in window)) {
    els.forEach(function (el) { el.classList.add('in-view'); });
    return;
  }

  var reduceMotion = window.matchMedia('(prefers-reduced-motion: reduce)').matches;

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
})();
