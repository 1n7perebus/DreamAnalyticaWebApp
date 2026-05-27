/**
 * Wall of Dreams — tabbed analytics (tabs + mobile swipe)
 */
(function () {
  'use strict';

  const DEFAULT_FILL = 'rgba(0,240,255,0.06)';
  const DEFAULT_STROKE = 'rgba(0,240,255,0.14)';

  function initWallAnalytics() {
    const root = document.querySelector('.wall-analytics');
    if (!root) return;

    const tabs = root.querySelectorAll('.wall-analytics__tab');
    const track = root.querySelector('.wall-analytics__track');
    const panels = root.querySelectorAll('.wall-analytics__panel');
    const dots = root.querySelectorAll('.wall-analytics__dot');
    const viewport = root.querySelector('.wall-analytics__viewport');
    if (!track || !panels.length) return;

    const panelIds = Array.from(panels).map((p) => p.dataset.panel);
    let activeIndex = Math.max(
      0,
      panelIds.indexOf(
        (root.querySelector('.wall-analytics__tab.is-active') || {}).dataset.tab
      )
    );

    function isSwipeLayout() {
      return window.matchMedia('(max-width: 767px)').matches;
    }

    function setActive(index, scrollIntoView) {
      activeIndex = Math.max(0, Math.min(index, panels.length - 1));
      const id = panelIds[activeIndex];
      const swipe = isSwipeLayout();

      tabs.forEach((tab) => {
        const on = tab.dataset.tab === id;
        tab.classList.toggle('is-active', on);
        tab.setAttribute('aria-selected', on ? 'true' : 'false');
      });
      panels.forEach((panel) => {
        const on = panel.dataset.panel === id;
        panel.classList.toggle('is-active', on);
        if (swipe) {
          panel.removeAttribute('hidden');
        } else {
          panel.hidden = !on;
        }
      });
      dots.forEach((dot, i) => {
        dot.classList.toggle('is-active', i === activeIndex);
      });

      if (scrollIntoView && viewport && swipe) {
        const w = viewport.offsetWidth || 1;
        viewport.scrollTo({ left: activeIndex * w, behavior: 'smooth' });
      }

      if (id === 'geo') {
        highlightGeoCountries(root);
      }
    }

    tabs.forEach((tab) => {
      tab.addEventListener('click', () => {
        const idx = panelIds.indexOf(tab.dataset.tab);
        if (idx >= 0) setActive(idx, true);
      });
    });

    dots.forEach((dot, i) => {
      dot.addEventListener('click', () => setActive(i, true));
    });

    if (viewport) {
      let scrollTimer;
      viewport.addEventListener(
        'scroll',
        () => {
          clearTimeout(scrollTimer);
          scrollTimer = setTimeout(() => {
            const w = viewport.offsetWidth || 1;
            const idx = Math.round(viewport.scrollLeft / w);
            if (idx !== activeIndex) setActive(idx, false);
          }, 80);
        },
        { passive: true }
      );
    }

    window.addEventListener('resize', () => setActive(activeIndex, false));
    setActive(activeIndex, false);
  }

  function getCountryData() {
    const dataEl = document.getElementById('wall-country-data');
    if (!dataEl) return [];
    try {
      return JSON.parse(dataEl.textContent);
    } catch (e) {
      return [];
    }
  }

  function paintCountries(svgRoot, countries) {
    const paths = svgRoot.querySelectorAll('.geo-country');
    paths.forEach((path) => {
      path.classList.remove('geo-country--active');
      path.style.fill = DEFAULT_FILL;
      path.style.stroke = DEFAULT_STROKE;
      path.style.strokeWidth = '0.5';
      path.style.filter = '';
      path.removeAttribute('data-count');
      path.removeAttribute('title');
    });

    if (!countries.length) return;

    const maxCount = Math.max(...countries.map((c) => c.count), 1);

    countries.forEach((c) => {
      const code = (c.code || '').toUpperCase();
      const matched = svgRoot.querySelectorAll(
        `.geo-country[data-iso2="${code}"], .geo-country[data-iso3="${code}"]`
      );
      const intensity = 0.35 + (c.count / maxCount) * 0.65;
      const fillA = Math.max(0, Math.min(1, 0.12 + 0.55 * intensity));
      const strokeA = Math.max(0, Math.min(1, 0.35 + 0.45 * intensity));
      const label = `${c.name}: ${c.count} dream${c.count === 1 ? '' : 's'} (${c.pct}% of geolocated)`;

      matched.forEach((path) => {
        path.classList.add('geo-country--active');
        path.style.fill = `rgba(0,240,255,${fillA})`;
        path.style.stroke = `rgba(0,240,255,${strokeA})`;
        path.style.strokeWidth = '0.75';
        path.style.filter = 'url(#geoGlow)';
        path.setAttribute('data-count', String(c.count));
        path.setAttribute('title', label);
      });
    });
  }

  function highlightGeoCountries(root) {
    const wrap = root.querySelector('.geo-map-wrap');
    if (!wrap) return;

    const mapUrl = wrap.dataset.mapUrl;
    const countries = getCountryData();
    if (!mapUrl) return;

    const existing = wrap.querySelector('svg');
    if (existing) {
      paintCountries(wrap, countries);
      return;
    }

    let loading = wrap.dataset.mapLoading === '1';
    if (loading) return;
    wrap.dataset.mapLoading = '1';

    fetch(mapUrl, { credentials: 'same-origin' })
      .then((res) => {
        if (!res.ok) throw new Error('map fetch failed');
        return res.text();
      })
      .then((svgText) => {
        wrap.innerHTML = svgText;
        paintCountries(wrap, countries);
      })
      .catch(() => {
        /* Keep any static fallback already in the template */
      })
      .finally(() => {
        wrap.dataset.mapLoading = '0';
      });
  }

  if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', initWallAnalytics);
  } else {
    initWallAnalytics();
  }
})();
