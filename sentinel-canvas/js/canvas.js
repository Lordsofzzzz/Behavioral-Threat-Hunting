/* ══════════════════════════════════════════════
   SENTINEL CANVAS — CANVAS ENGINE
   Zoom, pan, grid, snap, alignment guides,
   page save/restore.
   ══════════════════════════════════════════════ */

const Canvas = (() => {
  let _zoom    = 1;
  let _panX    = 0;
  let _panY    = 0;
  let _snap    = true;
  let _gridSz  = 32;
  let _gridOn  = true;
  let _panning = false;
  let _panStart = null;

  const MIN_ZOOM = 0.25;
  const MAX_ZOOM = 2.0;
  const CANVAS_W = 3200;
  const CANVAS_H = 2000;

  // Elements
  let _wrap, _canvas, _bg;

  function init() {
    _wrap   = document.getElementById('canvas-wrap');
    _canvas = document.getElementById('canvas');
    _bg     = document.getElementById('canvas-bg');

    _canvas.style.width  = `${CANVAS_W}px`;
    _canvas.style.height = `${CANVAS_H}px`;

    _applyTransform();
    _applyGrid();
    _attachPan();
    _attachWheel();
    _attachCanvasClick();
  }

  // ── Transform ─────────────────────────────────
  function _applyTransform() {
    _canvas.style.transform = `translate(${_panX}px, ${_panY}px) scale(${_zoom})`;
    document.getElementById('zoom-level').textContent = `${Math.round(_zoom * 100)}%`;
  }

  function zoomIn()  { setZoom(_zoom + 0.1); }
  function zoomOut() { setZoom(_zoom - 0.1); }
  function zoomReset(){ setZoom(1); _panX = 0; _panY = 0; _applyTransform(); }

  function setZoom(z, cx, cy) {
    const oldZ = _zoom;
    _zoom = Math.min(MAX_ZOOM, Math.max(MIN_ZOOM, z));

    // Zoom toward cursor if provided
    if (cx !== undefined && cy !== undefined) {
      const rect = _wrap.getBoundingClientRect();
      const mx = cx - rect.left;
      const my = cy - rect.top;
      _panX = mx - (_zoom/oldZ) * (mx - _panX);
      _panY = my - (_zoom/oldZ) * (my - _panY);
    }
    _applyTransform();
  }

  // ── Grid ──────────────────────────────────────
  function _applyGrid() {
    _bg.className = '';
    if (_gridOn) {
      _bg.className = _gridSz === 16 ? 'grid-16' : 'grid-32';
    }
    _bg.style.width  = `${CANVAS_W * _zoom + 200}px`;
    _bg.style.height = `${CANVAS_H * _zoom + 200}px`;
  }

  function setGridSnap(on)   { _snap = on; }
  function getGridSnap()     { return _snap; }
  function setGridSize(sz)   { _gridSz = parseInt(sz); _applyGrid(); }
  function getGridSize()     { return _gridSz; }
  function toggleGrid(on)    { _gridOn = on; _applyGrid(); }

  function snapVal(v) {
    if (!_snap) return Math.round(v);
    return Math.round(v / _gridSz) * _gridSz;
  }

  // Convert screen coords to canvas coords
  function screenToCanvas(sx, sy) {
    const rect = _wrap.getBoundingClientRect();
    return {
      x: (sx - rect.left - _panX) / _zoom,
      y: (sy - rect.top  - _panY) / _zoom,
    };
  }

  // ── Pan ───────────────────────────────────────
  function _attachPan() {
    _wrap.addEventListener('mousedown', e => {
      // Only pan on middle-click or space+drag
      if (e.button === 1 || (e.button === 0 && e.altKey)) {
        e.preventDefault();
        _panning = true;
        _panStart = { x: e.clientX - _panX, y: e.clientY - _panY };
        _wrap.style.cursor = 'grabbing';
      }
    });
    document.addEventListener('mousemove', e => {
      if (!_panning) return;
      _panX = e.clientX - _panStart.x;
      _panY = e.clientY - _panStart.y;
      _applyTransform();
    });
    document.addEventListener('mouseup', () => {
      if (_panning) {
        _panning = false;
        _wrap.style.cursor = '';
      }
    });
  }

  function _attachWheel() {
    _wrap.addEventListener('wheel', e => {
      e.preventDefault();
      if (e.ctrlKey || e.metaKey) {
        const delta = e.deltaY > 0 ? -0.08 : 0.08;
        setZoom(_zoom + delta, e.clientX, e.clientY);
      } else {
        _panX -= e.deltaX;
        _panY -= e.deltaY;
        _applyTransform();
      }
    }, { passive: false });
  }

  function _attachCanvasClick() {
    _wrap.addEventListener('mousedown', e => {
      if (e.target === _wrap || e.target === _canvas || e.target === _bg) {
        WidgetManager.deselectAll();
      }
    });
  }

  // ── Alignment Guides ──────────────────────────
  let _guides = [];

  function showGuides(rects, movingId) {
    clearGuides();
    const THRESH = 8;
    const moving = rects.find(r=>r.id===movingId);
    if (!moving) return;

    const snapped = { x: null, y: null };
    const results = { x: moving.x, y: moving.y };

    rects.forEach(r => {
      if (r.id === movingId) return;

      // Vertical alignments (x)
      const pairs = [
        [moving.x,            r.x],
        [moving.x,            r.x + r.w],
        [moving.x + moving.w, r.x],
        [moving.x + moving.w, r.x + r.w],
        [moving.x + moving.w/2, r.x + r.w/2],
      ];
      pairs.forEach(([a, b]) => {
        if (Math.abs(a - b) < THRESH && snapped.x === null) {
          snapped.x = b - (a - moving.x);
          _addGuide('v', b);
        }
      });

      // Horizontal alignments (y)
      const hpairs = [
        [moving.y,            r.y],
        [moving.y,            r.y + r.h],
        [moving.y + moving.h, r.y],
        [moving.y + moving.h, r.y + r.h],
        [moving.y + moving.h/2, r.y + r.h/2],
      ];
      hpairs.forEach(([a, b]) => {
        if (Math.abs(a - b) < THRESH && snapped.y === null) {
          snapped.y = b - (a - moving.y);
          _addGuide('h', b);
        }
      });
    });

    return {
      x: snapped.x !== null ? snapped.x : moving.x,
      y: snapped.y !== null ? snapped.y : moving.y,
    };
  }

  function _addGuide(dir, pos) {
    const el = document.createElement('div');
    el.className = `align-guide ${dir}`;
    if (dir === 'v') el.style.left = `${pos}px`;
    else             el.style.top  = `${pos}px`;
    _canvas.appendChild(el);
    _guides.push(el);
  }

  function clearGuides() {
    _guides.forEach(g => g.remove());
    _guides = [];
  }

  // ── Page save / restore ───────────────────────
  function savePage(pageId) {
    const page = App.state.pages.find(p => p.id === pageId);
    if (!page) return;
    // Snapshot current DOM widget positions/sizes into page.widgets
    const inner = _canvas;
    inner.querySelectorAll('.widget').forEach(el => {
      const wid = el.id;
      if (page.widgets[wid]) {
        page.widgets[wid].x = parseInt(el.style.left) || 0;
        page.widgets[wid].y = parseInt(el.style.top)  || 0;
        page.widgets[wid].w = el.offsetWidth;
        page.widgets[wid].h = el.offsetHeight;
        // Capture notes content
        const notes = el.querySelector('.notes-body');
        if (notes) page.widgets[wid].notes = notes.value;
      }
    });
  }

  function restorePage(pageId) {
    // Remove all existing widgets from canvas
    clearAll();
    const page = App.state.pages.find(p => p.id === pageId);
    if (!page) return;
    Object.values(page.widgets).forEach(w => {
      WidgetManager.addWidget(w.type, { ...w, _skipHistory: true });
    });
  }

  function clearAll() {
    _canvas.querySelectorAll('.widget').forEach(el => el.remove());
    clearGuides();
  }

  function getCanvasEl() { return _canvas; }
  function getWrapEl()   { return _wrap; }
  function getZoom()     { return _zoom; }

  return {
    init, zoomIn, zoomOut, zoomReset, setZoom, getZoom,
    setGridSnap, getGridSnap, setGridSize, getGridSize, toggleGrid,
    snapVal, screenToCanvas,
    showGuides, clearGuides,
    savePage, restorePage, clearAll,
    getCanvasEl, getWrapEl,
    CANVAS_W, CANVAS_H,
  };
})();
