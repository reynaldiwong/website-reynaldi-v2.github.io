/* nav.js — sticky nav state, scroll progress bar, mobile drawer. */
(function () {
  var nav = document.querySelector('.nav');
  var toggle = document.querySelector('.nav__toggle');
  var drawer = document.querySelector('.drawer');
  var progress = document.querySelector('.scroll-progress');

  /* Scroll progress + nav background state */
  function onScroll() {
    var top = window.scrollY || document.documentElement.scrollTop;
    if (nav) nav.classList.toggle('is-scrolled', top > 10);

    if (progress) {
      var doc = document.documentElement;
      var max = doc.scrollHeight - doc.clientHeight;
      var pct = max > 0 ? (top / max) * 100 : 0;
      progress.style.width = pct + '%';
    }
  }

  /* Mobile drawer */
  function setDrawer(open) {
    if (!drawer || !toggle) return;
    drawer.classList.toggle('is-open', open);
    drawer.inert = !open;               // remove off-canvas links from tab/a11y order
    toggle.setAttribute('aria-expanded', open ? 'true' : 'false');
    toggle.setAttribute('aria-label', open ? 'Close menu' : 'Open menu');
    document.body.style.overflow = open ? 'hidden' : '';
  }

  if (toggle) {
    toggle.addEventListener('click', function () {
      setDrawer(!drawer.classList.contains('is-open'));
    });
  }

  /* Close drawer on link tap */
  if (drawer) {
    drawer.querySelectorAll('a').forEach(function (a) {
      a.addEventListener('click', function () { setDrawer(false); });
    });
  }

  /* Close drawer on Escape */
  document.addEventListener('keydown', function (e) {
    if (e.key === 'Escape') setDrawer(false);
  });

  window.addEventListener('scroll', onScroll, { passive: true });
  onScroll();
})();
