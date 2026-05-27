/* =====================================================
   Dream Analytica — Cyber Neon Micro-Interactions
   ===================================================== */

(function () {
  'use strict';

  const forceMotion = localStorage.getItem('neonForceMotion') === '1';
  const reduced = window.matchMedia('(prefers-reduced-motion: reduce)').matches && !forceMotion;
  const isTouch = window.matchMedia('(hover: none)').matches;
  /* iOS WebKit (incl. Brave) can crash/reload tabs under heavy canvas + rAF + resize storms */
  const isIOS =
    /iPhone|iPad|iPod/i.test(navigator.userAgent) ||
    (navigator.platform === 'MacIntel' && navigator.maxTouchPoints > 1);
  const liteHero = isIOS || reduced;

  document.documentElement.classList.add(reduced ? 'motion-reduced' : 'motion-on');
  if (isIOS) document.documentElement.classList.add('ios-lite');

  if (window.matchMedia('(prefers-reduced-motion: reduce)').matches && !forceMotion) {
    console.info(
      '[Dream Analytica] System "reduce motion" is ON — some effects are limited. ' +
      'To enable full motion: Windows Settings → Accessibility → Visual effects → Animation effects ON. ' +
      'Or run: localStorage.setItem("neonForceMotion","1"); location.reload();'
    );
  }

  // ------------------------------------------------------------------
  // Nav: scroll shrink + active link
  // ------------------------------------------------------------------
  function initNav() {
    const nav = document.querySelector('nav');
    if (!nav) return;

    const onScroll = () => {
      if (window.scrollY > 24) nav.classList.add('is-scrolled');
      else nav.classList.remove('is-scrolled');
    };
    window.addEventListener('scroll', onScroll, { passive: true });
    onScroll();

    // Active link highlight (mark nav-link / sidenav-link whose href matches current path)
    const path = window.location.pathname.replace(/\/+$/, '') || '/';
    document.querySelectorAll('.nav-link, .sidenav-link').forEach((a) => {
      const href = (a.getAttribute('href') || '').replace(/\/+$/, '') || '/';
      if (href === path) {
        a.classList.add('is-active');
        a.setAttribute('aria-current', 'page');
      }
    });
  }

  // ------------------------------------------------------------------
  // Reveal on scroll (replaces per-page IntersectionObservers)
  // ------------------------------------------------------------------
  function initReveal() {
    const elements = document.querySelectorAll('.animate, .reveal');
    if (!elements.length) return;

    if (!('IntersectionObserver' in window)) {
      elements.forEach((el) => el.classList.add('is-visible'));
      return;
    }

    const io = new IntersectionObserver(
      (entries) => {
        entries.forEach((entry) => {
          if (entry.isIntersecting) {
            entry.target.classList.add('is-visible');
            io.unobserve(entry.target);
          }
        });
      },
      { threshold: 0.1, rootMargin: '0px 0px -40px 0px' }
    );

    elements.forEach((el) => io.observe(el));
  }

  // ------------------------------------------------------------------
  // 3D tilt on .neon-card[data-tilt] and .feature-card
  // ------------------------------------------------------------------
  function initTilt() {
    if (reduced || isTouch) return;
    const cards = document.querySelectorAll('[data-tilt], .feature-card');
    cards.forEach((card) => {
      let raf = null;
      let rect = null;

      const onEnter = () => {
        rect = card.getBoundingClientRect();
      };

      const onMove = (e) => {
        if (!rect) rect = card.getBoundingClientRect();
        const x = (e.clientX - rect.left) / rect.width;
        const y = (e.clientY - rect.top) / rect.height;
        const rx = (0.5 - y) * 6;
        const ry = (x - 0.5) * 8;
        if (raf) cancelAnimationFrame(raf);
        raf = requestAnimationFrame(() => {
          card.style.transform = `perspective(900px) rotateX(${rx}deg) rotateY(${ry}deg) translateY(-4px)`;
        });
      };

      const onLeave = () => {
        if (raf) cancelAnimationFrame(raf);
        rect = null;
        card.style.transform = '';
      };

      card.addEventListener('mouseenter', onEnter);
      card.addEventListener('mousemove', onMove);
      card.addEventListener('mouseleave', onLeave);
    });
  }

  // ------------------------------------------------------------------
  // Animated counters [data-count]
  // ------------------------------------------------------------------
  function initCounters() {
    const counters = document.querySelectorAll('[data-count]');
    if (!counters.length) return;

    const animate = (el) => {
      const target = parseFloat(el.getAttribute('data-count'));
      const suffix = el.getAttribute('data-suffix') || '';
      const duration = parseInt(el.getAttribute('data-duration') || '1600', 10);
      const isFloat = !Number.isInteger(target);
      const startTime = performance.now();

      const step = (now) => {
        const t = Math.min(1, (now - startTime) / duration);
        const eased = 1 - Math.pow(1 - t, 3);
        const v = target * eased;
        el.textContent = (isFloat ? v.toFixed(1) : Math.floor(v).toLocaleString()) + suffix;
        if (t < 1) requestAnimationFrame(step);
        else el.textContent = (isFloat ? target.toFixed(1) : Math.floor(target).toLocaleString()) + suffix;
      };
      requestAnimationFrame(step);
    };

    if (!('IntersectionObserver' in window)) {
      counters.forEach(animate);
      return;
    }

    const io = new IntersectionObserver(
      (entries) => {
        entries.forEach((entry) => {
          if (entry.isIntersecting) {
            animate(entry.target);
            io.unobserve(entry.target);
          }
        });
      },
      { threshold: 0.4 }
    );
    counters.forEach((el) => io.observe(el));
  }

  // ------------------------------------------------------------------
  // Hero particle canvas
  // ------------------------------------------------------------------
  function initHeroParticles() {
    if (liteHero) return;
    const canvas = document.querySelector('.hero-canvas');
    if (!canvas) return;
    const ctx = canvas.getContext('2d', { alpha: true });
    if (!ctx) return;

    let particles = [];
    let w = 0;
    let h = 0;
    let lastW = 0;
    let lastH = 0;
    const dpr = Math.min(window.devicePixelRatio || 1, isTouch ? 1 : 1.5);
    let raf = null;
    let resizeTimer = null;
    let mouse = { x: -9999, y: -9999 };

    const stage = canvas.parentElement;
    if (!stage) return;

    const resize = () => {
      const rect = stage.getBoundingClientRect();
      const nextW = Math.max(1, Math.round(rect.width));
      const nextH = Math.max(1, Math.round(rect.height));
      if (nextW === lastW && nextH === lastH) return;
      lastW = nextW;
      lastH = nextH;
      w = nextW;
      h = nextH;
      canvas.width = Math.floor(w * dpr);
      canvas.height = Math.floor(h * dpr);
      canvas.style.width = w + 'px';
      canvas.style.height = h + 'px';
      ctx.setTransform(dpr, 0, 0, dpr, 0, 0);

      const cap = isTouch ? 45 : 110;
      const baseCount = Math.min(cap, Math.floor((w * h) / 16000));
      particles = new Array(baseCount).fill(0).map(() => ({
        x: Math.random() * w,
        y: Math.random() * h,
        vx: (Math.random() - 0.5) * 0.35,
        vy: (Math.random() - 0.5) * 0.35,
        r: Math.random() * 1.6 + 0.4,
        c: Math.random() > 0.5 ? '0,240,255' : '255,43,214',
      }));
    };

    const tick = () => {
      ctx.clearRect(0, 0, w, h);

      for (let i = 0; i < particles.length; i++) {
        const p = particles[i];
        p.x += p.vx;
        p.y += p.vy;
        if (p.x < 0 || p.x > w) p.vx *= -1;
        if (p.y < 0 || p.y > h) p.vy *= -1;

        if (!isTouch) {
          const dxm = p.x - mouse.x;
          const dym = p.y - mouse.y;
          const dm2 = dxm * dxm + dym * dym;
          if (dm2 < 14000) {
            const f = 1 - dm2 / 14000;
            const dist = Math.sqrt(dm2 + 0.01);
            p.x -= (dxm / dist) * f * 0.7;
            p.y -= (dym / dist) * f * 0.7;
          }
        }

        for (let j = i + 1; j < particles.length; j++) {
          const q = particles[j];
          const dx = p.x - q.x;
          const dy = p.y - q.y;
          const d2 = dx * dx + dy * dy;
          if (d2 < 13000) {
            const alpha = (1 - d2 / 13000) * 0.35;
            ctx.strokeStyle = `rgba(${p.c}, ${alpha})`;
            ctx.lineWidth = 0.6;
            ctx.beginPath();
            ctx.moveTo(p.x, p.y);
            ctx.lineTo(q.x, q.y);
            ctx.stroke();
          }
        }
      }

      for (const p of particles) {
        ctx.fillStyle = `rgba(${p.c}, 0.85)`;
        ctx.beginPath();
        ctx.arc(p.x, p.y, p.r, 0, Math.PI * 2);
        ctx.fill();
      }

      raf = requestAnimationFrame(tick);
    };

    const scheduleResize = () => {
      if (resizeTimer) clearTimeout(resizeTimer);
      resizeTimer = setTimeout(() => {
        resizeTimer = null;
        cancelAnimationFrame(raf);
        raf = null;
        resize();
        tick();
      }, 200);
    };

    const onMouse = (e) => {
      const rect = stage.getBoundingClientRect();
      mouse.x = e.clientX - rect.left;
      mouse.y = e.clientY - rect.top;
    };
    const onLeave = () => { mouse.x = -9999; mouse.y = -9999; };

    resize();
    tick();

    window.addEventListener('resize', scheduleResize, { passive: true });
    if (window.visualViewport) {
      window.visualViewport.addEventListener('resize', scheduleResize, { passive: true });
    }
    if (!isTouch) {
      stage.addEventListener('mousemove', onMouse);
      stage.addEventListener('mouseleave', onLeave);
    }

    const io = new IntersectionObserver((entries) => {
      entries.forEach((entry) => {
        if (entry.isIntersecting) {
          if (!raf) tick();
        } else {
          cancelAnimationFrame(raf);
          raf = null;
        }
      });
    });
    io.observe(stage);
  }

  // ------------------------------------------------------------------
  // Glitch random burst on .glitch-text
  // ------------------------------------------------------------------
  function initGlitch() {
    if (liteHero) return;
    const targets = document.querySelectorAll('.glitch-text');
    targets.forEach((el) => {
      setInterval(() => {
        if (Math.random() < 0.18) {
          el.classList.add('is-glitching');
          setTimeout(() => el.classList.remove('is-glitching'), 280);
        }
      }, 2200);
    });
  }

  // ------------------------------------------------------------------
  // Marquee — JS scroll (CSS keyframes + mask-image fail on Chrome desktop)
  // ------------------------------------------------------------------
  function startMarqueeJs(track) {
    if (track.dataset.marqueeJs === '1') return;
    track.dataset.marqueeJs = '1';
    track.classList.add('is-marquee-running');

    let offset = 0;
    let halfWidth = 0;
    let raf = null;
    let lastTime = 0;
    const pxPerSecond = reduced ? 28 : 52;

    const measure = () => {
      halfWidth = track.scrollWidth / 2;
      if (offset >= halfWidth && halfWidth > 0) offset = offset % halfWidth;
    };

    const step = (now) => {
      if (!lastTime) lastTime = now;
      const dt = Math.min(48, now - lastTime) / 1000;
      lastTime = now;

      if (halfWidth <= 0) measure();
      if (halfWidth > 0) {
        offset += pxPerSecond * dt;
        if (offset >= halfWidth) offset -= halfWidth;
        track.style.transform = 'translate3d(' + (-offset) + 'px,0,0)';
      }
      raf = requestAnimationFrame(step);
    };

    const start = () => {
      measure();
      if (halfWidth <= 0) return;
      if (!raf) {
        lastTime = 0;
        raf = requestAnimationFrame(step);
      }
    };

    const stop = () => {
      if (raf) {
        cancelAnimationFrame(raf);
        raf = null;
      }
    };

    if ('ResizeObserver' in window) {
      new ResizeObserver(measure).observe(track);
    }
    window.addEventListener('resize', measure, { passive: true });
    window.addEventListener('load', measure, { once: true });

    const root = track.closest('.marquee') || track;
    if ('IntersectionObserver' in window) {
      new IntersectionObserver(
        (entries) => {
          entries.forEach((entry) => {
            if (entry.isIntersecting) start();
            else stop();
          });
        },
        { threshold: 0.05 }
      ).observe(root);
    } else {
      start();
    }

    start();
  }

  function initMarquee() {
    const tracks = document.querySelectorAll('.marquee__track');
    tracks.forEach((track) => {
      if (track.dataset.marqueeReady === '1') return;

      track.innerHTML = track.innerHTML + track.innerHTML;
      track.dataset.marqueeReady = '1';

      const run = () => startMarqueeJs(track);
      if (document.fonts && document.fonts.ready) {
        document.fonts.ready.then(run).catch(run);
      } else {
        run();
      }
    });
  }

  // ------------------------------------------------------------------
  // Sticky CTA bar show/hide
  // ------------------------------------------------------------------
  function initStickyCta() {
    const cta = document.querySelector('.sticky-cta');
    if (!cta) return;
    const close = cta.querySelector('.sticky-cta__close');
    let dismissed = sessionStorage.getItem('neonStickyDismissed') === '1';

    const onScroll = () => {
      if (dismissed) return;
      const scrolled = window.scrollY;
      const total = document.documentElement.scrollHeight - window.innerHeight;
      const ratio = total > 0 ? scrolled / total : 0;
      if (ratio > 0.35 && ratio < 0.95) cta.classList.add('is-visible');
      else cta.classList.remove('is-visible');
    };
    window.addEventListener('scroll', onScroll, { passive: true });

    if (close) {
      close.addEventListener('click', () => {
        cta.classList.remove('is-visible');
        dismissed = true;
        sessionStorage.setItem('neonStickyDismissed', '1');
      });
    }
  }

  // ------------------------------------------------------------------
  // Ring meter animation (.ring-meter[data-value])
  // ------------------------------------------------------------------
  function initRingMeter() {
    const rings = document.querySelectorAll('.ring-meter');
    rings.forEach((ring) => {
      const fill = ring.querySelector('.ring-meter__fill');
      if (!fill) return;
      const r = parseFloat(fill.getAttribute('r')) || 90;
      const c = 2 * Math.PI * r;
      const value = parseFloat(ring.getAttribute('data-value')) || 0;
      const max = parseFloat(ring.getAttribute('data-max')) || 5;
      const pct = Math.min(1, Math.max(0, value / max));
      fill.setAttribute('stroke-dasharray', c.toFixed(2));
      fill.setAttribute('stroke-dashoffset', c.toFixed(2));

      const io = new IntersectionObserver((entries) => {
        entries.forEach((entry) => {
          if (entry.isIntersecting) {
            fill.style.strokeDashoffset = (c * (1 - pct)).toFixed(2);
            io.unobserve(ring);
          }
        });
      }, { threshold: 0.4 });
      io.observe(ring);
    });
  }

  // ------------------------------------------------------------------
  // Wall of Dreams — mood filters + demographic sort
  // ------------------------------------------------------------------
  function initDreamWallControls() {
    const root = document.querySelector('[data-dream-wall-controls]');
    const list = document.querySelector('.dreams-list');
    if (!root || !list) return;

    const filterRow = root.querySelector('.dream-filters');
    const sortTabs = root.querySelectorAll('.dream-sort-tabs [data-sort]');
    const filterChips = filterRow ? filterRow.querySelectorAll('.chip-filter') : [];
    let cards = Array.from(list.querySelectorAll('.dream-card[data-score]'));
    let activeFilter = 'all';
    let activeSort = 'newest';

    const genderRank = { FEMALE: 0, MALE: 1 };

    function pubTs(card) {
      return parseInt(card.getAttribute('data-pub'), 10) || 0;
    }

    function cardMatchesFilter(card) {
      const score = parseInt(card.getAttribute('data-score'), 10) || 0;
      const mbti = (card.getAttribute('data-mbti') || '').toUpperCase();
      if (activeFilter === 'positive') return score >= 4;
      if (activeFilter === 'neutral') return score === 3;
      if (activeFilter === 'negative') return score <= 2;
      if (activeFilter.startsWith('mbti:')) {
        return mbti === activeFilter.slice(5).toUpperCase();
      }
      return true;
    }

    function compareCards(a, b) {
      const aPub = pubTs(a);
      const bPub = pubTs(b);

      if (activeSort === 'newest') {
        return bPub - aPub;
      }

      if (activeSort === 'personality') {
        const aM = (a.getAttribute('data-mbti') || '').toUpperCase();
        const bM = (b.getAttribute('data-mbti') || '').toUpperCase();
        if (!aM && bM) return 1;
        if (aM && !bM) return -1;
        if (aM !== bM) return aM.localeCompare(bM);
        return bPub - aPub;
      }

      if (activeSort === 'age') {
        const aAge = parseInt(a.getAttribute('data-age'), 10);
        const bAge = parseInt(b.getAttribute('data-age'), 10);
        const aHas = !Number.isNaN(aAge);
        const bHas = !Number.isNaN(bAge);
        if (!aHas && bHas) return 1;
        if (aHas && !bHas) return -1;
        if (aHas && bHas && aAge !== bAge) return aAge - bAge;
        return bPub - aPub;
      }

      if (activeSort === 'gender') {
        const aG = (a.getAttribute('data-gender') || '').toUpperCase();
        const bG = (b.getAttribute('data-gender') || '').toUpperCase();
        const aR = genderRank[aG] !== undefined ? genderRank[aG] : 2;
        const bR = genderRank[bG] !== undefined ? genderRank[bG] : 2;
        if (aR !== bR) return aR - bR;
        if (aG !== bG) return aG.localeCompare(bG);
        return bPub - aPub;
      }

      if (activeSort === 'geo') {
        const aGeo = (
          a.getAttribute('data-country-name') ||
          a.getAttribute('data-country-code') ||
          ''
        ).toUpperCase();
        const bGeo = (
          b.getAttribute('data-country-name') ||
          b.getAttribute('data-country-code') ||
          ''
        ).toUpperCase();
        if (!aGeo && bGeo) return 1;
        if (aGeo && !bGeo) return -1;
        if (aGeo !== bGeo) return aGeo.localeCompare(bGeo);
        return bPub - aPub;
      }

      return bPub - aPub;
    }

    function applyWallState() {
      cards.sort(compareCards);
      cards.forEach((card) => list.appendChild(card));
      cards.forEach((card) => {
        card.classList.toggle('is-hidden', !cardMatchesFilter(card));
      });
    }

    filterChips.forEach((chip) => {
      const activate = () => {
        filterChips.forEach((c) => c.classList.remove('is-active'));
        chip.classList.add('is-active');
        activeFilter = chip.getAttribute('data-filter') || 'all';
        applyWallState();
      };
      chip.addEventListener('click', activate);
      chip.addEventListener('keydown', (e) => {
        if (e.key === 'Enter' || e.key === ' ') {
          e.preventDefault();
          activate();
        }
      });
    });

    sortTabs.forEach((tab) => {
      tab.addEventListener('click', () => {
        sortTabs.forEach((t) => {
          const on = t === tab;
          t.classList.toggle('is-active', on);
          t.setAttribute('aria-selected', on ? 'true' : 'false');
        });
        activeSort = tab.getAttribute('data-sort') || 'newest';
        applyWallState();
      });
    });
  }

  // ------------------------------------------------------------------
  // Scale meter (consult): keep is-checked class on labels in sync
  // ------------------------------------------------------------------
  function initScaleMeter() {
    const meter = document.querySelector('.scale-meter');
    if (!meter) return;
    const radios = meter.querySelectorAll('input[type="radio"]');
    const update = () => {
      meter.querySelectorAll('label').forEach((l) => l.classList.remove('is-checked'));
      radios.forEach((r) => {
        if (r.checked) {
          const lbl = meter.querySelector(`label[for="${r.id}"]`);
          if (lbl) lbl.classList.add('is-checked');
        }
      });
    };
    radios.forEach((r) => r.addEventListener('change', update));
    update();
  }

  // ------------------------------------------------------------------
  // Form submit shimmer (visual feedback on submit)
  // ------------------------------------------------------------------
  function initFormSubmit() {
    document.querySelectorAll('form').forEach((form) => {
      form.addEventListener('submit', () => {
        const btn = form.querySelector('button[type="submit"], .btn-large, .btn');
        if (btn) {
          btn.classList.add('is-loading');
          btn.setAttribute('disabled', 'disabled');
          const span = btn.querySelector('span');
          if (span && !span.dataset.original) {
            span.dataset.original = span.textContent;
            span.textContent = 'TRANSMITTING…';
          }
        }
      });
    });
  }

  // ------------------------------------------------------------------
  // Hero orb — JS-driven rotation (works even when CSS animations are blocked)
  // ------------------------------------------------------------------
  function initHeroOrbMotion() {
    const anchor = document.querySelector('.hero-orb-anchor');
    if (!anchor) return;

    const sweep = anchor.querySelector('.hero-orb-sweep');
    const orbit = anchor.querySelector('.hero-orb-orbit');
    const orb = anchor.querySelector('.hero-orb');
    if (!orb) return;

    /* Rings always use CSS animation (orbRingCW / orbRingCCW, 60s) — never touched by JS */

    if (liteHero) return;

    if (sweep) sweep.classList.add('hero-orb-sweep--js');
    if (orbit) orbit.classList.add('hero-orb-orbit--js');
    orb.classList.add('hero-orb--js');

    var start = performance.now();

    function tick(now) {
      var t = (now - start) / 1000;
      var scale = 1 + 0.07 * Math.sin(t * 0.9);
      var pulse = 0.5 + 0.5 * Math.sin(t * 2.2);

      if (sweep) {
        sweep.style.transform = 'rotate(' + (t * 55) + 'deg)';
      }

      if (orbit) {
        orbit.style.transform = 'rotate(' + (-t * 28) + 'deg)';
      }

      orb.style.transform = 'scale(' + scale + ')';
      orb.style.boxShadow =
        '0 0 ' + (50 + pulse * 40) + 'px rgba(0,240,255,' + (0.35 + pulse * 0.25) + '),' +
        '0 0 ' + (90 + pulse * 50) + 'px rgba(255,43,214,' + (0.15 + pulse * 0.2) + '),' +
        'inset 0 0 40px rgba(0,240,255,0.12)';

      requestAnimationFrame(tick);
    }

    requestAnimationFrame(tick);
  }

  // ------------------------------------------------------------------
  // Boot
  // ------------------------------------------------------------------
  function boot() {
    try {
      initNav();
      initReveal();
      initTilt();
      initCounters();
      initHeroOrbMotion();
      initHeroParticles();
      initGlitch();
      initMarquee();
      initStickyCta();
      initRingMeter();
      initDreamWallControls();
      initScaleMeter();
      initFormSubmit();
    } catch (err) {
      console.error('[Dream Analytica] neon.js init error:', err);
      document.documentElement.classList.add('ios-lite');
    }
  }

  if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', boot);
  } else {
    boot();
  }
})();
