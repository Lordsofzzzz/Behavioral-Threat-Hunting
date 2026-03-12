/* ══════════════════════════════════════════════
   SENTINEL CANVAS — DRAG & RESIZE
   ══════════════════════════════════════════════ */

const Drag = (() => {
  let _drag   = null;
  let _resize = null;

  function init() {
    document.addEventListener('mousemove', _onMove);
    document.addEventListener('mouseup',   _onUp);
  }

  // ── Drag ──────────────────────────────────────
  function startDrag(e, widgetId) {
    e.preventDefault();
    const el   = document.getElementById(widgetId);
    const zoom = Canvas.getZoom();
    const pos  = Canvas.screenToCanvas(e.clientX, e.clientY);

    _drag = {
      id:   widgetId,
      el,
      startX: pos.x - (parseInt(el.style.left) || 0),
      startY: pos.y - (parseInt(el.style.top)  || 0),
      origX: parseInt(el.style.left) || 0,
      origY: parseInt(el.style.top)  || 0,
    };
    el.classList.add('dragging');
    WidgetManager.bringToFront(widgetId);
  }

  // ── Resize ────────────────────────────────────
  function startResize(e, widgetId, dir) {
    e.preventDefault();
    e.stopPropagation();
    const el  = document.getElementById(widgetId);
    const pos = Canvas.screenToCanvas(e.clientX, e.clientY);

    _resize = {
      id:      widgetId,
      el,
      dir,
      startX:  pos.x,
      startY:  pos.y,
      startW:  el.offsetWidth,
      startH:  el.offsetHeight,
      origW:   el.offsetWidth,
      origH:   el.offsetHeight,
    };
    WidgetManager.bringToFront(widgetId);
  }

  function _onMove(e) {
    if (_drag) _doMove(e);
    if (_resize) _doResize(e);
  }

  function _doMove(e) {
    const { id, el, startX, startY } = _drag;
    const pos = Canvas.screenToCanvas(e.clientX, e.clientY);
    let x = pos.x - startX;
    let y = pos.y - startY;

    // Grid snap
    x = Canvas.snapVal(x);
    y = Canvas.snapVal(y);

    // Clamp to canvas
    x = Math.max(0, Math.min(Canvas.CANVAS_W - el.offsetWidth,  x));
    y = Math.max(0, Math.min(Canvas.CANVAS_H - el.offsetHeight, y));

    // Alignment guides (other widgets)
    const rects = _getAllRects(id);
    rects.push({ id, x, y, w: el.offsetWidth, h: el.offsetHeight });
    const snapped = Canvas.showGuides(rects, id);
    x = snapped.x; y = snapped.y;

    el.style.left = `${x}px`;
    el.style.top  = `${y}px`;
  }

  function _doResize(e) {
    const { id, el, dir, startX, startY, startW, startH } = _resize;
    const pos = Canvas.screenToCanvas(e.clientX, e.clientY);
    let dx = pos.x - startX;
    let dy = pos.y - startY;

    let w = startW, h = startH;
    if (dir.includes('e') || dir === 'se') w = Math.max(160, startW + dx);
    if (dir.includes('s') || dir === 'se') h = Math.max(100, startH + dy);

    w = Canvas.snapVal(w);
    h = Canvas.snapVal(h);

    el.style.width  = `${w}px`;
    el.style.height = `${h}px`;
  }

  function _onUp() {
    if (_drag) {
      const { id, el, origX, origY } = _drag;
      const newX = parseInt(el.style.left) || 0;
      const newY = parseInt(el.style.top)  || 0;
      el.classList.remove('dragging');

      // Update page state
      const p = App.currentPage();
      if (p?.widgets[id]) {
        p.widgets[id].x = newX;
        p.widgets[id].y = newY;
      }

      // Push to history if moved
      if (newX !== origX || newY !== origY) {
        History.push({ type:'moveWidget', widgetId:id, oldX:origX, oldY:origY, newX, newY });
      }
      Canvas.clearGuides();
      _drag = null;
    }

    if (_resize) {
      const { id, el, origW, origH } = _resize;
      const newW = el.offsetWidth;
      const newH = el.offsetHeight;

      // Update page state
      const p = App.currentPage();
      if (p?.widgets[id]) {
        p.widgets[id].w = newW;
        p.widgets[id].h = newH;
      }

      if (newW !== origW || newH !== origH) {
        History.push({ type:'resizeWidget', widgetId:id, oldW:origW, oldH:origH, newW, newH });
      }
      _resize = null;
    }
  }

  function _getAllRects(excludeId) {
    const rects = [];
    const p = App.currentPage();
    if (!p) return rects;
    Object.keys(p.widgets).forEach(id => {
      if (id === excludeId) return;
      const el = document.getElementById(id);
      if (!el) return;
      rects.push({
        id,
        x: parseInt(el.style.left) || 0,
        y: parseInt(el.style.top)  || 0,
        w: el.offsetWidth,
        h: el.offsetHeight,
      });
    });
    return rects;
  }

  return { init, startDrag, startResize };
})();
