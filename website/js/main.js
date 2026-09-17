/* ============================================================
   APEX PERFORMANCE — main.js
   Vanilla JS, no dependencies, no build step.
   Everything degrades gracefully: with JS disabled the site is
   still fully readable and the contact form still submits.
   ============================================================ */
(function () {
  'use strict';

  var reduced = window.matchMedia('(prefers-reduced-motion: reduce)').matches;
  var $  = function (s, c) { return (c || document).querySelector(s); };
  var $$ = function (s, c) { return Array.prototype.slice.call((c || document).querySelectorAll(s)); };

  /* ---------- 1. NAV: sticky state + hide-on-scroll-down ---------- */
  (function nav() {
    var bar = $('.nav');
    if (!bar) return;
    var last = window.scrollY;
    var ticking = false;

    function update() {
      var y = window.scrollY;
      bar.classList.toggle('is-stuck', y > 24);
      // Hide when scrolling down past the fold, show on any upward scroll.
      if (!document.body.classList.contains('menu-open')) {
        bar.classList.toggle('is-hidden', y > 420 && y > last + 4);
      }
      last = y;
      ticking = false;
    }
    update();
    window.addEventListener('scroll', function () {
      if (!ticking) { ticking = true; requestAnimationFrame(update); }
    }, { passive: true });
  })();

  /* ---------- 2. MOBILE MENU ---------- */
  (function menu() {
    var btn  = $('.nav__toggle');
    var menu = $('#site-menu');
    if (!btn || !menu) return;

    var links = $$('.menu__link', menu);
    var lastFocus = null;

    function setOpen(open) {
      btn.setAttribute('aria-expanded', String(open));
      menu.classList.toggle('is-open', open);
      menu.setAttribute('aria-hidden', String(!open));
      document.body.classList.toggle('menu-open', open);
      // Stagger the link reveal
      links.forEach(function (l, i) { l.style.transitionDelay = open ? (90 + i * 55) + 'ms' : '0ms'; });
      if (open) { lastFocus = document.activeElement; links[0] && links[0].focus(); }
      else if (lastFocus) { lastFocus.focus(); }
    }

    btn.addEventListener('click', function () {
      setOpen(btn.getAttribute('aria-expanded') !== 'true');
    });
    menu.addEventListener('click', function (e) { if (e.target.closest('a')) setOpen(false); });
    document.addEventListener('keydown', function (e) {
      if (e.key === 'Escape' && btn.getAttribute('aria-expanded') === 'true') setOpen(false);
    });
    // Simple focus trap while the overlay is open
    menu.addEventListener('keydown', function (e) {
      if (e.key !== 'Tab') return;
      var f = $$('a, button', menu).filter(function (el) { return el.offsetParent !== null; });
      if (!f.length) return;
      var first = f[0], lastEl = f[f.length - 1];
      if (e.shiftKey && document.activeElement === first) { e.preventDefault(); lastEl.focus(); }
      else if (!e.shiftKey && document.activeElement === lastEl) { e.preventDefault(); first.focus(); }
    });
    setOpen(false);
  })();

  /* ---------- 3. SPLIT TEXT into masked lines ----------
     Wraps each visual line of [data-split] in .ln > span so it can
     slide up from behind a mask. Re-runs on resize (line breaks move). */
  (function split() {
    var targets = $$('[data-split]');
    if (!targets.length || reduced) return;

    targets.forEach(function (el) { el.dataset.raw = el.innerHTML; });

    function build(el) {
      el.innerHTML = el.dataset.raw;
      // Wrap every word so we can measure where lines break. Each word
      // remembers the inline wrapper it came from (e.g. <span class="thin">)
      // so styling survives the rebuild. One level of nesting is supported,
      // which covers every use on this site.
      var formats = [];
      function fmtIndex(node, root) {
        var parent = node.parentNode;
        if (!parent || parent === root) return -1;
        var key = parent.tagName + '|' + (parent.className || '');
        var found = formats.indexOf(key);
        if (found === -1) { formats.push(key); found = formats.length - 1; }
        return found;
      }

      var walker = document.createTreeWalker(el, NodeFilter.SHOW_TEXT, null);
      var nodes = [], n;
      while ((n = walker.nextNode())) nodes.push(n);

      nodes.forEach(function (node) {
        if (!node.nodeValue.trim()) return;
        var fi = fmtIndex(node, el);
        var frag = document.createDocumentFragment();
        node.nodeValue.split(/(\s+)/).forEach(function (part) {
          if (!part.trim()) { frag.appendChild(document.createTextNode(part)); return; }
          var w = document.createElement('span');
          w.className = 'wd';
          w.style.display = 'inline-block';
          w.setAttribute('data-fmt', fi);
          w.textContent = part;
          frag.appendChild(w);
        });
        node.parentNode.replaceChild(frag, node);
      });

      // Group words by vertical offset — each distinct offset is one visual line.
      var words = $$('.wd', el), lines = [], currentTop = null, bucket = null;
      words.forEach(function (w) {
        var top = Math.round(w.offsetTop);
        if (currentTop === null || Math.abs(top - currentTop) > 4) {
          bucket = []; lines.push(bucket); currentTop = top;
        }
        bucket.push(w);
      });
      if (!lines.length) return;

      function openTag(key) {
        var bits = key.split('|');
        return '<' + bits[0].toLowerCase() + (bits[1] ? ' class="' + bits[1] + '"' : '') + '>';
      }
      function closeTag(key) { return '</' + key.split('|')[0].toLowerCase() + '>'; }
      function esc(t) {
        return t.replace(/&/g, '&amp;').replace(/</g, '&lt;').replace(/>/g, '&gt;');
      }

      var html = lines.map(function (line) {
        var out = '', openFmt = -1;
        line.forEach(function (w, idx) {
          var f = parseInt(w.getAttribute('data-fmt'), 10);
          if (f !== openFmt) {
            if (openFmt !== -1) out += closeTag(formats[openFmt]);
            if (f !== -1) out += openTag(formats[f]);
            openFmt = f;
          }
          out += (idx ? ' ' : '') + esc(w.textContent);
        });
        if (openFmt !== -1) out += closeTag(formats[openFmt]);
        return '<span class="ln"><span>' + out + '</span></span>';
      }).join('');
      el.innerHTML = html;

      $$('.ln > span', el).forEach(function (s, i) { s.style.setProperty('--d', (i * 85) + 'ms'); });
    }

    function buildAll() { targets.forEach(build); }
    buildAll();

    var t;
    window.addEventListener('resize', function () {
      clearTimeout(t);
      t = setTimeout(function () {
        var wasIn = targets.map(function (el) { return el.classList.contains('is-in'); });
        buildAll();
        targets.forEach(function (el, i) { if (wasIn[i]) el.classList.add('is-in'); });
      }, 220);
    });
  })();

  /* ---------- 4. SCROLL REVEAL ---------- */
  (function reveal() {
    var items = $$('[data-reveal], [data-split]');
    if (!items.length) return;

    if (reduced || !('IntersectionObserver' in window)) {
      items.forEach(function (el) { el.classList.add('is-in'); });
      return;
    }

    var io = new IntersectionObserver(function (entries) {
      entries.forEach(function (entry) {
        if (!entry.isIntersecting) return;
        entry.target.classList.add('is-in');
        io.unobserve(entry.target);
      });
    }, { rootMargin: '0px 0px -12% 0px', threshold: 0.08 });

    items.forEach(function (el, i) {
      // Stagger siblings inside the same [data-stagger] parent
      var parent = el.closest('[data-stagger]');
      if (parent) {
        var sibs = $$('[data-reveal]', parent);
        el.style.setProperty('--d', (sibs.indexOf(el) * 90) + 'ms');
      }
      io.observe(el);
    });
  })();

  /* ---------- 5. SCROLL PROGRESS BAR ---------- */
  (function progress() {
    var bar = $('.progress');
    if (!bar) return;
    var ticking = false;
    function update() {
      var h = document.documentElement.scrollHeight - window.innerHeight;
      bar.style.setProperty('--p', h > 0 ? Math.min(window.scrollY / h, 1) : 0);
      ticking = false;
    }
    window.addEventListener('scroll', function () {
      if (!ticking) { ticking = true; requestAnimationFrame(update); }
    }, { passive: true });
    update();
  })();

  /* ---------- 6. HERO PARALLAX ---------- */
  (function parallax() {
    var img = $('[data-parallax]');
    if (!img || reduced) return;
    var ticking = false;
    function update() {
      var y = window.scrollY;
      if (y < window.innerHeight * 1.4) {
        img.style.transform = 'translate3d(0,' + (y * 0.16).toFixed(2) + 'px,0) scale(1.06)';
      }
      ticking = false;
    }
    window.addEventListener('scroll', function () {
      if (!ticking) { ticking = true; requestAnimationFrame(update); }
    }, { passive: true });
    update();
  })();

  /* ---------- 7. CUSTOM CURSOR + MAGNETIC BUTTONS ---------- */
  (function cursor() {
    if (reduced || window.matchMedia('(pointer: coarse)').matches) return;

    var dot = document.createElement('div');
    dot.className = 'cursor';
    dot.setAttribute('aria-hidden', 'true');
    document.body.appendChild(dot);

    var tx = 0, ty = 0, cx = 0, cy = 0;
    document.addEventListener('mousemove', function (e) {
      tx = e.clientX; ty = e.clientY;
      dot.classList.add('is-on');
    }, { passive: true });
    document.addEventListener('mouseleave', function () { dot.classList.remove('is-on'); });

    (function loop() {
      cx += (tx - cx) * 0.18;
      cy += (ty - cy) * 0.18;
      dot.style.transform = 'translate3d(' + cx.toFixed(2) + 'px,' + cy.toFixed(2) + 'px,0)';
      requestAnimationFrame(loop);
    })();

    var hot = 'a, button, input, textarea, select, .compare, [data-hot]';
    document.addEventListener('mouseover', function (e) {
      if (e.target.closest(hot)) dot.classList.add('is-hot');
    });
    document.addEventListener('mouseout', function (e) {
      if (e.target.closest(hot)) dot.classList.remove('is-hot');
    });

    // Magnetic pull on primary buttons
    $$('[data-magnetic]').forEach(function (el) {
      var raf = null;
      el.addEventListener('mousemove', function (e) {
        var r = el.getBoundingClientRect();
        var mx = e.clientX - r.left - r.width / 2;
        var my = e.clientY - r.top - r.height / 2;
        cancelAnimationFrame(raf);
        raf = requestAnimationFrame(function () {
          el.style.transform = 'translate(' + (mx * 0.22).toFixed(2) + 'px,' + (my * 0.3).toFixed(2) + 'px)';
        });
      });
      el.addEventListener('mouseleave', function () {
        cancelAnimationFrame(raf);
        el.style.transition = 'transform .5s cubic-bezier(.22,1,.36,1)';
        el.style.transform = '';
        setTimeout(function () { el.style.transition = ''; }, 500);
      });
    });
  })();

  /* ---------- 8. ANIMATED COUNTERS ---------- */
  (function counters() {
    var nums = $$('[data-count]');
    if (!nums.length) return;

    function run(el) {
      var target = parseFloat(el.dataset.count);
      var dec = (el.dataset.decimals | 0);
      if (reduced || isNaN(target)) { el.textContent = target.toFixed(dec); return; }
      var start = performance.now(), dur = 1400;
      (function tick(now) {
        var p = Math.min((now - start) / dur, 1);
        var eased = 1 - Math.pow(1 - p, 3);          // easeOutCubic
        el.textContent = (target * eased).toFixed(dec);
        if (p < 1) requestAnimationFrame(tick);
      })(start);
    }

    if (!('IntersectionObserver' in window)) { nums.forEach(run); return; }
    var io = new IntersectionObserver(function (entries) {
      entries.forEach(function (en) {
        if (!en.isIntersecting) return;
        run(en.target);
        io.unobserve(en.target);
      });
    }, { threshold: 0.6 });
    nums.forEach(function (el) { io.observe(el); });
  })();

  /* ---------- 9. FAQ ACCORDION ---------- */
  (function faq() {
    var qs = $$('.faq__q');
    if (!qs.length) return;
    qs.forEach(function (q) {
      q.addEventListener('click', function () {
        var open = q.getAttribute('aria-expanded') === 'true';
        // Comment out the next 3 lines to allow multiple panels open at once.
        qs.forEach(function (o) {
          if (o !== q) o.setAttribute('aria-expanded', 'false');
        });
        q.setAttribute('aria-expanded', String(!open));
      });
    });
  })();

  /* ---------- 10. BEFORE / AFTER SLIDER ---------- */
  (function compare() {
    $$('.compare').forEach(function (box) {
      var range = $('.compare__range', box);
      if (!range) return;

      function set(v) {
        box.style.setProperty('--pos', v + '%');
        range.setAttribute('aria-valuenow', Math.round(v));
      }
      set(range.value || 50);

      range.addEventListener('input', function () { set(range.value); });

      // Drag anywhere on the image, not just the (invisible) range thumb
      function fromPointer(e) {
        var r = box.getBoundingClientRect();
        var x = ((e.clientX - r.left) / r.width) * 100;
        var v = Math.max(0, Math.min(100, x));
        range.value = v;
        set(v);
      }
      var dragging = false;
      box.addEventListener('pointerdown', function (e) {
        dragging = true;
        box.setPointerCapture(e.pointerId);
        fromPointer(e);
      });
      box.addEventListener('pointermove', function (e) { if (dragging) fromPointer(e); });
      box.addEventListener('pointerup',     function () { dragging = false; });
      box.addEventListener('pointercancel', function () { dragging = false; });
    });
  })();

  /* ---------- 11. APPLICATION FORM (apply.html) ----------
     One short page. Inline validation, localStorage autosave so a
     half-filled form survives a closed tab, and a fetch submit that
     swaps in a confirmation panel instead of reloading the page. */
  (function applyForm() {
    var form = $('#apply-form');
    if (!form) return;

    var submitBtn = $('#apply-submit');
    var statusEl  = $('#apply-status');
    var savedNote = $('#saved-note');
    var donePanel = $('#apply-done');
    var KEY = 'apex-apply-el-v1';

    var checks = {
      required: function (v) { return v.trim().length > 0 || 'Το πεδίο είναι υποχρεωτικό.'; },
      email:    function (v) { return /^[^\s@]+@[^\s@]+\.[^\s@]{2,}$/.test(v.trim()) || 'Συμπλήρωσε έγκυρο email.'; },
      checked:  function (v, el) { return el.checked || 'Χρειάζεται η συγκατάθεσή σου για να συνεχίσουμε.'; }
    };

    function slot(id) { return document.getElementById(id + '-error'); }

    function validateField(el) {
      var rule = checks[el.dataset.validate];
      if (!rule) return true;
      var res = rule(el.value, el);
      var ok = res === true;
      el.setAttribute('aria-invalid', String(!ok));
      var s = slot(el.id);
      if (s) s.textContent = ok ? '' : res;
      return ok;
    }

    function validateGroups() {
      var ok = true;
      $$('[data-required-group]', form).forEach(function (g) {
        var name = g.getAttribute('data-required-group');
        var picked = form.querySelector('input[name="' + name + '"]:checked');
        var s = slot(name);
        if (s) s.textContent = picked ? '' : 'Διάλεξε μία επιλογή.';
        if (!picked) ok = false;
      });
      return ok;
    }

    $$('[data-validate]', form).forEach(function (el) {
      el.addEventListener('blur',   function () { if (el.value.trim() || el.type === 'checkbox') validateField(el); });
      el.addEventListener('input',  function () { if (el.getAttribute('aria-invalid') === 'true') validateField(el); });
      el.addEventListener('change', function () { if (el.type === 'checkbox') validateField(el); });
    });
    $$('[data-required-group] input', form).forEach(function (el) {
      el.addEventListener('change', function () { var s = slot(el.name); if (s) s.textContent = ''; });
    });

    /* --- autosave --- */
    var timer;
    function save() {
      try {
        var out = {};
        new FormData(form).forEach(function (v, k) {
          if (k.charAt(0) === '_') return;
          if (out[k] === undefined) out[k] = v;
          else if (Array.isArray(out[k])) out[k].push(v);
          else out[k] = [out[k], v];
        });
        localStorage.setItem(KEY, JSON.stringify(out));
        if (savedNote) {
          savedNote.classList.add('is-on');
          clearTimeout(timer);
          timer = setTimeout(function () { savedNote.classList.remove('is-on'); }, 1600);
        }
      } catch (e) { /* private mode or blocked storage — not fatal */ }
    }

    function restore() {
      var raw;
      try { raw = localStorage.getItem(KEY); } catch (e) { return; }
      if (!raw) return;
      var data;
      try { data = JSON.parse(raw); } catch (e) { return; }
      Object.keys(data).forEach(function (k) {
        var vals = [].concat(data[k]);
        $$('[name]', form).forEach(function (el) {
          if (el.name !== k) return;
          if (el.type === 'checkbox' || el.type === 'radio') {
            if (vals.indexOf(el.value) !== -1) el.checked = true;
          } else if (vals[0] !== undefined) {
            el.value = vals[0];
          }
        });
      });
    }

    form.addEventListener('input',  function () { clearTimeout(timer); timer = setTimeout(save, 600); });
    form.addEventListener('change', save);

    function say(msg, state) {
      if (!statusEl) return;
      statusEl.hidden = false;
      statusEl.dataset.state = state;
      statusEl.textContent = msg;
    }

    form.addEventListener('submit', function (e) {
      e.preventDefault();

      var trap = form.querySelector('[name="_gotcha"]');
      if (trap && trap.value) return;

      var ok = true;
      $$('[data-validate]', form).forEach(function (el) { if (!validateField(el)) ok = false; });
      if (!validateGroups()) ok = false;

      if (!ok) {
        say('Έλεγξε τα πεδία που επισημαίνονται και δοκίμασε ξανά.', 'err');
        var bad = form.querySelector('[aria-invalid="true"]');
        if (bad) { bad.focus(); bad.scrollIntoView({ block: 'center', behavior: reduced ? 'auto' : 'smooth' }); }
        return;
      }

      var action = form.getAttribute('action') || '';
      if (!action || action.indexOf('REPLACE_WITH') !== -1) {
        say('Demo mode: δεν έχει συνδεθεί endpoint ακόμη. Δες το README.md → «Σύνδεση της φόρμας». Οι απαντήσεις σου είναι αποθηκευμένες σε αυτόν τον browser.', 'err');
        return;
      }

      submitBtn.disabled = true;
      var label = submitBtn.textContent;
      submitBtn.textContent = 'Αποστολή…';
      say('Γίνεται αποστολή…', 'ok');

      fetch(action, { method: 'POST', body: new FormData(form), headers: { Accept: 'application/json' } })
        .then(function (r) {
          if (!r.ok) throw new Error('Request failed: ' + r.status);
          try { localStorage.removeItem(KEY); } catch (err) {}
          form.style.display = 'none';
          if (donePanel) {
            donePanel.classList.add('is-on');
            donePanel.setAttribute('tabindex', '-1');
            donePanel.focus({ preventScroll: true });
            donePanel.scrollIntoView({ block: 'start', behavior: reduced ? 'auto' : 'smooth' });
          }
        })
        .catch(function () {
          say('Κάτι πήγε στραβά. Οι απαντήσεις σου είναι αποθηκευμένες — δοκίμασε ξανά ή στείλε email στο [EMAIL ΣΟΥ].', 'err');
          submitBtn.disabled = false;
          submitBtn.textContent = label;
        });
    });

    restore();
  })();

  /* ---------- 12. CURRENT YEAR ---------- */
  $$('[data-year]').forEach(function (el) { el.textContent = new Date().getFullYear(); });

})();
