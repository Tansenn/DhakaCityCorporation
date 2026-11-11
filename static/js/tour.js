(function () {
  var root = document.getElementById('pageTour');
  if (!root) return;
  var source = document.getElementById('tourSource');
  var spot = document.getElementById('tourSpot');
  var card = document.getElementById('tourCard');
  var arrow = document.getElementById('tourArrow');
  var countEl = document.getElementById('tourCount');
  var titleEl = document.getElementById('tourTitle');
  var textEl = document.getElementById('tourText');
  var btnPrev = document.getElementById('tourPrev');
  var btnNext = document.getElementById('tourNext');
  var btnSkip = document.getElementById('tourSkip');
  var btnSkipLink = document.getElementById('tourSkipLink');
  var replay = document.getElementById('tourReplay');

  var key = 'gzp_tour_' + (root.dataset.tour || 'page');
  var steps = [];
  var index = 0;
  var ticking = false;

  Array.prototype.forEach.call(source.children, function (li) {
    var el = document.querySelector(li.dataset.target);
    if (el) steps.push({ el: el, title: li.dataset.title, text: li.dataset.text });
  });

  function remember() {
    try { localStorage.setItem(key, 'done'); } catch (e) { /* private mode */ }
  }

  function isNew() {
    try { return localStorage.getItem(key) !== 'done'; } catch (e) { return true; }
  }

  function place() {
    var el = steps[index].el;
    var r = el.getBoundingClientRect();
    var vw = window.innerWidth;
    var vh = window.innerHeight;
    var pad = 6;
    var gap = 16;
    var edge = 12;
    var topEdge = document.querySelector('.topbar') ? 74 : edge;

    card.style.width = Math.min(344, vw - 24) + 'px';
    var cardW = card.offsetWidth;
    var cardH = card.offsetHeight;

    // A spotlight taller than the room left by the card would push the card
    // off-screen, so cap it and slide it so spot + card always fit.
    var spotH = Math.min(Math.max(r.height, 0), Math.max(120, vh - cardH - gap - topEdge - edge - 4));
    var spotTop = Math.max(topEdge, Math.min(r.top, vh - spotH - edge));
    spot.style.top = (spotTop - pad) + 'px';
    spot.style.left = (r.left - pad) + 'px';
    spot.style.width = Math.max(0, r.width + pad * 2) + 'px';
    spot.style.height = Math.max(0, spotH + pad * 2) + 'px';

    var belowTop = spotTop + spotH + gap;
    var aboveTop = spotTop - gap - cardH;
    var fitsBelow = belowTop + cardH <= vh - edge;
    var fitsAbove = aboveTop >= topEdge;
    var below = fitsBelow || !fitsAbove;
    var top = below ? belowTop : aboveTop;
    top = Math.max(topEdge, Math.min(top, vh - cardH - edge));
    var left = Math.max(edge, Math.min(r.left + r.width / 2 - cardW / 2, vw - cardW - edge));

    card.style.top = top + 'px';
    card.style.left = left + 'px';
    var tip = Math.max(20, Math.min(r.left + r.width / 2 - left, cardW - 20));
    arrow.style.left = (tip - 7) + 'px';
    arrow.className = 'tour-arrow ' + (below ? 'up' : 'down');
  }

  function queuePlace() {
    if (ticking) return;
    ticking = true;
    window.requestAnimationFrame(function () {
      ticking = false;
      if (!root.hidden) place();
    });
  }

  function show(i) {
    index = i;
    var step = steps[index];
    titleEl.textContent = step.title;
    textEl.textContent = step.text;
    countEl.textContent = (index + 1) + ' / ' + steps.length;
    btnPrev.hidden = index === 0;
    btnNext.textContent = index === steps.length - 1 ? btnNext.dataset.finish : btnNext.dataset.next;
    // Park the target just under the sticky topbar so the card has room below.
    var offset = document.querySelector('.topbar') ? 78 : 16;
    var targetTop = window.scrollY + step.el.getBoundingClientRect().top - offset;
    window.scrollTo({ top: Math.max(0, targetTop), behavior: 'smooth' });
    place();
    window.setTimeout(place, 320);
    window.setTimeout(place, 620);
    window.setTimeout(place, 1000);
    window.setTimeout(place, 1500);
    window.setTimeout(function () {
      // If smooth scrolling did not land (reduced motion, busy browser), jump.
      if (index === steps.indexOf(step)) {
        var now = step.el.getBoundingClientRect();
        if (now.top < 0 || now.top + 24 > window.innerHeight) {
          window.scrollTo({ top: Math.max(0, window.scrollY + now.top - offset), behavior: 'auto' });
          place();
        }
      }
    }, 700);
  }

  function start() {
    if (!steps.length) return;
    root.hidden = false;
    replay.hidden = true;
    document.body.classList.add('tour-open');
    window.addEventListener('scroll', queuePlace, { passive: true });
    window.addEventListener('resize', queuePlace);
    show(0);
  }

  function finish() {
    root.hidden = true;
    replay.hidden = false;
    document.body.classList.remove('tour-open');
    window.removeEventListener('scroll', queuePlace);
    window.removeEventListener('resize', queuePlace);
    remember();
  }

  btnNext.addEventListener('click', function () {
    if (index === steps.length - 1) { finish(); return; }
    show(index + 1);
  });
  btnPrev.addEventListener('click', function () {
    if (index > 0) show(index - 1);
  });
  btnSkip.addEventListener('click', finish);
  btnSkipLink.addEventListener('click', finish);
  replay.addEventListener('click', function () {
    try { localStorage.removeItem(key); } catch (e) { /* ignore */ }
    start();
  });

  document.addEventListener('keydown', function (event) {
    if (root.hidden) return;
    if (event.key === 'Escape') { finish(); }
    else if (event.key === 'ArrowRight') { btnNext.click(); }
    else if (event.key === 'ArrowLeft' && index > 0) { show(index - 1); }
  });

  replay.hidden = false;
  if (isNew()) {
    window.setTimeout(start, 800);
  }
})();
