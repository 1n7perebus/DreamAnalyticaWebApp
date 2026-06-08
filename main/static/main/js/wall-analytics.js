/**
 * Wall of Dreams — tabbed analytics (tabs + mobile swipe)
 */
(function () {
  'use strict';

  const DEFAULT_FILL = 'rgba(0,240,255,0.06)';
  const DEFAULT_STROKE = 'rgba(0,240,255,0.14)';
  const GEO_TOOLTIP_CLASS = 'geo-tooltip';
  const SVG_NS = 'http://www.w3.org/2000/svg';
  const GEO_SELECTED_FILL = 'rgba(255, 43, 214, 0.72)';
  const GEO_SELECTED_STROKE = 'rgba(255, 124, 231, 0.96)';
  const GEO_MIN_ZOOM = 1;
  const GEO_MAX_ZOOM = 4;
  const GEO_ZOOM_STEP = 0.35;
  const GEO_DRAG_THRESHOLD = 6;

  function emitCountryToggle(code, name, active) {
    document.dispatchEvent(
      new CustomEvent('wall:country-toggle', {
        detail: {
          countryCode: code || '',
          countryName: name || '',
          active: !!active
        }
      })
    );
  }

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
      if (path.classList.contains('geo-country--selected')) return;
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
      if (path.classList.contains('geo-country--selected')) return;
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

  function ensureMapStructure(wrap) {
    let viewport = wrap.querySelector('.geo-map-viewport');
    if (!viewport) {
      viewport = document.createElement('div');
      viewport.className = 'geo-map-viewport';
      viewport.setAttribute('tabindex', '0');
      viewport.setAttribute('aria-label', 'Interactive world map. Scroll to zoom, drag to pan.');

      const stage = document.createElement('div');
      stage.className = 'geo-map-stage';
      viewport.appendChild(stage);

      const controls = document.createElement('div');
      controls.className = 'geo-map-controls';
      controls.setAttribute('aria-label', 'Map zoom controls');
      controls.innerHTML = [
        '<button type="button" class="geo-map-controls__btn" data-geo-zoom="in" aria-label="Zoom in">+</button>',
        '<span class="geo-map-controls__level" data-geo-zoom-level aria-live="polite">100%</span>',
        '<button type="button" class="geo-map-controls__btn" data-geo-zoom="out" aria-label="Zoom out">−</button>',
        '<button type="button" class="geo-map-controls__btn geo-map-controls__btn--reset" data-geo-zoom="reset" aria-label="Reset zoom">⟲</button>'
      ].join('');

      wrap.insertBefore(viewport, wrap.firstChild);
      wrap.appendChild(controls);
    }

    return {
      viewport: wrap.querySelector('.geo-map-viewport'),
      stage: wrap.querySelector('.geo-map-stage'),
      controls: wrap.querySelector('.geo-map-controls')
    };
  }

  function mountSvgInStage(wrap, svgRoot) {
    const { stage } = ensureMapStructure(wrap);
    if (svgRoot && svgRoot.parentElement !== stage) {
      stage.appendChild(svgRoot);
    }
    return stage;
  }

  function setupGeoZoom(wrap) {
    if (!wrap || wrap.dataset.geoZoomBound === '1') return;
    wrap.dataset.geoZoomBound = '1';

    const { viewport, stage, controls } = ensureMapStructure(wrap);
    const svg = wrap.querySelector('svg');
    if (svg) mountSvgInStage(wrap, svg);

    let scale = GEO_MIN_ZOOM;
    let translateX = 0;
    let translateY = 0;
    let isPanning = false;
    let pointerDown = false;
    let panPointerId = null;
    let panStartX = 0;
    let panStartY = 0;
    let panStartTx = 0;
    let panStartTy = 0;
    let suppressClick = false;
    let pinchStartDist = 0;
    let pinchStartScale = GEO_MIN_ZOOM;
    let pinchCenterX = 0;
    let pinchCenterY = 0;

    const levelEl = controls ? controls.querySelector('[data-geo-zoom-level]') : null;

    function stageSize() {
      const rect = stage.getBoundingClientRect();
      const baseW = rect.width / scale || viewport.clientWidth;
      const baseH = rect.height / scale || viewport.clientHeight;
      return { baseW, baseH };
    }

    function clampTranslate() {
      const { baseW, baseH } = stageSize();
      const contentW = baseW * scale;
      const contentH = baseH * scale;
      const viewW = viewport.clientWidth;
      const viewH = viewport.clientHeight;

      if (contentW <= viewW) {
        translateX = (viewW - contentW) / 2;
      } else {
        const minX = viewW - contentW;
        translateX = Math.max(minX, Math.min(0, translateX));
      }

      if (contentH <= viewH) {
        translateY = (viewH - contentH) / 2;
      } else {
        const minY = viewH - contentH;
        translateY = Math.max(minY, Math.min(0, translateY));
      }
    }

    function applyTransform() {
      clampTranslate();
      stage.style.transform = `translate(${translateX}px, ${translateY}px) scale(${scale})`;
      wrap.dataset.geoZoom = String(scale);
      wrap.dataset.geoSuppressClick = suppressClick ? '1' : '0';
      if (levelEl) {
        levelEl.textContent = `${Math.round(scale * 100)}%`;
      }
      viewport.classList.toggle('is-zoomed', scale > GEO_MIN_ZOOM + 0.01);
    }

    function setZoom(nextScale, anchorX, anchorY) {
      const prevScale = scale;
      scale = Math.max(GEO_MIN_ZOOM, Math.min(GEO_MAX_ZOOM, nextScale));
      if (scale === prevScale) return;

      const ax = anchorX != null ? anchorX : viewport.clientWidth / 2;
      const ay = anchorY != null ? anchorY : viewport.clientHeight / 2;
      const ratio = scale / prevScale;
      translateX = ax - (ax - translateX) * ratio;
      translateY = ay - (ay - translateY) * ratio;

      if (scale <= GEO_MIN_ZOOM + 0.001) {
        scale = GEO_MIN_ZOOM;
        translateX = 0;
        translateY = 0;
      }

      applyTransform();
    }

    function resetZoom() {
      scale = GEO_MIN_ZOOM;
      translateX = 0;
      translateY = 0;
      applyTransform();
    }

    function zoomBy(delta, anchorX, anchorY) {
      setZoom(scale + delta, anchorX, anchorY);
    }

    viewport.addEventListener(
      'wheel',
      (event) => {
        event.preventDefault();
        const rect = viewport.getBoundingClientRect();
        const x = event.clientX - rect.left;
        const y = event.clientY - rect.top;
        const delta = event.deltaY < 0 ? GEO_ZOOM_STEP : -GEO_ZOOM_STEP;
        zoomBy(delta, x, y);
      },
      { passive: false }
    );

    viewport.addEventListener('pointerdown', (event) => {
      if (event.button !== 0) return;
      if (event.target.closest('.geo-map-controls')) return;

      pointerDown = true;
      panPointerId = event.pointerId;
      panStartX = event.clientX;
      panStartY = event.clientY;
      panStartTx = translateX;
      panStartTy = translateY;
      suppressClick = false;

      if (scale > GEO_MIN_ZOOM + 0.01) {
        isPanning = true;
        viewport.classList.add('is-panning');
        viewport.setPointerCapture(event.pointerId);
      }
    });

    viewport.addEventListener('pointermove', (event) => {
      if (!pointerDown || event.pointerId !== panPointerId) return;

      const dx = event.clientX - panStartX;
      const dy = event.clientY - panStartY;
      if (Math.abs(dx) > GEO_DRAG_THRESHOLD || Math.abs(dy) > GEO_DRAG_THRESHOLD) {
        suppressClick = true;
      }

      if (!isPanning) return;

      translateX = panStartTx + dx;
      translateY = panStartTy + dy;
      applyTransform();
    });

    function endPan(event) {
      if (!pointerDown || (event && event.pointerId !== panPointerId)) return;
      pointerDown = false;
      isPanning = false;
      panPointerId = null;
      viewport.classList.remove('is-panning');
      wrap.dataset.geoSuppressClick = suppressClick ? '1' : '0';
      if (suppressClick) {
        window.setTimeout(() => {
          suppressClick = false;
          wrap.dataset.geoSuppressClick = '0';
        }, 0);
      }
    }

    viewport.addEventListener('pointerup', endPan);
    viewport.addEventListener('pointercancel', endPan);

    viewport.addEventListener('dblclick', (event) => {
      if (event.target.closest('.geo-map-controls')) return;
      const rect = viewport.getBoundingClientRect();
      const x = event.clientX - rect.left;
      const y = event.clientY - rect.top;
      if (scale >= GEO_MAX_ZOOM - 0.01) {
        resetZoom();
      } else {
        setZoom(Math.min(GEO_MAX_ZOOM, scale + GEO_ZOOM_STEP * 2), x, y);
      }
    });

    viewport.addEventListener(
      'touchstart',
      (event) => {
        if (event.touches.length !== 2) return;
        const rect = viewport.getBoundingClientRect();
        const [a, b] = event.touches;
        pinchStartDist = Math.hypot(b.clientX - a.clientX, b.clientY - a.clientY);
        pinchStartScale = scale;
        pinchCenterX = (a.clientX + b.clientX) / 2 - rect.left;
        pinchCenterY = (a.clientY + b.clientY) / 2 - rect.top;
        suppressClick = true;
      },
      { passive: true }
    );

    viewport.addEventListener(
      'touchmove',
      (event) => {
        if (event.touches.length !== 2 || !pinchStartDist) return;
        event.preventDefault();
        const [a, b] = event.touches;
        const dist = Math.hypot(b.clientX - a.clientX, b.clientY - a.clientY);
        const nextScale = pinchStartScale * (dist / pinchStartDist);
        setZoom(nextScale, pinchCenterX, pinchCenterY);
      },
      { passive: false }
    );

    viewport.addEventListener('touchend', () => {
      pinchStartDist = 0;
      window.setTimeout(() => {
        suppressClick = false;
        wrap.dataset.geoSuppressClick = '0';
      }, 0);
    });

    if (controls) {
      controls.addEventListener('click', (event) => {
        const btn = event.target.closest('[data-geo-zoom]');
        if (!btn) return;
        event.stopPropagation();
        const action = btn.getAttribute('data-geo-zoom');
        if (action === 'in') zoomBy(GEO_ZOOM_STEP);
        else if (action === 'out') zoomBy(-GEO_ZOOM_STEP);
        else if (action === 'reset') resetZoom();
      });
    }

    window.addEventListener('resize', () => applyTransform());
    applyTransform();
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
    let selectedCode = null;

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

    const applyCountrySelectedState = (code) => {
      const svg = wrap.querySelector('svg');
      if (!svg) return;

      if (selectedCode) {
        countryPathsByCode(svg, selectedCode).forEach((path) => {
          path.classList.remove('geo-country--selected');
          if (path.dataset.geoBaseFill) path.style.fill = path.dataset.geoBaseFill;
          if (path.dataset.geoBaseStroke) path.style.stroke = path.dataset.geoBaseStroke;
          path.style.strokeWidth = '0.75';
          path.style.filter = 'url(#geoGlow)';
          path.style.fillOpacity = '';
        });
      }

      selectedCode = code || null;
      wrap.dataset.geoSelectedCode = selectedCode || '';

      if (!selectedCode) return;

      countryPathsByCode(svg, selectedCode).forEach((path) => {
        path.classList.add('geo-country--selected');
        path.style.fill = GEO_SELECTED_FILL;
        path.style.stroke = GEO_SELECTED_STROKE;
        path.style.strokeWidth = '1.2';
        path.style.fillOpacity = '0.92';
        path.style.filter = 'url(#geoRainbowGlow)';
      });
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
      if (wrap.dataset.geoSuppressClick === '1') return;
      const target = event.target && event.target.closest
        ? event.target.closest('.geo-country--active')
        : null;
      if (!target) {
        applyCountrySelectedState(null);
        emitCountryToggle('', '', false);
        hideTooltip();
        return;
      }
      const text = target.getAttribute('data-tooltip');
      if (!text) return;
      const nextCode = (
        target.getAttribute('data-iso2') ||
        target.getAttribute('data-iso3') ||
        ''
      ).toUpperCase();
      const nextName = text.split(':')[0] || nextCode;
      const isTogglingOff = selectedCode === nextCode;
      applyCountrySelectedState(isTogglingOff ? null : nextCode);
      emitCountryToggle(
        isTogglingOff ? '' : nextCode,
        isTogglingOff ? '' : nextName,
        !isTogglingOff
      );
      const rect = wrap.getBoundingClientRect();
      const x = event.clientX - rect.left + 14;
      const y = event.clientY - rect.top + 14;
      if (isTogglingOff) {
        hideTooltip();
      } else {
        showTooltip(text, x, y, true);
      }
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
      mountSvgInStage(wrap, existing);
      setupGeoZoom(wrap);
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
        wrap.textContent = '';
        delete wrap.dataset.geoTooltipBound;
        delete wrap.dataset.geoZoomBound;
        const { stage } = ensureMapStructure(wrap);
        stage.innerHTML = svgText;
        setupGeoZoom(wrap);
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
