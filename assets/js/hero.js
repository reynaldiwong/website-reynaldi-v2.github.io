/* hero.js — JSON "character sheet" typewriter + live "playtime" counter.
   Faithful vanilla port of the original HeroJson motif. */
(function () {
  var root = document.getElementById('hero-json');
  if (!root) return;

  var START = '2022-08-01';
  var reduceMotion = window.matchMedia('(prefers-reduced-motion: reduce)').matches;

  function computeDuration() {
    var start = new Date(START).getTime();
    var diff = Math.max(0, Date.now() - start);
    var seconds = Math.floor((diff / 1000) % 60);
    var minutes = Math.floor((diff / (1000 * 60)) % 60);
    var hours = Math.floor((diff / (1000 * 60 * 60)) % 24);
    var daysTotal = Math.floor(diff / (1000 * 60 * 60 * 24));
    var years = Math.floor(daysTotal / 365);
    var remainingDays = daysTotal % 365;
    var months = Math.floor(remainingDays / 30);
    var days = remainingDays % 30;
    return { years: years, months: months, days: days, hours: hours, minutes: minutes, seconds: seconds };
  }

  // Token list: { text, type, key? } — key marks live "playtime" values.
  var tokens = [
    { text: '{', type: 'punctuation' },
    { text: '\n  ', type: 'plain' },
    { text: '"name"', type: 'key' }, { text: ': ', type: 'punctuation' },
    { text: '"Reynaldi Wong"', type: 'string' }, { text: ',', type: 'punctuation' },
    { text: '\n  ', type: 'plain' },
    { text: '"class"', type: 'key' }, { text: ': ', type: 'punctuation' },
    { text: '"DevOps Engineer"', type: 'string' }, { text: ',', type: 'punctuation' },
    { text: '\n  ', type: 'plain' },
    { text: '"origin"', type: 'key' }, { text: ': ', type: 'punctuation' },
    { text: '"Mechatronics Engineering"', type: 'string' }, { text: ',', type: 'punctuation' },
    { text: '\n  ', type: 'plain' },
    { text: '"playtime"', type: 'key' }, { text: ': ', type: 'punctuation' },
    { text: '{', type: 'punctuation' },
    { text: '\n    ', type: 'plain' },
    { text: '"years"', type: 'key' }, { text: ': ', type: 'punctuation' },
    { text: '0', type: 'value', key: 'years' }, { text: ',', type: 'punctuation' },
    { text: '\n    ', type: 'plain' },
    { text: '"months"', type: 'key' }, { text: ': ', type: 'punctuation' },
    { text: '0', type: 'value', key: 'months' }, { text: ',', type: 'punctuation' },
    { text: '\n    ', type: 'plain' },
    { text: '"days"', type: 'key' }, { text: ': ', type: 'punctuation' },
    { text: '0', type: 'value', key: 'days' }, { text: ',', type: 'punctuation' },
    { text: '\n    ', type: 'plain' },
    { text: '"hours"', type: 'key' }, { text: ': ', type: 'punctuation' },
    { text: '0', type: 'value', key: 'hours' }, { text: ',', type: 'punctuation' },
    { text: '\n    ', type: 'plain' },
    { text: '"minutes"', type: 'key' }, { text: ': ', type: 'punctuation' },
    { text: '0', type: 'value', key: 'minutes' }, { text: ',', type: 'punctuation' },
    { text: '\n    ', type: 'plain' },
    { text: '"seconds"', type: 'key' }, { text: ': ', type: 'punctuation' },
    { text: '00', type: 'value', key: 'seconds' },
    { text: '\n  ', type: 'plain' },
    { text: '}', type: 'punctuation' },
    { text: '\n', type: 'plain' },
    { text: '}', type: 'punctuation' }
  ];

  function pad(n) { return n < 10 ? '0' + n : String(n); }

  // Build span per token; live value spans are tracked by key.
  var liveSpans = {};
  var spans = tokens.map(function (t) {
    var s = document.createElement('span');
    s.className = 'json-' + t.type;
    if (t.key) {
      s.dataset.key = t.key;
      liveSpans[t.key] = s;
    }
    s.textContent = t.text;
    return s;
  });

  function tick() {
    var d = computeDuration();
    liveSpans.years.textContent = String(d.years);
    liveSpans.months.textContent = String(d.months);
    liveSpans.days.textContent = String(d.days);
    liveSpans.hours.textContent = String(d.hours);
    liveSpans.minutes.textContent = String(d.minutes);
    liveSpans.seconds.textContent = pad(d.seconds);
  }

  // Cursor span
  var cursor = document.createElement('span');
  cursor.className = 'cursor';
  cursor.textContent = '|';

  // Clear the static no-JS fallback before revealing over it.
  root.textContent = '';

  // Start live counter immediately (values visible behind the reveal).
  tick();
  setInterval(tick, 1000);

  if (reduceMotion) {
    spans.forEach(function (s) { root.appendChild(s); });
    root.appendChild(cursor);
    return;
  }

  // Typewriter reveal: append tokens one at a time.
  var i = 0;
  var speed = 26;
  function type() {
    if (i < spans.length) {
      root.appendChild(spans[i]);
      i++;
      // Punctuation & whitespace snap faster than strings/keys.
      var t = tokens[i - 1];
      var isFast = t.type === 'punctuation' || t.type === 'plain';
      setTimeout(type, isFast ? speed * 0.5 : speed);
    } else {
      root.appendChild(cursor);
    }
  }
  type();
})();
