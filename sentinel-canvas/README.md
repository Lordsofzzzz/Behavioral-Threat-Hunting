# Sentinel Canvas v2

A **Looker Studio-style** drag-and-drop dashboard builder for [Log Sentinel](../log-sentinel/README.md).

Build fully custom security dashboards — arrange widgets freely, switch themes, save layouts, and export to PNG or PDF.

---

## What's New in v2

- **Multi-page dashboards** — unlimited tabbed pages, rename/add/remove
- **6 built-in themes** — Cyber Dark, Clean Light, Midnight Blue, Solarized, High Contrast, Terminal Green
- **System auto theme** — follows OS dark/light preference automatically
- **Undo / Redo** — full history stack (Ctrl+Z / Ctrl+Y)
- **Grid snap + alignment guides** — snap to 16px or 32px grid, snap-to-edge between widgets
- **Widget enhancements** — rename (double-click title), duplicate, minimize, accent color
- **Right-click context menu** on every widget
- **Properties panel** — precise X/Y/W/H controls and per-widget settings
- **Multiple API profiles** — switch between environments (dev/prod) without editing code
- **Export to PNG and PDF** — via html2canvas + jsPDF
- **Keyboard shortcuts** — full set including arrow-nudge and Ctrl+D duplicate
- **Auto-save** to browser localStorage — layout persists across page refreshes
- **New widgets** — Risk Gauge, Activity Heatmap, Clock/Uptime, Notes
- **Canvas zoom & pan** — Ctrl+scroll to zoom, Alt+drag or middle-click to pan

---

## Available Widgets

| Widget | Type | Data Source |
|---|---|---|
| Stats Counters | Data | `/api/stats` |
| Alert Table | Data | `/api/alerts` |
| Attack Type Chart | Data | `/api/stats` |
| Top Attacking IPs | Data | `/api/stats` |
| Timeline | Data | `/api/stats` |
| Incidents | Data | `/api/incidents` |
| Risk Gauge | Visual | `/api/stats` |
| Activity Heatmap | Visual | `/api/stats` |
| Clock / Uptime | Visual | (local) |
| Notes | Utility | (local) |

---

## Themes

| Theme | Type |
|---|---|
| Cyber Dark | Dark (default) |
| Clean Light | Light |
| Midnight Blue | Dark |
| Solarized | Dark |
| High Contrast | Dark |
| Terminal Green | Dark |
| Auto (System) | Follows OS preference |

---

## Requirements

- Python 3.8+
- No extra Python packages
- Log Sentinel's `Dashboard-server.py` for live data (optional — widgets show errors gracefully if API is offline)

---

## Setup

1. Start Log Sentinel:
   ```bash
   cd log-sentinel/
   python sentinel.py
   python Dashboard-server.py
   ```

2. Start Sentinel Canvas:
   ```bash
   cd sentinel-canvas/
   python canvas-server.py
   ```

3. Open **http://localhost:8889** in your browser

---

## File Structure

```
sentinel-canvas/
├── canvas-server.py     # Python static file server
├── index.html           # App shell
├── css/
│   ├── base.css         # Reset, fonts, utilities
│   ├── themes.css       # All 6 theme definitions
│   ├── layout.css       # Header, sidebar, canvas, panels
│   └── widgets.css      # Widget styles
├── js/
│   ├── app.js           # Global state, event bus, page management
│   ├── theme.js         # Theme engine + system auto
│   ├── history.js       # Undo/redo stack
│   ├── api.js           # API client + caching
│   ├── canvas.js        # Zoom, pan, grid, snap, alignment guides
│   ├── drag.js          # Drag and resize controller
│   ├── renderers.js     # Widget data renderers
│   ├── widgets.js       # Widget factory and manager
│   ├── export.js        # PNG/PDF export
│   ├── ui.js            # Toast, context menu, properties panel, shortcuts
│   └── main.js          # App init and wiring
└── README.md
```

---

## Keyboard Shortcuts

| Key | Action |
|---|---|
| `Ctrl+Z` | Undo |
| `Ctrl+Y` / `Ctrl+Shift+Z` | Redo |
| `Ctrl+D` | Duplicate selected widget |
| `Ctrl+S` | Save layout to browser |
| `Delete` / `Backspace` | Remove selected widget |
| `F2` | Rename selected widget |
| `Arrow keys` | Nudge widget 8px |
| `Shift+Arrow` | Nudge widget 32px |
| `Ctrl+Scroll` | Zoom in/out |
| `Alt+Drag` | Pan canvas |
| `Escape` | Deselect / close menus |
| `?` | Toggle keyboard shortcuts help |

---

## Architecture

Sentinel Canvas is intentionally standalone — the Python server serves static files only. All data fetching, layout state, and interactivity happens entirely in the browser. This means it has zero Python dependencies beyond the stdlib and works equally well served from any static web server.

Layout state is auto-saved to `localStorage` every 60 seconds and on page unload. Use **Save Layout** to export a portable `.json` file you can share or version-control.
