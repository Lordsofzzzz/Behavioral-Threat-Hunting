/* ══════════════════════════════════════════════
   SENTINEL CANVAS — UNDO / REDO HISTORY
   ══════════════════════════════════════════════ */

const History = (() => {
  const MAX = 80;
  let stack = [];
  let ptr   = -1;     // points to current state
  let _pause = false;

  function push(action) {
    if (_pause) return;
    // Drop redo branch
    stack = stack.slice(0, ptr + 1);
    stack.push(action);
    if (stack.length > MAX) stack.shift();
    ptr = stack.length - 1;
    App.emit('history:changed', { canUndo: canUndo(), canRedo: canRedo() });
  }

  function canUndo() { return ptr >= 0; }
  function canRedo() { return ptr < stack.length - 1; }

  function undo() {
    if (!canUndo()) return;
    const action = stack[ptr--];
    _pause = true;
    applyUndo(action);
    _pause = false;
    App.emit('history:changed', { canUndo: canUndo(), canRedo: canRedo() });
    Toast.show('Undo', 'success');
  }

  function redo() {
    if (!canRedo()) return;
    const action = stack[++ptr];
    _pause = true;
    applyRedo(action);
    _pause = false;
    App.emit('history:changed', { canUndo: canUndo(), canRedo: canRedo() });
    Toast.show('Redo', 'success');
  }

  function applyUndo(action) {
    switch (action.type) {
      case 'addWidget':
        WidgetManager.removeWidget(action.widgetId, true);
        break;
      case 'removeWidget':
        WidgetManager.restoreWidget(action.widget);
        break;
      case 'moveWidget': {
        const el = document.getElementById(action.widgetId);
        if (el) {
          el.style.left = `${action.oldX}px`;
          el.style.top  = `${action.oldY}px`;
          const p = App.currentPage();
          if (p?.widgets[action.widgetId]) {
            p.widgets[action.widgetId].x = action.oldX;
            p.widgets[action.widgetId].y = action.oldY;
          }
        }
        break;
      }
      case 'resizeWidget': {
        const el = document.getElementById(action.widgetId);
        if (el) {
          el.style.width  = `${action.oldW}px`;
          el.style.height = `${action.oldH}px`;
          const p = App.currentPage();
          if (p?.widgets[action.widgetId]) {
            p.widgets[action.widgetId].w = action.oldW;
            p.widgets[action.widgetId].h = action.oldH;
          }
        }
        break;
      }
      case 'renameWidget': {
        const p = App.currentPage();
        if (p?.widgets[action.widgetId]) {
          p.widgets[action.widgetId].title = action.oldTitle;
          const titleEl = document.querySelector(`#${action.widgetId} .widget-title`);
          if (titleEl) titleEl.textContent = action.oldTitle;
        }
        break;
      }
      case 'addPage':
        App.removePage(action.pageId);
        break;
      case 'removePage': {
        // Re-insert page at idx
        App.state.pages.splice(action.idx, 0, action.page);
        App.emit('pages:changed');
        break;
      }
      case 'renamePage': {
        const pg = App.state.pages.find(p=>p.id===action.pageId);
        if (pg) { pg.name = action.oldName; App.emit('pages:changed'); }
        break;
      }
    }
  }

  function applyRedo(action) {
    switch (action.type) {
      case 'addWidget':
        WidgetManager.restoreWidget(action.widget);
        break;
      case 'removeWidget':
        WidgetManager.removeWidget(action.widgetId, true);
        break;
      case 'moveWidget': {
        const el = document.getElementById(action.widgetId);
        if (el) {
          el.style.left = `${action.newX}px`;
          el.style.top  = `${action.newY}px`;
          const p = App.currentPage();
          if (p?.widgets[action.widgetId]) {
            p.widgets[action.widgetId].x = action.newX;
            p.widgets[action.widgetId].y = action.newY;
          }
        }
        break;
      }
      case 'resizeWidget': {
        const el = document.getElementById(action.widgetId);
        if (el) {
          el.style.width  = `${action.newW}px`;
          el.style.height = `${action.newH}px`;
          const p = App.currentPage();
          if (p?.widgets[action.widgetId]) {
            p.widgets[action.widgetId].w = action.newW;
            p.widgets[action.widgetId].h = action.newH;
          }
        }
        break;
      }
      case 'renameWidget': {
        const p = App.currentPage();
        if (p?.widgets[action.widgetId]) {
          p.widgets[action.widgetId].title = action.newTitle;
          const titleEl = document.querySelector(`#${action.widgetId} .widget-title`);
          if (titleEl) titleEl.textContent = action.newTitle;
        }
        break;
      }
      case 'addPage':
        // Restore the exact original page so IDs stay stable across undo/redo
        App.state.pages.push(JSON.parse(JSON.stringify(action.page)));
        App.emit('pages:changed');
        break;
      case 'removePage':
        App.removePage(action.pageId);
        break;
      case 'renamePage': {
        const pg = App.state.pages.find(p=>p.id===action.pageId);
        if (pg) { pg.name = action.newName; App.emit('pages:changed'); }
        break;
      }
    }
  }

  function clear() {
    stack = []; ptr = -1;
    App.emit('history:changed', { canUndo: false, canRedo: false });
  }

  return { push, undo, redo, clear, canUndo, canRedo };
})();