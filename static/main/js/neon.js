/* =====================================================
   Dream Analytica — Cyber Neon Micro-Interactions
   ===================================================== */

(function () {
  'use strict';

  const forceMotion = localStorage.getItem('neonForceMotion') === '1';
  const reduced = window.matchMedia('(prefers-reduced-motion: reduce)').matches && !forceMotion;
  const isTouch = window.matchMedia('(hover: none)').matches;

  document.documentElement.classList.add(reduced ? 'motion-reduced' : 'motion-on');

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
    if (reduced) return;
    const canvas = document.querySelector('.hero-canvas');
    if (!canvas) return;
    const ctx = canvas.getContext('2d');
    let particles = [];
    let w = 0;
    let h = 0;
    let dpr = Math.min(window.devicePixelRatio || 1, 1.5);
    let raf = null;
    let mouse = { x: -9999, y: -9999 };

    const stage = canvas.parentElement;

    const resize = () => {
      const rect = stage.getBoundingClientRect();
      w = rect.width;
      h = rect.height;
      canvas.width = w * dpr;
      canvas.height = h * dpr;
      canvas.style.width = w + 'px';
      canvas.style.height = h + 'px';
      ctx.setTransform(dpr, 0, 0, dpr, 0, 0);

      const baseCount = Math.min(110, Math.floor((w * h) / 14000));
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

      // Connections
      for (let i = 0; i < particles.length; i++) {
        const p = particles[i];
        p.x += p.vx;
        p.y += p.vy;
        if (p.x < 0 || p.x > w) p.vx *= -1;
        if (p.y < 0 || p.y > h) p.vy *= -1;

        // Mouse attraction
        const dxm = p.x - mouse.x;
        const dym = p.y - mouse.y;
        const dm2 = dxm * dxm + dym * dym;
        if (dm2 < 14000) {
          const f = 1 - dm2 / 14000;
          p.x -= (dxm / Math.sqrt(dm2 + 0.01)) * f * 0.7;
          p.y -= (dym / Math.sqrt(dm2 + 0.01)) * f * 0.7;
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

      // Nodes
      for (const p of particles) {
        ctx.fillStyle = `rgba(${p.c}, 0.85)`;
        ctx.shadowBlur = 8;
        ctx.shadowColor = `rgba(${p.c}, 0.7)`;
        ctx.beginPath();
        ctx.arc(p.x, p.y, p.r, 0, Math.PI * 2);
        ctx.fill();
      }
      ctx.shadowBlur = 0;

      raf = requestAnimationFrame(tick);
    };

    const onMouse = (e) => {
      const rect = stage.getBoundingClientRect();
      mouse.x = e.clientX - rect.left;
      mouse.y = e.clientY - rect.top;
    };
    const onLeave = () => { mouse.x = -9999; mouse.y = -9999; };

    resize();
    tick();

    window.addEventListener('resize', () => {
      cancelAnimationFrame(raf);
      resize();
      tick();
    });
    stage.addEventListener('mousemove', onMouse);
    stage.addEventListener('mouseleave', onLeave);

    // Pause when off-screen
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
    if (reduced) return;
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
  // Marquee duplication (so seamless scroll works)
  // ------------------------------------------------------------------
  function initMarquee() {
    const tracks = document.querySelectorAll('.marquee__track');
    tracks.forEach((track) => {
      const clone = track.innerHTML;
      track.innerHTML = clone + clone;
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
  // Dream filters (chip toggles)
  // ------------------------------------------------------------------
  function initDreamFilters() {
    const filterRow = document.querySelector('.dream-filters');
    if (!filterRow) return;
    const chips = filterRow.querySelectorAll('.chip-filter');
    const cards = document.querySelectorAll('.dream-card[data-score]');

    chips.forEach((chip) => {
      chip.addEventListener('click', () => {
        chips.forEach((c) => c.classList.remove('is-active'));
        chip.classList.add('is-active');
        const filter = chip.getAttribute('data-filter') || 'all';
        cards.forEach((card) => {
          const score = parseInt(card.getAttribute('data-score'), 10) || 0;
          const mbti = (card.getAttribute('data-mbti') || '').toUpperCase();
          let visible = true;
          if (filter === 'positive') visible = score >= 4;
          else if (filter === 'neutral') visible = score === 3;
          else if (filter === 'negative') visible = score <= 2;
          else if (filter.startsWith('mbti:')) visible = mbti === filter.slice(5).toUpperCase();
          card.classList.toggle('is-hidden', !visible);
        });
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

    if (reduced) return;

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
    initDreamFilters();
    initScaleMeter();
    initFormSubmit();
  }

  if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', boot);
  } else {
    boot();
  }
})();
