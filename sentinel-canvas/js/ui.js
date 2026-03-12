/* ══════════════════════════════════════════════
   SENTINEL CANVAS — UI MODULES
   Toast, ContextMenu, PropertiesPanel, Shortcuts
   ══════════════════════════════════════════════ */

// ── Toast ─────────────────────────────────────
const Toast = (() => {
  function show(msg, type='') {
    const container = document.getElementById('toast-container');
    const el = document.createElement('div');
    el.className = `toast ${type}`;
    el.textContent = msg;
    container.appendChild(el);
    requestAnimationFrame(() => {
      requestAnimationFrame(() => el.classList.add('show'));
    });
    setTimeout(() => {
      el.classList.remove('show');
      setTimeout(() => el.remove(), 250);
    }, 2500);
  }
  return { show };
})();

// ── Context Menu ──────────────────────────────
const ContextMenu = (() => {
  let _targetId = null;
  const menu = () => document.getElementById('ctx-menu');

  function show(x, y, widgetId) {
    _targetId = widgetId;
    const m = menu();
    m.innerHTML = `
      <div class="ctx-item" data-action="refresh"><span class="ctx-item-icon">↺</span>Refresh<span class="ctx-item-key">R</span></div>
      <div class="ctx-item" data-action="duplicate"><span class="ctx-item-icon">⧉</span>Duplicate<span class="ctx-item-key">D</span></div>
      <div class="ctx-item" data-action="rename"><span class="ctx-item-icon">✏</span>Rename<span class="ctx-item-key">F2</span></div>
      <div class="ctx-item" data-action="minimize"><span class="ctx-item-icon">−</span>Minimize / Restore</div>
      <div class="ctx-separator"></div>
      <div class="ctx-item" data-action="bring-front"><span class="ctx-item-icon">⬆</span>Bring to Front</div>
      <div class="ctx-item" data-action="send-back"><span class="ctx-item-icon">⬇</span>Send to Back</div>
      <div class="ctx-separator"></div>
      <div class="ctx-item danger" data-action="remove"><span class="ctx-item-icon">×</span>Remove<span class="ctx-item-key">Del</span></div>
    `;
    m.classList.add('visible');

    // Position with boundary checks
    const vw = window.innerWidth;
    const vh = window.innerHeight;
    const mw = 190; const mh = 240;
    m.style.left = `${Math.min(x, vw-mw-8)}px`;
    m.style.top  = `${Math.min(y, vh-mh-8)}px`;

    m.querySelectorAll('.ctx-item').forEach(item => {
      item.addEventListener('click', () => {
        hide();
        _handle(item.dataset.action);
      });
    });
  }

  function _handle(action) {
    if (!_targetId) return;
    switch (action) {
      case 'refresh':     WidgetManager.refreshAll();                       break;
      case 'duplicate':   WidgetManager.duplicateWidget(_targetId);         break;
      case 'rename': {
        const el = document.querySelector(`#${_targetId} .widget-title`);
        if (el) el.dispatchEvent(new MouseEvent('dblclick', {bubbles:true}));
        break;
      }
      case 'minimize':    WidgetManager.toggleMinimize(_targetId);          break;
      case 'bring-front': WidgetManager.bringToFront(_targetId);            break;
      case 'send-back': {
        const el = document.getElementById(_targetId);
        if (el) el.style.zIndex = 1;
        break;
      }
      case 'remove':      WidgetManager.removeWidget(_targetId);            break;
    }
  }

  function hide() {
    menu().classList.remove('visible');
    _targetId = null;
  }

  function init() {
    document.addEventListener('mousedown', e => {
      if (!e.target.closest('#ctx-menu')) hide();
    });
    document.addEventListener('keydown', e => {
      if (e.key === 'Escape') hide();
    });
  }

  return { show, hide, init };
})();

