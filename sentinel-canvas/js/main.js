/* ══════════════════════════════════════════════
   SENTINEL CANVAS — MAIN INIT
   Wires all modules together.
   ══════════════════════════════════════════════ */

document.addEventListener('DOMContentLoaded', () => {

  // ── 1. Core init ──────────────────────────────
  App.init();
  Canvas.init();
  Drag.init();
  ContextMenu.init();
  PropPanel.init();
  Shortcuts.init();
  ThemeEngine.renderSwatches(document.getElementById('theme-grid'));
  ThemeEngine.init(null); // will be overridden after App.loadFromStorage

  // ── 2. Restore persisted state ────────────────
  const restored = App.loadFromStorage();
  if (restored && App.state.pages.length > 0) {
    Canvas.restorePage(App.state.currentPageId);
  }

  // ── 3. Page tabs ──────────────────────────────
  function renderPageTabs() {
    const container = document.getElementById('page-tabs');
    container.innerHTML = '';
    App.state.pages.forEach(page => {
      const tab = document.createElement('div');
      tab.className = `page-tab ${page.id === App.state.currentPageId ? 'active' : ''}`;
      tab.dataset.pageId = page.id;
      tab.innerHTML = `
        <span class="page-tab-name">${App.esc(page.name)}</span>
        <span class="page-tab-close" title="Remove page">×</span>
      `;

      // Switch page
      tab.addEventListener('click', e => {
        if (e.target.classList.contains('page-tab-close')) {
          App.removePage(page.id);
          return;
        }
        App.switchPage(page.id);
      });

      // Rename on double-click
      const nameEl = tab.querySelector('.page-tab-name');
      nameEl.addEventListener('dblclick', e => {
        e.stopPropagation();
        nameEl.contentEditable = 'true';
        nameEl.focus();
        const sel = window.getSelection();
        const range = document.createRange();
        range.selectNodeContents(nameEl);
        sel.removeAllRanges();
        sel.addRange(range);

        const commit = () => {
          nameEl.contentEditable = 'false';
          App.renamePage(page.id, nameEl.textContent);
        };
        nameEl.addEventListener('blur', commit, { once: true });
        nameEl.addEventListener('keydown', e => {
          if (e.key === 'Enter') { e.preventDefault(); nameEl.blur(); }
          if (e.key === 'Escape') { nameEl.textContent = page.name; nameEl.blur(); }
        });
      });

      container.appendChild(tab);
    });
  }

  App.on('pages:changed', renderPageTabs);
  App.on('page:switched', () => renderPageTabs());

  document.getElementById('page-add-btn').addEventListener('click', () => {
    const id = App.addPage();
    App.switchPage(id);
  });

  renderPageTabs();

  // ── 4. Sidebar tabs ───────────────────────────
  document.querySelectorAll('.sidebar-tab').forEach(tab => {
    tab.addEventListener('click', () => {
      document.querySelectorAll('.sidebar-tab').forEach(t => t.classList.remove('active'));
      tab.classList.add('active');
      document.querySelectorAll('.sidebar-content').forEach(c => c.style.display = 'none');
      document.getElementById(`tab-${tab.dataset.tab}`).style.display = 'block';
    });
  });

  // ── 5. Widget items ───────────────────────────
  document.querySelectorAll('.widget-item[data-type]').forEach(item => {
    item.addEventListener('click', () => {
      WidgetManager.addWidget(item.dataset.type);
    });
  });

  // ── 6. Header buttons ─────────────────────────
  document.getElementById('btn-undo').addEventListener('click', () => History.undo());
  document.getElementById('btn-redo').addEventListener('click', () => History.redo());
  document.getElementById('btn-refresh').addEventListener('click', () => WidgetManager.refreshAll());

  // Sidebar + props panel toggles
  document.getElementById('btn-sidebar').addEventListener('click', () => {
    const sidebar = document.getElementById('sidebar');
    const btn = document.getElementById('btn-sidebar');
    sidebar.classList.toggle('collapsed');
    btn.classList.toggle('active');
  });
  document.getElementById('btn-props').addEventListener('click', () => {
    const panel = document.getElementById('prop-panel');
    const btn = document.getElementById('btn-props');
    panel.classList.toggle('collapsed');
    btn.classList.toggle('active');
  });

  // API status click
  document.getElementById('api-status').addEventListener('click', () => {
    API.invalidate();
    API.checkStatus();
    WidgetManager.refreshAll();
  });

  // Export dropdown
  const exportBtn = document.getElementById('btn-export');
  const exportDrop = document.getElementById('export-dropdown');
  exportBtn.addEventListener('click', e => {
    e.stopPropagation();
    exportDrop.style.display = exportDrop.style.display === 'none' ? 'block' : 'none';
  });
  document.addEventListener('mousedown', e => {
    if (!e.target.closest('#btn-export') && !e.target.closest('#export-dropdown')) {
      exportDrop.style.display = 'none';
    }
  });

  document.getElementById('export-png').addEventListener('click', () => {
    exportDrop.style.display = 'none';
    Exporter.exportPNG();
  });
  document.getElementById('export-pdf').addEventListener('click', () => {
    exportDrop.style.display = 'none';
    Exporter.exportPDF();
  });

  // Save / load layout
  document.getElementById('btn-save-layout').addEventListener('click', () => {
    exportDrop.style.display = 'none';
    const layout = App.exportLayout();
    const blob = new Blob([JSON.stringify(layout, null, 2)], { type: 'application/json' });
    const url = URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url; a.download = 'sentinel-layout.json'; a.click();
    setTimeout(() => URL.revokeObjectURL(url), 1000);
    Toast.show('Layout saved', 'success');
  });

  document.getElementById('load-layout-input').addEventListener('change', e => {
    const file = e.target.files[0];
    if (!file) return;
    const reader = new FileReader();
    reader.onload = ev => {
      try {
        App.importLayout(JSON.parse(ev.target.result));
      } catch {
        Toast.show('Failed to parse layout file', 'error');
      }
    };
    reader.readAsText(file);
    e.target.value = '';
    exportDrop.style.display = 'none';
  });

  // ── 7. Zoom controls ──────────────────────────
  document.getElementById('zoom-in').addEventListener('click',    () => Canvas.zoomIn());
  document.getElementById('zoom-out').addEventListener('click',   () => Canvas.zoomOut());
  document.getElementById('zoom-reset').addEventListener('click', () => Canvas.zoomReset());

  // ── 8. Undo/Redo button states ────────────────
  App.on('history:changed', ({ canUndo, canRedo }) => {
    const undoBtn = document.getElementById('btn-undo');
    const redoBtn = document.getElementById('btn-redo');
    undoBtn.disabled = !canUndo;
    undoBtn.style.opacity = canUndo ? '1' : '0.4';
    redoBtn.disabled = !canRedo;
    redoBtn.style.opacity = canRedo ? '1' : '0.4';
  });

  // ── 9. Settings panel ─────────────────────────
  // Snap toggle
  const snapToggle = document.getElementById('toggle-snap');
  snapToggle.addEventListener('click', () => {
    snapToggle.classList.toggle('on');
    Canvas.setGridSnap(snapToggle.classList.contains('on'));
  });

  // Grid toggle
  const gridToggle = document.getElementById('toggle-grid');
  gridToggle.addEventListener('click', () => {
    gridToggle.classList.toggle('on');
    Canvas.toggleGrid(gridToggle.classList.contains('on'));
  });

  // Grid size
  document.querySelectorAll('.grid-size-btn').forEach(btn => {
    btn.addEventListener('click', () => {
      document.querySelectorAll('.grid-size-btn').forEach(b => b.classList.remove('active'));
      btn.classList.add('active');
      Canvas.setGridSize(parseInt(btn.dataset.size));
    });
  });

  // Refresh interval
  document.getElementById('refresh-interval').addEventListener('change', e => {
    const ms = parseInt(e.target.value);
    App.stopAutoRefresh();
    if (ms > 0) {
      App.state.REFRESH_MS = ms;
      App.startAutoRefresh();
    }
  });

  // API Profiles — renderProfiles is defined at module scope below DOMContentLoaded
  // so that event-delegated handlers can call it without relying on inline onclick globals.

  document.getElementById('add-profile-btn').addEventListener('click', () => {
    const name = document.getElementById('new-profile-name').value.trim();
    const url  = document.getElementById('new-profile-url').value.trim().replace(/\/$/,'');
    if (!name || !url) { Toast.show('Enter a name and URL', 'warn'); return; }
    try { new URL(url); } catch { Toast.show('Invalid URL', 'error'); return; }
    App.addProfile(name, url);
    renderProfiles();
    document.getElementById('new-profile-name').value = '';
    document.getElementById('new-profile-url').value = '';
  });

  App.on('profiles:changed', renderProfiles);
  renderProfiles();

  // Ensure default profile exists
  if (App.state.apiProfiles.length === 0) {
    App.addProfile('Local', 'http://localhost:8888');
    renderProfiles();
  }

  // ── 10. Shortcuts modal ───────────────────────
  document.getElementById('btn-shortcuts').addEventListener('click', () => {
    document.getElementById('shortcuts-modal').style.display = 'flex';
  });
  document.getElementById('shortcuts-close').addEventListener('click', () => {
    document.getElementById('shortcuts-modal').style.display = 'none';
  });
  document.getElementById('shortcuts-modal').addEventListener('click', e => {
    if (e.target === document.getElementById('shortcuts-modal'))
      document.getElementById('shortcuts-modal').style.display = 'none';
  });

  // ── 11. Theme swatches ────────────────────────
  App.on('theme:changed', () => {
    ThemeEngine.renderSwatches(document.getElementById('theme-grid'));
  });

  // ── 12. API check ─────────────────────────────
  API.checkStatus();

  // ── 13. Page switch wiring ────────────────────
  App.on('page:switched', (pageId) => {
    Canvas.restorePage(pageId);
    document.getElementById('empty-hint').style.display =
      Object.keys(App.currentPage()?.widgets || {}).length === 0 ? 'block' : 'none';
  });

  // Attach event delegation for profile list buttons (avoids inline onclick globals)
  document.getElementById('api-profiles-list').addEventListener('click', e => {
    const useBtn    = e.target.closest('[data-profile-use]');
    const removeBtn = e.target.closest('[data-profile-remove]');
    if (useBtn) {
      App.state.activeProfileIdx = parseInt(useBtn.dataset.profileUse);
      renderProfiles();
      API.invalidate();
      API.checkStatus();
      WidgetManager.refreshAll();
    }
    if (removeBtn) {
      App.removeProfile(parseInt(removeBtn.dataset.profileRemove));
      renderProfiles();
    }
  });

  console.log('%c⬡ Sentinel Canvas v2.0 ready', 'color:#00e5ff;font-weight:bold;font-size:14px');
});

