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
    renderGeoMarkers(root);
  }

  function renderGeoMarkers(root) {
    const layer = root.querySelector('.geo-map__markers');
    const dataEl = document.getElementById('wall-country-data');
    if (!layer || !dataEl) return;

    let markers = [];
    try {
      markers = JSON.parse(dataEl.textContent);
    } catch (e) {
      return;
    }

    layer.innerHTML = '';
    markers.forEach((m) => {
      if (m.x == null || m.y == null) return;
      const g = document.createElementNS('http://www.w3.org/2000/svg', 'g');
      g.setAttribute('class', 'geo-map__marker');
      g.setAttribute('transform', `translate(${m.x}, ${m.y})`);

      const pulse = document.createElementNS('http://www.w3.org/2000/svg', 'circle');
      pulse.setAttribute('class', 'geo-map__pulse');
      pulse.setAttribute('r', String(m.size + 6));
      pulse.setAttribute('cx', '0');
      pulse.setAttribute('cy', '0');

      const core = document.createElementNS('http://www.w3.org/2000/svg', 'circle');
      core.setAttribute('class', 'geo-map__core');
      core.setAttribute('r', String(m.size));
      core.setAttribute('cx', '0');
      core.setAttribute('cy', '0');

      const title = document.createElementNS('http://www.w3.org/2000/svg', 'title');
      title.textContent = `${m.name}: ${m.count} dream${m.count === 1 ? '' : 's'} (${m.pct}%)`;

      g.appendChild(pulse);
      g.appendChild(core);
      g.appendChild(title);
      layer.appendChild(g);
    });
  }

  if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', initWallAnalytics);
  } else {
    initWallAnalytics();
  }
})();
