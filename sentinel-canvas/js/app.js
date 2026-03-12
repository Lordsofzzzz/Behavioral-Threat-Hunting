/* ══════════════════════════════════════════════
   SENTINEL CANVAS — APP STATE & INIT
   ══════════════════════════════════════════════ */

const App = (() => {
  // ── Global State ──────────────────────────────
  const state = {
    pages: [],           // [{ id, name, widgets: {id: widgetData} }]
    currentPageId: null,
    selectedWidgetId: null,
    apiProfiles: [],     // [{ name, url }]
    activeProfileIdx: 0,
    startTime: Date.now(),
    refreshTimer: null,
    REFRESH_MS: 30000,
  };

  // ── Event Bus ─────────────────────────────────
  const listeners = {};
  const on  = (ev, fn) => { (listeners[ev] = listeners[ev] || []).push(fn); };
  const off = (ev, fn) => { listeners[ev] = (listeners[ev]||[]).filter(f=>f!==fn); };
  const emit = (ev, data) => { (listeners[ev]||[]).forEach(fn => fn(data)); };

  // ── Helpers ───────────────────────────────────
  function uid() {
    return `_${Math.random().toString(36).slice(2,9)}`;
  }

  function esc(str) {
    return String(str ?? '')
      .replace(/&/g, '&amp;')
      .replace(/</g, '&lt;')
      .replace(/>/g, '&gt;')
      .replace(/"/g, '&quot;')
      .replace(/'/g, '&#x27;');
  }

  const VALID_SEVERITIES = new Set(['CRITICAL','WARNING','INFO']);
  function sevClass(val) {
    const u = String(val ?? '').toUpperCase();
    return VALID_SEVERITIES.has(u) ? u : 'WARNING';
  }

  // ── Page Management ───────────────────────────
  function addPage(name, silent=false) {
    const id = uid();
    state.pages.push({ id, name: name || `Page ${state.pages.length+1}`, widgets: {} });
    if (!state.currentPageId) state.currentPageId = id;
    emit('pages:changed');
    if (!silent) History.push({ type:'addPage', pageId: id, page: JSON.parse(JSON.stringify(state.pages[state.pages.length-1])) });
    return id;
  }

  function removePage(id) {
    if (state.pages.length <= 1) { Toast.show('Cannot remove the last page', 'warn'); return; }
    const idx = state.pages.findIndex(p=>p.id===id);
    if (idx === -1) return;
    History.push({ type:'removePage', page: JSON.parse(JSON.stringify(state.pages[idx])), idx });
    state.pages.splice(idx, 1);
    if (state.currentPageId === id) {
      state.currentPageId = state.pages[Math.max(0, idx-1)].id;
      emit('page:switched', state.currentPageId);
    }
    emit('pages:changed');
  }

  function switchPage(id) {
    if (state.currentPageId === id) return;
    Canvas.savePage(state.currentPageId);
    state.currentPageId = id;
    state.selectedWidgetId = null;
    Canvas.restorePage(id);
    emit('page:switched', id);
    emit('selection:changed', null);
  }

  function renamePage(id, name) {
    const p = state.pages.find(p=>p.id===id);
    if (!p) return;
    const old = p.name;
    p.name = name.trim() || old;
    emit('pages:changed');
    History.push({ type:'renamePage', pageId: id, oldName: old, newName: p.name });
  }

  function currentPage() {
    return state.pages.find(p=>p.id===state.currentPageId);
  }

  // ── API Profile Management ─────────────────────
  function getApiBase() {
    const p = state.apiProfiles[state.activeProfileIdx];
    return p ? p.url : 'http://localhost:8888';
  }

  function addProfile(name, url) {
    state.apiProfiles.push({ name, url });
    emit('profiles:changed');
  }

  function removeProfile(idx) {
    state.apiProfiles.splice(idx, 1);
    if (state.activeProfileIdx >= state.apiProfiles.length)
      state.activeProfileIdx = Math.max(0, state.apiProfiles.length - 1);
    emit('profiles:changed');
  }

  // ── Auto-refresh ──────────────────────────────
  function startAutoRefresh() {
    if (state.refreshTimer) clearInterval(state.refreshTimer);
    state.refreshTimer = setInterval(() => {
      emit('refresh:all');
    }, state.REFRESH_MS);
  }

  function stopAutoRefresh() {
    if (state.refreshTimer) clearInterval(state.refreshTimer);
  }

  // ── Persist to localStorage ───────────────────
  function saveToStorage() {
    try {
      Canvas.savePage(state.currentPageId);
      const data = {
        pages: state.pages,
        currentPageId: state.currentPageId,
        apiProfiles: state.apiProfiles,
        activeProfileIdx: state.activeProfileIdx,
        theme: ThemeEngine.current(),
        gridSnap: Canvas.getGridSnap(),
        gridSize: Canvas.getGridSize(),
      };
      localStorage.setItem('sentinel_canvas_v2', JSON.stringify(data));
    } catch(e) { /* storage unavailable */ }
  }

  function loadFromStorage() {
    try {
      const raw = localStorage.getItem('sentinel_canvas_v2');
      if (!raw) return false;
      const data = JSON.parse(raw);
      state.pages = data.pages || [];
      state.currentPageId = data.currentPageId || (state.pages[0]?.id ?? null);
      state.apiProfiles = data.apiProfiles || [{ name: 'Local', url: 'http://localhost:8888' }];
      state.activeProfileIdx = data.activeProfileIdx || 0;
      if (data.theme) ThemeEngine.apply(data.theme);
      if (data.gridSnap !== undefined) Canvas.setGridSnap(data.gridSnap);
      if (data.gridSize) Canvas.setGridSize(data.gridSize);
      return true;
    } catch(e) { return false; }
  }

  // ── Serialise / export layout ─────────────────
  function exportLayout() {
    Canvas.savePage(state.currentPageId);
    return {
      version: 2,
      pages: state.pages,
      currentPageId: state.currentPageId,
      apiProfiles: state.apiProfiles,
      activeProfileIdx: state.activeProfileIdx,
      theme: ThemeEngine.current(),
      gridSnap: Canvas.getGridSnap(),
      gridSize: Canvas.getGridSize(),
    };
  }

  function importLayout(data) {
    if (!data || data.version !== 2) {
      // try upgrading v1
      if (data?.version === 1) {
        data = upgradeV1(data);
      } else {
        Toast.show('Incompatible layout format', 'error');
        return;
      }
    }
    // Clear current canvas
    Canvas.clearAll();
    state.pages = data.pages || [];
    state.currentPageId = data.currentPageId || state.pages[0]?.id;
    state.apiProfiles = data.apiProfiles || state.apiProfiles;
    state.activeProfileIdx = data.activeProfileIdx || 0;
    if (data.theme) ThemeEngine.apply(data.theme);
    Canvas.restorePage(state.currentPageId);
    emit('pages:changed');
    emit('page:switched', state.currentPageId);
    Toast.show(`Loaded ${state.pages.reduce((s,p)=>s+Object.keys(p.widgets).length,0)} widgets`, 'success');
  }

  function upgradeV1(old) {
    const pageId = uid();
    return {
      version: 2,
      pages: [{
        id: pageId,
        name: 'Page 1',
        widgets: (old.widgets||[]).reduce((acc, w, i) => {
          const id = uid();
          acc[id] = { ...w, id };
          return acc;
        }, {})
      }],
      currentPageId: pageId,
      apiProfiles: [{ name: 'Local', url: old.apiBase || 'http://localhost:8888' }],
      activeProfileIdx: 0,
    };
  }

  // ── Init ──────────────────────────────────────
  function init() {
    const restored = loadFromStorage();
    if (!restored || state.pages.length === 0) {
      addPage('Page 1', true);
    }
    startAutoRefresh();

    // Save on visibility change / unload
    document.addEventListener('visibilitychange', () => {
      if (document.hidden) saveToStorage();
    });
    window.addEventListener('beforeunload', saveToStorage);

    // Periodic auto-save
    setInterval(saveToStorage, 60000);
  }

  return {
    state, on, off, emit, uid, esc, sevClass,
    addPage, removePage, switchPage, renamePage, currentPage,
    getApiBase, addProfile, removeProfile,
    startAutoRefresh, stopAutoRefresh,
    saveToStorage, loadFromStorage,
    exportLayout, importLayout, init,
  };
})();