// ── Properties Panel ──────────────────────────
const PropPanel = (() => {
  function render(widgetId) {
    const panel = document.getElementById('prop-content');
    if (!panel) return;

    if (!widgetId) {
      panel.innerHTML = `
        <div class="prop-no-selection">
          <div class="prop-no-selection-icon">◻</div>
          <div class="prop-no-selection-text">Select a widget to see its properties</div>
        </div>`;
      return;
    }

    const p = App.currentPage();
    const w = p?.widgets[widgetId];
    if (!w) return;
    const el = document.getElementById(widgetId);
    if (!el) return;

    panel.innerHTML = `
      <div class="prop-group">
        <div class="prop-group-label">Widget</div>
        <div class="prop-row">
          <span class="prop-label">Title</span>
        </div>
        <input class="prop-input full" id="prop-title" value="${App.esc(w.title)}" />
      </div>

      <div class="prop-group">
        <div class="prop-group-label">Position</div>
        <div class="prop-row">
          <span class="prop-label">X</span>
          <input class="prop-input" id="prop-x" type="number" value="${parseInt(el.style.left)||0}" />
          <span class="prop-label">Y</span>
          <input class="prop-input" id="prop-y" type="number" value="${parseInt(el.style.top)||0}" />
        </div>
        <div class="prop-row">
          <span class="prop-label">W</span>
          <input class="prop-input" id="prop-w" type="number" value="${el.offsetWidth}" />
          <span class="prop-label">H</span>
          <input class="prop-input" id="prop-h" type="number" value="${el.offsetHeight}" />
        </div>
      </div>

      <div class="prop-group">
        <div class="prop-group-label">Accent Color</div>
        <div style="display:flex;gap:6px;flex-wrap:wrap;">
          ${['default','red','green','yellow','purple','blue'].map(c => `
            <div class="prop-color-chip ${w.accent===c?'active':''}" data-color="${c}"
              style="width:24px;height:24px;border-radius:4px;cursor:pointer;border:2px solid ${w.accent===c?'var(--text)':'transparent'};
              background:${_colorMap(c)}"
              title="${c}"></div>
          `).join('')}
        </div>
      </div>

      <div class="prop-group">
        <div class="prop-group-label">Actions</div>
        <button class="prop-btn" id="prop-refresh">↺ Refresh Data</button>
        <button class="prop-btn" id="prop-duplicate">⧉ Duplicate Widget</button>
        <button class="prop-btn" id="prop-minimize">− Minimize / Restore</button>
        <button class="prop-btn danger" id="prop-remove">× Remove Widget</button>
      </div>
    `;

    // Bind inputs
    document.getElementById('prop-title').addEventListener('change', e => {
      const newTitle = e.target.value.trim() || w.title;
      const titleEl = el.querySelector('.widget-title');
      if (titleEl) titleEl.textContent = newTitle;
      History.push({ type:'renameWidget', widgetId, oldTitle:w.title, newTitle });
      w.title = newTitle;
    });

    ['x','y','w','h'].forEach(prop => {
      document.getElementById(`prop-${prop}`).addEventListener('change', e => {
        const val = parseInt(e.target.value) || 0;
        if (prop === 'x') { el.style.left   = `${val}px`; w.x = val; }
        if (prop === 'y') { el.style.top    = `${val}px`; w.y = val; }
        if (prop === 'w') { el.style.width  = `${val}px`; w.w = val; }
        if (prop === 'h') { el.style.height = `${val}px`; w.h = val; }
      });
    });

    panel.querySelectorAll('.prop-color-chip').forEach(chip => {
      chip.addEventListener('click', () => {
        const c = chip.dataset.color;
        el.dataset.accent = c;
        w.accent = c;
        render(widgetId);
      });
    });

    document.getElementById('prop-refresh').addEventListener('click', () => {
      const body = document.getElementById(`body_${widgetId}`);
      if (body) {
        // trigger reload via WidgetManager
        App.emit('widget:refresh', widgetId);
      }
    });
    document.getElementById('prop-duplicate').addEventListener('click', () => WidgetManager.duplicateWidget(widgetId));
    document.getElementById('prop-minimize').addEventListener('click', () => WidgetManager.toggleMinimize(widgetId));
    document.getElementById('prop-remove').addEventListener('click', () => {
      WidgetManager.removeWidget(widgetId);
    });
  }

  function _colorMap(c) {
    return { default:'var(--accent)', red:'var(--accent2)', green:'var(--accent3)',
             yellow:'var(--warn)', purple:'var(--purple)', blue:'var(--blue)' }[c] || 'var(--accent)';
  }

  function init() {
    App.on('selection:changed', id => render(id));
    App.on('widget:refresh', id => {
      // re-trigger load
      const el = document.getElementById(id);
      if (el) el.querySelector('.wbtn.refresh')?.click();
    });
  }

  return { render, init };
})();

// ── Keyboard Shortcuts ────────────────────────
const Shortcuts = (() => {
  function init() {
    document.addEventListener('keydown', e => {
      // Don't fire when typing in inputs
      const tag = document.activeElement?.tagName;
      if (['INPUT','TEXTAREA','SELECT'].includes(tag)) return;
      if (document.activeElement?.contentEditable === 'true') return;

      const sel = App.state.selectedWidgetId;

      if ((e.ctrlKey || e.metaKey) && e.key === 'z' && !e.shiftKey) {
        e.preventDefault(); History.undo(); return;
      }
      if ((e.ctrlKey || e.metaKey) && (e.key === 'y' || (e.key === 'z' && e.shiftKey))) {
        e.preventDefault(); History.redo(); return;
      }
      if ((e.ctrlKey || e.metaKey) && e.key === 's') {
        e.preventDefault(); App.saveToStorage(); Toast.show('Saved', 'success'); return;
      }
      if ((e.ctrlKey || e.metaKey) && e.key === 'd' && sel) {
        e.preventDefault(); WidgetManager.duplicateWidget(sel); return;
      }
      if (e.key === 'Delete' || e.key === 'Backspace') {
        if (sel) { WidgetManager.removeWidget(sel); return; }
      }
      if (e.key === 'F2' && sel) {
        const el = document.querySelector(`#${sel} .widget-title`);
        if (el) el.dispatchEvent(new MouseEvent('dblclick', {bubbles:true}));
        return;
      }
      if (e.key === 'Escape') {
        WidgetManager.deselectAll();
        ContextMenu.hide();
        return;
      }
      // Arrow nudge
      if (sel && ['ArrowLeft','ArrowRight','ArrowUp','ArrowDown'].includes(e.key)) {
        e.preventDefault();
        const wEl = document.getElementById(sel);
        if (!wEl) return;
        const step = e.shiftKey ? 32 : 8;
        const x = parseInt(wEl.style.left)||0;
        const y = parseInt(wEl.style.top)||0;
        let nx = x, ny = y;
        if (e.key === 'ArrowLeft')  nx = x - step;
        if (e.key === 'ArrowRight') nx = x + step;
        if (e.key === 'ArrowUp')    ny = y - step;
        if (e.key === 'ArrowDown')  ny = y + step;
        wEl.style.left = `${Math.max(0,nx)}px`;
        wEl.style.top  = `${Math.max(0,ny)}px`;
        const p = App.currentPage();
        if (p?.widgets[sel]) { p.widgets[sel].x = nx; p.widgets[sel].y = ny; }
        return;
      }
      if (e.key === '?' || (e.shiftKey && e.key === '/')) {
        const m = document.getElementById('shortcuts-modal');
        if (m) m.style.display = m.style.display === 'none' ? 'flex' : 'none';
      }
    });
  }
  return { init };
})();