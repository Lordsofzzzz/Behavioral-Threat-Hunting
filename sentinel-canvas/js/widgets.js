/* ══════════════════════════════════════════════
   SENTINEL CANVAS — WIDGET MANAGER
   ══════════════════════════════════════════════ */

const WidgetManager = (() => {
  const REGISTRY = {
    stats:     { title: 'Stats Counters',   icon: '📊', w: 520, h: 160, desc: 'Total, critical, warning counts' },
    alerts:    { title: 'Alert Table',      icon: '🚨', w: 700, h: 300, desc: 'Live list of recent alerts' },
    attacks:   { title: 'Attack Types',     icon: '🎯', w: 380, h: 280, desc: 'Breakdown by attack category' },
    ips:       { title: 'Top IPs',          icon: '🌐', w: 380, h: 280, desc: 'Most active attacking IPs' },
    timeline:  { title: 'Timeline',         icon: '📈', w: 540, h: 240, desc: 'Alert volume over time' },
    incidents: { title: 'Incidents',        icon: '🔗', w: 520, h: 320, desc: 'Correlated attack campaigns' },
    gauge:     { title: 'Risk Gauge',       icon: '🎚', w: 240, h: 200, desc: 'Average risk score gauge' },
    heatmap:   { title: 'Activity Heatmap', icon: '🔥', w: 480, h: 160, desc: 'Hourly activity heatmap' },
    clock:     { title: 'Clock / Uptime',   icon: '🕐', w: 280, h: 140, desc: 'Live clock and session uptime' },
    notes:     { title: 'Notes',            icon: '📝', w: 320, h: 200, desc: 'Free text / markdown notes' },
  };

  let _zTop = 10;

  // ── Add Widget ────────────────────────────────
  function addWidget(type, opts = {}) {
    const def = REGISTRY[type];
    if (!def) return;
    const p = App.currentPage();
    if (!p) return;

    const id  = opts.id || App.uid();
    const x   = opts.x  ?? _autoX();
    const y   = opts.y  ?? _autoY();
    const w   = opts.w  ?? def.w;
    const h   = opts.h  ?? def.h;
    const title = opts.title || def.title;
    const accent = opts.accent || 'default';

    const widgetData = { id, type, x, y, w, h, title, accent, notes: opts.notes || '' };
    p.widgets[id] = widgetData;

    const el = _buildEl(widgetData);
    Canvas.getCanvasEl().appendChild(el);
    bringToFront(id);
    _loadData(id);

    if (!opts._skipHistory) {
      History.push({ type: 'addWidget', widgetId: id, widget: { ...widgetData } });
    }

    document.getElementById('empty-hint').style.display = 'none';
    App.emit('widget:added', id);
    return id;
  }

  // ── Build DOM element ─────────────────────────
  function _buildEl(w) {
    const el = document.createElement('div');
    el.className = 'widget';
    el.id = w.id;
    el.dataset.type = w.type;
    el.dataset.accent = w.accent || 'default';
    el.style.cssText = `left:${w.x}px;top:${w.y}px;width:${w.w}px;height:${w.h}px;z-index:${++_zTop}`;

    el.innerHTML = `
      <div class="widget-accent-bar"></div>
      <div class="widget-header">
        <span class="widget-title" title="Double-click to rename">${App.esc(w.title)}</span>
        <div class="widget-actions">
          <button class="wbtn refresh" title="Refresh">↺</button>
          <button class="wbtn minimize" title="Minimize/Restore">−</button>
          <button class="wbtn duplicate" title="Duplicate">⧉</button>
          <button class="wbtn close" title="Remove">×</button>
        </div>
      </div>
      <div class="widget-body" id="body_${w.id}">
        <div class="w-loading"><div class="w-spinner"></div>Loading…</div>
      </div>
      <div class="w-footer">
        <span id="footer-ts-${w.id}">—</span>
        <span id="footer-src-${w.id}" style="color:var(--muted);opacity:0.6">${App.esc(App.getApiBase())}</span>
      </div>
      <div class="resize-handle se" title="Resize"></div>
      <div class="resize-handle e"></div>
      <div class="resize-handle s"></div>
    `;

    // Events
    const header = el.querySelector('.widget-header');
    header.addEventListener('mousedown', e => {
      if (e.target.tagName === 'BUTTON' || e.target.classList.contains('widget-title')) return;
      Drag.startDrag(e, w.id);
    });

    // Resize handles
    el.querySelector('.resize-handle.se').addEventListener('mousedown', e => Drag.startResize(e, w.id, 'se'));
    el.querySelector('.resize-handle.e').addEventListener('mousedown',  e => Drag.startResize(e, w.id, 'e'));
    el.querySelector('.resize-handle.s').addEventListener('mousedown',  e => Drag.startResize(e, w.id, 's'));

    // Buttons
    el.querySelector('.wbtn.refresh').addEventListener('click', e => { e.stopPropagation(); _loadData(w.id); });
    el.querySelector('.wbtn.minimize').addEventListener('click', e => { e.stopPropagation(); toggleMinimize(w.id); });
    el.querySelector('.wbtn.duplicate').addEventListener('click', e => { e.stopPropagation(); duplicateWidget(w.id); });
    el.querySelector('.wbtn.close').addEventListener('click', e => { e.stopPropagation(); removeWidget(w.id); });

    // Title double-click to rename
    const titleEl = el.querySelector('.widget-title');
    titleEl.addEventListener('dblclick', e => {
      e.stopPropagation();
      _startRename(w.id, titleEl);
    });

    // Selection
    el.addEventListener('mousedown', e => {
      if (!e.target.closest('button') && !e.target.closest('.resize-handle')) {
        selectWidget(w.id);
      }
    });

    // Right-click context menu
    el.addEventListener('contextmenu', e => {
      e.preventDefault();
      selectWidget(w.id);
      ContextMenu.show(e.clientX, e.clientY, w.id);
    });

    return el;
  }

  // ── Load data ─────────────────────────────────
  async function _loadData(id) {
    const p = App.currentPage();
    if (!p?.widgets[id]) return;
    const { type, notes } = p.widgets[id];
    const body = document.getElementById(`body_${id}`);
    if (!body) return;

    // Notes widget — no API needed
    if (type === 'notes') {
      Renderers.renderNotes(body, notes);
      // Save notes on input
      body.querySelector('.notes-body')?.addEventListener('input', e => {
        if (p.widgets[id]) p.widgets[id].notes = e.target.value;
      });
      _updateFooter(id);
      return;
    }
    if (type === 'clock') {
      Renderers.renderClock(body, id);
      _updateFooter(id);
      return;
    }

    body.innerHTML = '<div class="w-loading"><div class="w-spinner"></div>Loading…</div>';

    try {
      switch (type) {
        case 'stats':     await Renderers.renderStats(body);     break;
        case 'alerts':    await Renderers.renderAlerts(body);    break;
        case 'attacks':   await Renderers.renderAttacks(body);   break;
        case 'ips':       await Renderers.renderIPs(body);       break;
        case 'timeline':  await Renderers.renderTimeline(body);  break;
        case 'incidents': await Renderers.renderIncidents(body); break;
        case 'gauge':     await Renderers.renderGauge(body);     break;
        case 'heatmap':   await Renderers.renderHeatmap(body);   break;
      }
      _updateFooter(id);
    } catch (err) {
      body.innerHTML = `<div class="w-error">
        <div class="w-error-icon">⚠</div>
        <div>Could not load data</div>
        <div class="w-error-detail">${App.esc(err.message)}</div>
        <div class="w-error-hint">API: ${App.esc(App.getApiBase())}</div>
      </div>`;
    }
  }

  function _updateFooter(id) {
    const tsEl = document.getElementById(`footer-ts-${id}`);
    if (tsEl) tsEl.textContent = `Updated ${new Date().toLocaleTimeString()}`;
  }

  // ── Rename ────────────────────────────────────
  function _startRename(id, titleEl) {
    const oldTitle = titleEl.textContent;
    titleEl.contentEditable = 'true';
    titleEl.focus();
    const range = document.createRange();
    range.selectNodeContents(titleEl);
    window.getSelection().removeAllRanges();
    window.getSelection().addRange(range);

    const commit = () => {
      titleEl.contentEditable = 'false';
      const newTitle = titleEl.textContent.trim() || oldTitle;
      titleEl.textContent = newTitle;
      const p = App.currentPage();
      if (p?.widgets[id]) {
        History.push({ type:'renameWidget', widgetId:id, oldTitle, newTitle });
        p.widgets[id].title = newTitle;
      }
    };

    titleEl.addEventListener('blur', commit, { once: true });
    titleEl.addEventListener('keydown', e => {
      if (e.key === 'Enter') { e.preventDefault(); titleEl.blur(); }
      if (e.key === 'Escape') { titleEl.textContent = oldTitle; titleEl.blur(); }
    }, { once: true });
  }

  // ── Remove ────────────────────────────────────
  function removeWidget(id, silent=false) {
    const p = App.currentPage();
    const el = document.getElementById(id);
    if (!el) return;

    // Stop clock timer
    if (el._clockTimer) clearInterval(el._clockTimer);

    if (!silent && p?.widgets[id]) {
      History.push({ type:'removeWidget', widgetId:id, widget: { ...p.widgets[id] } });
    }

    delete p?.widgets[id];
    el.remove();

    if (App.state.selectedWidgetId === id) {
      App.state.selectedWidgetId = null;
      App.emit('selection:changed', null);
    }

    _checkEmpty();
    App.emit('widget:removed', id);
  }

  function restoreWidget(w) {
    const p = App.currentPage();
    if (!p) return;
    addWidget(w.type, { ...w, _skipHistory: true });
  }

  // ── Duplicate ─────────────────────────────────
  function duplicateWidget(id) {
    const p = App.currentPage();
    if (!p?.widgets[id]) return;
    const src = p.widgets[id];
    addWidget(src.type, {
      ...src,
      id: undefined,
      x: src.x + 32,
      y: src.y + 32,
      _skipHistory: false,
    });
    Toast.show('Widget duplicated', 'success');
  }

  // ── Minimize ──────────────────────────────────
  function toggleMinimize(id) {
    const el = document.getElementById(id);
    if (!el) return;
    el.classList.toggle('minimized');
    el.querySelector('.wbtn.minimize').textContent = el.classList.contains('minimized') ? '+' : '−';
  }

  // ── Selection ─────────────────────────────────
  function selectWidget(id) {
    document.querySelectorAll('.widget.selected').forEach(el => el.classList.remove('selected'));
    const el = document.getElementById(id);
    if (el) {
      el.classList.add('selected');
      bringToFront(id);
    }
    App.state.selectedWidgetId = id;
    App.emit('selection:changed', id);
  }

  function deselectAll() {
    document.querySelectorAll('.widget.selected').forEach(el => el.classList.remove('selected'));
    App.state.selectedWidgetId = null;
    App.emit('selection:changed', null);
  }

  // ── Bring to front ────────────────────────────
  function bringToFront(id) {
    const el = document.getElementById(id);
    if (el) el.style.zIndex = ++_zTop;
  }

  // ── Refresh all ───────────────────────────────
  function refreshAll() {
    API.invalidate();
    const p = App.currentPage();
    if (!p) return;
    Object.keys(p.widgets).forEach(id => _loadData(id));
    API.checkStatus();
  }

  // ── Auto-position ─────────────────────────────
  let _autoCounter = 0;
  function _autoX() { return 40 + (_autoCounter % 6) * 32; }
  function _autoY() { _autoCounter++; return 40 + (_autoCounter % 6) * 32; }

  // ── Empty hint ────────────────────────────────
  function _checkEmpty() {
    const p = App.currentPage();
    const hint = document.getElementById('empty-hint');
    if (hint) hint.style.display = (!p || Object.keys(p.widgets).length === 0) ? 'block' : 'none';
  }

  // ── Refresh on auto-refresh event ─────────────
  App.on('refresh:all', refreshAll);

  // ── Update footer source when profile changes ─
  App.on('profiles:changed', () => {
    const p = App.currentPage();
    if (!p) return;
    Object.keys(p.widgets).forEach(id => {
      const el = document.getElementById(`footer-src-${id}`);
      if (el) el.textContent = App.getApiBase();
    });
  });

  return {
    REGISTRY,
    addWidget, removeWidget, restoreWidget, duplicateWidget,
    selectWidget, deselectAll, bringToFront,
    refreshAll, toggleMinimize,
  };
})();
