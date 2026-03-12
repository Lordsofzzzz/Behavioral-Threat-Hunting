/* ══════════════════════════════════════════════
   SENTINEL CANVAS — API CLIENT
   ══════════════════════════════════════════════ */

const API = (() => {
  const _cache = {};
  const CACHE_TTL = 10000; // 10s cache to avoid hammering API

  async function fetch_(endpoint) {
    const url = `${App.getApiBase()}${endpoint}`;
    const now = Date.now();
    if (_cache[url] && (now - _cache[url].ts) < CACHE_TTL) {
      return _cache[url].data;
    }
    const res = await fetch(url, { signal: AbortSignal.timeout(8000) });
    if (!res.ok) throw new Error(`HTTP ${res.status}`);
    const data = await res.json();
    _cache[url] = { ts: now, data };
    return data;
  }

  function invalidate() {
    Object.keys(_cache).forEach(k => delete _cache[k]);
  }

  async function checkStatus() {
    const dot  = document.getElementById('statusDot');
    const text = document.getElementById('statusText');
    dot.className = 'status-dot checking';
    text.textContent = 'checking…';
    try {
      await fetch_('/api/stats');
      const host = App.getApiBase().replace(/^https?:\/\//, '');
      dot.className  = 'status-dot online';
      text.textContent = `${host} — online`;
      return true;
    } catch {
      dot.className  = 'status-dot offline';
      text.textContent = 'API offline';
      return false;
    }
  }

  async function getStats()     { return fetch_('/api/stats'); }
  async function getAlerts()    { return fetch_('/api/alerts'); }
  async function getIncidents() { return fetch_('/api/incidents'); }

  return { fetch: fetch_, invalidate, checkStatus, getStats, getAlerts, getIncidents };
})();
