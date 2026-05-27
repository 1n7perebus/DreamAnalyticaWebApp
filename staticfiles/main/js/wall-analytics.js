/**
 * Wall of Dreams — tabbed analytics (tabs + mobile swipe)
 */
(function () {
  'use strict';

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

    /* Mobile swipe: sync tab to scroll position */
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

    /* Touch drag hint on track */
    let touchStartX = 0;
    if (viewport) {
      viewport.addEventListener(
        'touchstart',
        (e) => {
          touchStartX = e.touches[0].clientX;
        },
        { passive: true }
      );
    }

    window.addEventListener('resize', () => setActive(activeIndex, false));
    setActive(activeIndex, false);
    highlightGeoCountries(root);
  }

  function highlightGeoCountries(root) {
    const mapObj = root.querySelector('.geo-map-object');
    const dataEl = document.getElementById('wall-country-data');
    if (!mapObj || !dataEl) return;

    let countries = [];
    try {
      countries = JSON.parse(dataEl.textContent);
    } catch (e) {
      return;
    }

    function apply() {
      const doc = mapObj.contentDocument;
      if (!doc) return;

      const paths = doc.querySelectorAll('.geo-country');
      paths.forEach((p) => {
        p.classList.remove('geo-country--active');
        p.removeAttribute('data-count');
        p.removeAttribute('title');
      });

      if (!countries.length) return;

      const maxCount = Math.max(...countries.map((c) => c.count), 1);

      countries.forEach((c) => {
        const code = (c.code || '').toUpperCase();
        const matched = doc.querySelectorAll(
          `.geo-country[data-iso2="${code}"], .geo-country[data-iso3="${code}"]`
        );
        const intensity = 0.35 + (c.count / maxCount) * 0.65;
        const label = `${c.name}: ${c.count} dream${c.count === 1 ? '' : 's'} (${c.pct}% of geolocated)`;
        matched.forEach((path) => {
          path.classList.add('geo-country--active');
          path.style.setProperty('--geo-intensity', String(intensity));
          path.setAttribute('data-count', String(c.count));
          path.setAttribute('title', label);
        });
      });
    }

    if (mapObj.contentDocument && mapObj.contentDocument.querySelector('svg')) {
      apply();
    } else {
      mapObj.addEventListener('load', apply, { once: true });
    }
  }

  if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', initWallAnalytics);
  } else {
    initWallAnalytics();
  }
})();
