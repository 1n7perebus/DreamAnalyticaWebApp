/**
 * Wall of Dreams — tabbed analytics (tabs + mobile swipe)
 */
(function () {
  'use strict';

  const DEFAULT_FILL = 'rgba(0,240,255,0.06)';
  const DEFAULT_STROKE = 'rgba(0,240,255,0.14)';
  const GEO_TOOLTIP_CLASS = 'geo-tooltip';
  const SVG_NS = 'http://www.w3.org/2000/svg';

  function ensureGeoRainbowDefs(svgRoot) {
    if (!svgRoot) return;

    svgRoot.querySelector('#geoRainbowFill')?.remove();
    svgRoot.querySelector('#geoRainbowGlow')?.remove();

    let defs = svgRoot.querySelector('defs');
    if (!defs) {
      defs = document.createElementNS(SVG_NS, 'defs');
      svgRoot.insertBefore(defs, svgRoot.firstChild);
    }

    const grad = document.createElementNS(SVG_NS, 'linearGradient');
    grad.setAttribute('id', 'geoRainbowFill');
    grad.setAttribute('gradientUnits', 'userSpaceOnUse');
    grad.setAttribute('x1', '0');
    grad.setAttribute('y1', '0');
    grad.setAttribute('x2', '960');
    grad.setAttribute('y2', '480');

    const stopDefs = [
      { offset: '0%', colors: '#00e8f5;#b878d8;#8b9cff;#d070e8;#00e8f5' },
      { offset: '50%', colors: '#c878e0;#7b9cff;#00e8f5;#d888e8;#9cb8f0' },
      { offset: '100%', colors: '#8b9cff;#00e8f5;#c878e0;#9cb8f0;#8b9cff' }
    ];

    stopDefs.forEach(({ offset, colors }) => {
      const stop = document.createElementNS(SVG_NS, 'stop');
      stop.setAttribute('offset', offset);
      stop.setAttribute('stop-color', '#9cb0e8');
      const anim = document.createElementNS(SVG_NS, 'animate');
      anim.setAttribute('attributeName', 'stop-color');
      anim.setAttribute('values', colors);
      anim.setAttribute('dur', '5.5s');
      anim.setAttribute('repeatCount', 'indefinite');
      stop.appendChild(anim);
      grad.appendChild(stop);
    });
    defs.appendChild(grad);

    const filter = document.createElementNS(SVG_NS, 'filter');
    filter.setAttribute('id', 'geoRainbowGlow');
    filter.setAttribute('x', '-70%');
    filter.setAttribute('y', '-70%');
    filter.setAttribute('width', '240%');
    filter.setAttribute('height', '240%');

    const blur = document.createElementNS(SVG_NS, 'feGaussianBlur');
    blur.setAttribute('in', 'SourceGraphic');
    blur.setAttribute('stdDeviation', '1.85');
    blur.setAttribute('result', 'blur');

    const merge = document.createElementNS(SVG_NS, 'feMerge');
    ['blur', 'blur', 'SourceGraphic'].forEach((nodeIn) => {
      const mergeNode = document.createElementNS(SVG_NS, 'feMergeNode');
      mergeNode.setAttribute('in', nodeIn);
      merge.appendChild(mergeNode);
    });

    filter.appendChild(blur);
    filter.appendChild(merge);
    defs.appendChild(filter);
  }

  function countryPathsByCode(svgRoot, code) {
    const c = (code || '').toUpperCase();
    return svgRoot.querySelectorAll(
      `.geo-country--active[data-iso2="${c}"], .geo-country--active[data-iso3="${c}"]`
    );
  }

  function clearCountryHover(svgRoot, code) {
    if (!svgRoot || !code) return;
    countryPathsByCode(svgRoot, code).forEach((path) => {
      path.classList.remove('geo-country--hover');
      requestAnimationFrame(() => {
        if (path.dataset.geoBaseFill) path.style.fill = path.dataset.geoBaseFill;
        if (path.dataset.geoBaseStroke) path.style.stroke = path.dataset.geoBaseStroke;
        path.style.fillOpacity = '';
        path.style.strokeWidth = '0.75';
        path.style.filter = 'url(#geoGlow)';
      });
    });
  }

  function applyCountryHover(svgRoot, code) {
    if (!svgRoot || !code) return;
    countryPathsByCode(svgRoot, code).forEach((path) => {
      path.classList.add('geo-country--hover');
      requestAnimationFrame(() => {
        path.style.fill = 'url(#geoRainbowFill)';
        path.style.fillOpacity = '0.78';
        path.style.stroke = 'rgba(200, 120, 220, 0.62)';
        path.style.strokeWidth = '0.9';
        path.style.filter = 'url(#geoRainbowGlow)';
      });
    });
  }

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
      path.classList.remove('geo-country--active', 'geo-country--hover');
      path.style.fill = DEFAULT_FILL;
      path.style.stroke = DEFAULT_STROKE;
      path.style.strokeWidth = '0.5';
      path.style.filter = '';
      path.removeAttribute('data-count');
      path.removeAttribute('data-tooltip');
      path.removeAttribute('title');
      delete path.dataset.geoBaseFill;
      delete path.dataset.geoBaseStroke;
    });

    ensureGeoRainbowDefs(svgRoot);

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
      const symbolText = c.top_symbol
        ? `\nTop symbol: ${c.top_symbol} (${c.top_symbol_count})`
        : '';
      const tooltipText = `${c.name}: ${c.count} dreamer${c.count === 1 ? '' : 's'}${symbolText}`;

      matched.forEach((path) => {
        path.classList.add('geo-country--active');
        path.style.fill = `rgba(0,240,255,${fillA})`;
        path.style.stroke = `rgba(0,240,255,${strokeA})`;
        path.style.strokeWidth = '0.75';
        path.style.filter = 'url(#geoGlow)';
        path.dataset.geoBaseFill = path.style.fill;
        path.dataset.geoBaseStroke = path.style.stroke;
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

    let hoverCode = null;

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
      const svg = wrap.querySelector('svg');
      const target = event.target && event.target.closest
        ? event.target.closest('.geo-country--active')
        : null;
      const nextCode = target
        ? (target.getAttribute('data-iso2') || target.getAttribute('data-iso3') || '').toUpperCase()
        : null;

      if (nextCode !== hoverCode) {
        if (svg) clearCountryHover(svg, hoverCode);
        hoverCode = nextCode;
        if (svg && hoverCode) applyCountryHover(svg, hoverCode);
      }

      if (wrap.dataset.geoTooltipPinned === '1') return;
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

    wrap.addEventListener('mouseleave', () => {
      const svg = wrap.querySelector('svg');
      if (svg) clearCountryHover(svg, hoverCode);
      hoverCode = null;
      hideTooltip();
    });

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
      paintCountries(existing, countries);
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
        const svg = wrap.querySelector('svg');
        if (svg) paintCountries(svg, countries);
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
