/* ══════════════════════════════════════════════
   SENTINEL CANVAS — THEME ENGINE
   ══════════════════════════════════════════════ */

const ThemeEngine = (() => {
  const THEMES = [
    {
      id: 'cyber-dark',
      name: 'Cyber Dark',
      isDark: true,
      preview: 'linear-gradient(135deg, #080b10 0%, #00e5ff22 50%, #ff456022 100%)',
    },
    {
      id: 'clean-light',
      name: 'Clean Light',
      isDark: false,
      preview: 'linear-gradient(135deg, #f0f4f8 0%, #0066ff15 50%, #e53e3e10 100%)',
    },
    {
      id: 'midnight',
      name: 'Midnight Blue',
      isDark: true,
      preview: 'linear-gradient(135deg, #060d1f 0%, #4d9fff20 50%, #0a1428 100%)',
    },
    {
      id: 'solarized',
      name: 'Solarized',
      isDark: true,
      preview: 'linear-gradient(135deg, #002b36 0%, #2aa19830 60%, #073642 100%)',
    },
    {
      id: 'high-contrast',
      name: 'High Contrast',
      isDark: true,
      preview: 'linear-gradient(135deg, #000 0%, #ffff0020 50%, #00ff0015 100%)',
    },
    {
      id: 'terminal',
      name: 'Terminal',
      isDark: true,
      preview: 'linear-gradient(135deg, #030a03 0%, #39ff1425 50%, #0a160a 100%)',
    },
  ];

  let _current = 'cyber-dark';
  let _mediaQuery = null;

  function getThemes() { return THEMES; }

  function current() { return _current; }

  function isDark(id) {
    const t = THEMES.find(t => t.id === (id || _current));
    return t ? t.isDark : true;
  }

  function apply(id, animate=true) {
    const theme = THEMES.find(t => t.id === id);
    if (!theme) return;
    _current = id;

    if (animate) {
      document.body.classList.add('theme-transition');
      setTimeout(() => document.body.classList.remove('theme-transition'), 400);
    }

    document.documentElement.setAttribute('data-theme', id);
    App.emit('theme:changed', id);
  }

  function applySystem() {
    // Listen for system preference
    if (_mediaQuery) {
      _mediaQuery.removeEventListener('change', _onSystemChange);
    }
    _mediaQuery = window.matchMedia('(prefers-color-scheme: dark)');
    _onSystemChange({ matches: _mediaQuery.matches });
    _mediaQuery.addEventListener('change', _onSystemChange);
    _current = 'system';
  }

  function _onSystemChange(e) {
    apply(e.matches ? 'cyber-dark' : 'clean-light', true);
  }

  function stopSystem() {
    if (_mediaQuery) {
      _mediaQuery.removeEventListener('change', _onSystemChange);
      _mediaQuery = null;
    }
  }

  // Build theme swatches in sidebar
  function renderSwatches(container) {
    container.innerHTML = '';
    THEMES.forEach(t => {
      const sw = document.createElement('div');
      sw.className = `theme-swatch ${_current === t.id ? 'active' : ''}`;
      sw.dataset.themeId = t.id;
      sw.innerHTML = `
        <div class="theme-swatch-preview" style="background:${t.preview}"></div>
        <div class="theme-swatch-name">${App.esc(t.name)}</div>
      `;
      sw.addEventListener('click', () => {
        stopSystem();
        apply(t.id);
        renderSwatches(container);
      });
      container.appendChild(sw);
    });

    // System auto option
    const sys = document.createElement('div');
    sys.className = `theme-swatch ${_current === 'system' ? 'active' : ''}`;
    sys.innerHTML = `
      <div class="theme-swatch-preview" style="background:linear-gradient(135deg, #f0f4f8 50%, #080b10 50%)"></div>
      <div class="theme-swatch-name">Auto (System)</div>
    `;
    sys.addEventListener('click', () => {
      applySystem();
      renderSwatches(container);
    });
    container.appendChild(sys);
  }

  // Init: apply stored or default
  function init(storedTheme) {
    if (storedTheme === 'system') {
      applySystem();
    } else {
      apply(storedTheme || 'cyber-dark', false);
    }
  }

  return { getThemes, current, isDark, apply, applySystem, stopSystem, renderSwatches, init };
})();
