/* hero.js — measures where the hero portrait must start so that it begins dead centre in the
   viewport and then travels right into its column (see --portrait-from in home.css).

   Measured rather than hard-coded because the distance depends on the layout, and measured
   with offsetLeft/offsetWidth rather than getBoundingClientRect, because the frame is
   already carrying the animation's transform by the time this runs - a rect would report the
   transformed position and feed the offset back into itself. offsetLeft is a layout value, so
   it stays honest. The CSS carries a -270px fallback for the case this never runs. */
(function () {
  var frame = document.querySelector('.hero__portrait-frame');
  if (!frame) return;

  function place() {
    var host = frame.offsetParent || frame.parentElement;
    if (!host || !frame.offsetWidth) return;
    var hostRect = host.getBoundingClientRect();
    var left = hostRect.left + frame.offsetLeft;
    var dx = (window.innerWidth / 2) - (left + frame.offsetWidth / 2);
    frame.style.setProperty('--portrait-from', Math.round(dx) + 'px');
  }

  place();
  window.addEventListener('resize', place);
})();