// ── renderProfiles — module scope so event handlers can always reach it ──────
function renderProfiles() {
  const list = document.getElementById('api-profiles-list');
  if (!list) return;
  list.innerHTML = App.state.apiProfiles.map((p, i) => {
    const isActive = i === App.state.activeProfileIdx;
    return `
      <div style="display:flex;align-items:center;gap:6px;padding:5px 0;border-bottom:1px solid var(--border)">
        <div style="flex:1;font-size:11px;color:var(--text2)">
          <span style="font-weight:600;color:${isActive ? 'var(--accent)' : 'var(--text)'}">${App.esc(p.name)}</span>
          <br><span style="font-family:var(--font-mono);font-size:9px">${App.esc(p.url)}</span>
        </div>
        <button data-profile-use="${i}"
          style="font-size:10px;padding:2px 7px;
          background:${isActive ? 'var(--accent-dim)' : 'var(--surface2)'};
          border:1px solid ${isActive ? 'var(--accent)' : 'var(--border)'};
          color:${isActive ? 'var(--accent)' : 'var(--text2)'};
          border-radius:3px;cursor:pointer">Use</button>
        ${App.state.apiProfiles.length > 1
          ? `<button data-profile-remove="${i}"
              style="font-size:10px;padding:2px 5px;background:transparent;
              border:1px solid var(--border);color:var(--accent2);border-radius:3px;cursor:pointer">×</button>`
          : ''}
      </div>`;
  }).join('');
}