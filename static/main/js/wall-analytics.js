/**
 * Wall of Dreams — tabbed analytics (tabs + mobile swipe)
 */
(function () {
  'use strict';

  const DEFAULT_FILL = 'rgba(0,240,255,0.06)';
  const DEFAULT_STROKE = 'rgba(0,240,255,0.14)';
  const GEO_TOOLTIP_CLASS = 'geo-tooltip';

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
        panel.hidden = !on;
      });
      dots.forEach((dot, i) => {
        dot.classList.toggle('is-active', i === activeIndex);
      });

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
      let touchStartX = 0;
      let touchStartY = 0;

      viewport.addEventListener(
        'touchstart',
        (e) => {
          touchStartX = e.touches[0].clientX;
          touchStartY = e.touches[0].clientY;
        },
        { passive: true }
      );

      viewport.addEventListener(
        'touchend',
        (e) => {
          if (!isSwipeLayout()) return;
          const dx = e.changedTouches[0].clientX - touchStartX;
          const dy = e.changedTouches[0].clientY - touchStartY;
          if (Math.abs(dx) < 48 || Math.abs(dx) < Math.abs(dy)) return;
          if (dx < 0 && activeIndex < panels.length - 1) {
            setActive(activeIndex + 1, false);
          } else if (dx > 0 && activeIndex > 0) {
            setActive(activeIndex - 1, false);
          }
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
      path.removeAttribute('data-tooltip');
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
      const tooltipText = `${c.name}: ${c.count} dreamer${c.count === 1 ? '' : 's'}`;

      matched.forEach((path) => {
        path.classList.add('geo-country--active');
        path.style.fill = `rgba(0,240,255,${fillA})`;
        path.style.stroke = `rgba(0,240,255,${strokeA})`;
        path.style.strokeWidth = '0.75';
        path.style.filter = 'url(#geoGlow)';
        path.setAttribute('data-count', String(c.count));
        path.setAttribute('data-tooltip', tooltipText);
        path.setAttribute('title', tooltipText);
      });
    });
  }

  function setupGeoTooltip(wrap) {
    if (!wrap) return;
    let tooltip = wrap.querySelector(`.${GEO_TOOLTIP_CLASS}`);
    if (!tooltip) {
      tooltip = document.createElement('div');
      tooltip.className = GEO_TOOLTIP_CLASS;
      tooltip.setAttribute('role', 'status');
      tooltip.setAttribute('aria-live', 'polite');
      wrap.appendChild(tooltip);
    }
    if (wrap.dataset.geoTooltipBound === '1') return;
    wrap.dataset.geoTooltipBound = '1';

    const hideTooltip = () => {
      tooltip.classList.remove('is-visible');
      wrap.dataset.geoTooltipPinned = '0';
    };

    const showTooltip = (text, x, y, pin) => {
      tooltip.textContent = text;
      const tipW = tooltip.offsetWidth || 180;
      const tipH = tooltip.offsetHeight || 34;
      const minX = 8;
      const maxX = Math.max(minX, wrap.clientWidth - tipW - 8);
      const minY = 8;
      const maxY = Math.max(minY, wrap.clientHeight - tipH - 8);
      const nextX = Math.max(minX, Math.min(x, maxX));
      const nextY = Math.max(minY, Math.min(y, maxY));
      tooltip.style.left = `${nextX}px`;
      tooltip.style.top = `${nextY}px`;
      wrap.dataset.geoTooltipPinned = pin ? '1' : '0';
      tooltip.classList.add('is-visible');
    };

    wrap.addEventListener('pointermove', (event) => {
      if (wrap.dataset.geoTooltipPinned === '1') return;
      const target = event.target && event.target.closest
        ? event.target.closest('.geo-country--active')
        : null;
      if (!target) {
        hideTooltip();
        return;
      }
      const text = target.getAttribute('data-tooltip');
      if (!text) {
        hideTooltip();
        return;
      }
      const rect = wrap.getBoundingClientRect();
      const x = event.clientX - rect.left + 14;
      const y = event.clientY - rect.top + 14;
      showTooltip(text, x, y, false);
    });

    wrap.addEventListener('mouseleave', hideTooltip);

    wrap.addEventListener('click', (event) => {
      const target = event.target && event.target.closest
        ? event.target.closest('.geo-country--active')
        : null;
      if (!target) {
        hideTooltip();
        return;
      }
      const text = target.getAttribute('data-tooltip');
      if (!text) return;
      const rect = wrap.getBoundingClientRect();
      const x = event.clientX - rect.left + 14;
      const y = event.clientY - rect.top + 14;
      showTooltip(text, x, y, true);
    });

    document.addEventListener('pointerdown', (event) => {
      if (!wrap.contains(event.target)) hideTooltip();
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
      setupGeoTooltip(wrap);
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
        setupGeoTooltip(wrap);
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
