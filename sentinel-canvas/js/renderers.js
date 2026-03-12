/* ══════════════════════════════════════════════
   SENTINEL CANVAS — WIDGET RENDERERS
   ══════════════════════════════════════════════ */

const Renderers = (() => {
  const { esc, sevClass } = App;

  // ── Stats ─────────────────────────────────────
  async function renderStats(body) {
    const s = await API.getStats();
    body.innerHTML = `
      <div class="stats-grid">
        <div class="stat-tile c-accent">
          <div class="stat-value">${esc(s.total)}</div>
          <div class="stat-label">Total Alerts</div>
        </div>
        <div class="stat-tile c-red">
          <div class="stat-value">${esc(s.critical)}</div>
          <div class="stat-label">Critical</div>
        </div>
        <div class="stat-tile c-warn">
          <div class="stat-value">${esc(s.warning)}</div>
          <div class="stat-label">Warning</div>
        </div>
        <div class="stat-tile c-green">
          <div class="stat-value">${esc(s.avg_score)}</div>
          <div class="stat-label">Avg Score</div>
        </div>
        <div class="stat-tile c-purple">
          <div class="stat-value">${esc(s.behavioral_anomalies)}</div>
          <div class="stat-label">Anomalies</div>
        </div>
        <div class="stat-tile c-blue">
          <div class="stat-value">${esc(s.incident_count)}</div>
          <div class="stat-label">Incidents</div>
        </div>
      </div>`;
  }

  // ── Alerts ────────────────────────────────────
  async function renderAlerts(body) {
    const alerts = await API.getAlerts();
    if (!alerts.length) {
      body.innerHTML = '<div class="w-empty"><div class="w-empty-icon">🔍</div>No alerts yet</div>';
      return;
    }
    const rows = alerts.slice(0,100).map(a => {
      const score = a.score ?? 0;
      const scoreClass = score >= 80 ? 'high' : score >= 60 ? 'med' : 'low';
      const sev = sevClass(a.severity);
      return `<tr>
        <td style="color:var(--text2)">${esc((a.time||'').slice(11,19))}</td>
        <td><span class="badge ${sev}">${sev}</span></td>
        <td style="color:var(--text)">${esc(a.type||'—')}</td>
        <td style="color:var(--accent);font-family:var(--font-mono)">${esc(a.ip||'—')}</td>
        <td style="color:var(--text2)">${esc((a.path||a.useragent||'—').slice(0,40))}</td>
        <td><span class="score-pill ${scoreClass}">${esc(score)}</span></td>
      </tr>`;
    }).join('');
    body.innerHTML = `<div class="alert-table-wrap">
      <table>
        <thead><tr><th>Time</th><th>Sev</th><th>Type</th><th>IP</th><th>Path/UA</th><th>Score</th></tr></thead>
        <tbody>${rows}</tbody>
      </table>
    </div>`;
    body.classList.add('no-pad');
  }

  // ── Attacks ───────────────────────────────────
  async function renderAttacks(body) {
    const s = await API.getStats();
    const types = s.attack_types || [];
    if (!types.length) {
      body.innerHTML = '<div class="w-empty"><div class="w-empty-icon">🎯</div>No data</div>';
      return;
    }
    const max = types[0].count || 1;
    const colors = ['var(--accent)','var(--accent2)','var(--accent3)','var(--warn)','var(--purple)','var(--blue)'];
    const bars = types.map((t, i) => `
      <div class="bar-row">
        <div class="bar-label" title="${esc(t.type)}">${esc(t.type)}</div>
        <div class="bar-track">
          <div class="bar-fill" style="width:${(t.count/max*100).toFixed(1)}%;background:${colors[i%colors.length]}"></div>
        </div>
        <div class="bar-count">${esc(t.count)}</div>
      </div>`).join('');
    body.innerHTML = `<div class="bar-chart">${bars}</div>`;
  }

  // ── Top IPs ───────────────────────────────────
  async function renderIPs(body) {
    const s = await API.getStats();
    const ips = s.top_ips || [];
    if (!ips.length) {
      body.innerHTML = '<div class="w-empty"><div class="w-empty-icon">🌐</div>No data</div>';
      return;
    }
    const max = ips[0].count || 1;
    const rows = ips.map((item, i) => `
      <div class="ip-row">
        <div class="ip-rank">${i+1}</div>
        <div class="ip-addr">${esc(item.ip)}</div>
        <div class="ip-bar-track">
          <div class="ip-bar-fill" style="width:${(item.count/max*100).toFixed(1)}%"></div>
        </div>
        <div class="ip-count">${esc(item.count)}</div>
      </div>`).join('');
    body.innerHTML = `<div class="ip-list">${rows}</div>`;
  }

  // ── Timeline ──────────────────────────────────
  async function renderTimeline(body) {
    const s = await API.getStats();
    const tl = s.timeline || [];
    if (!tl.length) {
      body.innerHTML = '<div class="w-empty"><div class="w-empty-icon">📈</div>No data</div>';
      return;
    }
    const maxC = Math.max(...tl.map(t=>t.count), 1);
    const cols = tl.map(t => {
      const pct = (t.count / maxC * 100).toFixed(1);
      const label = t.hour ? t.hour.slice(11,16) : '';
      return `<div class="tl-col" title="${esc(t.hour)}: ${esc(t.count)} alerts">
        <div class="tl-bar-wrap">
          <div class="tl-bar" style="height:${pct}%"></div>
        </div>
      </div>`;
    }).join('');
    const labels = tl.map(t => {
      const label = t.hour ? t.hour.slice(11,16) : '';
      return `<div class="tl-label">${esc(label)}</div>`;
    }).join('');
    body.innerHTML = `<div class="timeline-wrap">
      <div class="tl-chart">${cols}</div>
      <div class="tl-axis"></div>
      <div class="tl-labels">${labels}</div>
    </div>`;
  }

  // ── Incidents ─────────────────────────────────
  async function renderIncidents(body) {
    const incidents = await API.getIncidents();
    if (!incidents.length) {
      body.innerHTML = '<div class="w-empty"><div class="w-empty-icon">🔗</div>No incidents</div>';
      return;
    }
    const cards = incidents.slice(0,20).map(inc => {
      const typeTags = (inc.types||[]).map(t=>`<span class="inc-type-tag">${esc(t)}</span>`).join('');
      const scoreColor = inc.max_score>=80 ? 'var(--accent2)' : inc.max_score>=60 ? 'var(--warn)' : 'var(--accent3)';
      const sev = sevClass(inc.severity);
      return `<div class="incident-card ${sev}">
        <div class="inc-top">
          <span class="inc-id">${esc(inc.id)}</span>
          <span class="inc-ip">${esc(inc.ip)}</span>
          <span class="inc-score" style="color:${scoreColor}">${esc(inc.max_score)}/100</span>
          <span class="badge ${sev}">${sev}</span>
        </div>
        <div class="inc-types">${typeTags}</div>
        <div class="inc-meta">${esc(inc.alert_count)} alerts · ${esc((inc.start||'').slice(11,16))} → ${esc((inc.end||'').slice(11,16))}</div>
      </div>`;
    }).join('');
    body.innerHTML = `<div class="incident-list">${cards}</div>`;
  }

  // ── Notes (static, no API) ────────────────────
  function renderNotes(body, savedContent) {
    body.classList.add('no-pad');
    body.innerHTML = `<textarea class="notes-body" placeholder="Type your notes here…">${esc(savedContent||'')}</textarea>`;
  }

  // ── Clock ─────────────────────────────────────
  function renderClock(body, widgetId) {
    body.innerHTML = `<div class="clock-wrap">
      <div class="clock-time" id="clock-time-${widgetId}">--:--:--</div>
      <div class="clock-date" id="clock-date-${widgetId}">---</div>
      <div class="clock-uptime" id="clock-uptime-${widgetId}">Uptime: --</div>
    </div>`;
    _tickClock(widgetId);
    // Store interval on widget el
    const el = document.getElementById(widgetId);
    if (el._clockTimer) clearInterval(el._clockTimer);
    el._clockTimer = setInterval(() => _tickClock(widgetId), 1000);
  }

  function _tickClock(widgetId) {
    const now = new Date();
    const timeEl = document.getElementById(`clock-time-${widgetId}`);
    const dateEl = document.getElementById(`clock-date-${widgetId}`);
    const upEl   = document.getElementById(`clock-uptime-${widgetId}`);
    if (!timeEl) { return; }
    timeEl.textContent = now.toLocaleTimeString();
    dateEl.textContent = now.toLocaleDateString(undefined, { weekday:'long', year:'numeric', month:'long', day:'numeric' });
    const uptimeSec = Math.floor((Date.now() - App.state.startTime) / 1000);
    const h = Math.floor(uptimeSec/3600);
    const m = Math.floor((uptimeSec%3600)/60);
    const s = uptimeSec%60;
    if (upEl) upEl.textContent = `Uptime: ${h}h ${m}m ${s}s`;
  }

  // ── Risk Gauge ────────────────────────────────
  async function renderGauge(body) {
    const s = await API.getStats();
    const score = parseFloat(s.avg_score) || 0;
    const pct = score / 100;
    const r = 60;
    const cx = 80, cy = 80;
    const circumference = Math.PI * r; // half circle
    const arcLen = pct * circumference;
    const color = score >= 80 ? 'var(--accent2)' : score >= 60 ? 'var(--warn)' : 'var(--accent3)';

    body.innerHTML = `<div class="gauge-wrap">
      <svg class="gauge-svg" width="160" height="100" viewBox="0 0 160 100">
        <path d="M ${cx-r},${cy} A ${r},${r} 0 0,1 ${cx+r},${cy}"
          fill="none" stroke="var(--surface2)" stroke-width="14" stroke-linecap="round"/>
        <path d="M ${cx-r},${cy} A ${r},${r} 0 0,1 ${cx+r},${cy}"
          fill="none" stroke="${color}" stroke-width="14" stroke-linecap="round"
          stroke-dasharray="${arcLen} ${circumference}"
          style="transition:stroke-dasharray 0.8s cubic-bezier(.4,0,.2,1)"/>
        <text x="${cx}" y="${cy-8}" class="gauge-value" fill="${color}" font-size="24" font-family="var(--font-mono)" text-anchor="middle">${score}</text>
        <text x="${cx}" y="${cy+14}" fill="var(--muted)" font-size="9" font-family="var(--font-ui)" text-anchor="middle" font-weight="700" letter-spacing="2">RISK SCORE</text>
      </svg>
      <div class="gauge-label">${score >= 80 ? 'HIGH RISK' : score >= 60 ? 'MEDIUM' : 'LOW RISK'}</div>
    </div>`;
  }

  // ── Heatmap ───────────────────────────────────
  async function renderHeatmap(body) {
    const s = await API.getStats();
    const tl = s.timeline || [];
    if (!tl.length) {
      body.innerHTML = '<div class="w-empty"><div class="w-empty-icon">🔥</div>No data</div>';
      return;
    }
    // Build 4 rows (6h buckets) × N cols
    const maxC = Math.max(...tl.map(t=>t.count), 1);
    const getColor = (v) => {
      const pct = v / maxC;
      if (pct === 0) return 'var(--surface2)';
      if (pct < 0.25) return 'var(--accent3-dim)';
      if (pct < 0.5)  return 'rgba(0,224,150,0.4)';
      if (pct < 0.75) return 'var(--warn)';
      return 'var(--accent2)';
    };

    const cells = tl.map(t => `<div class="heatmap-cell"
      style="background:${getColor(t.count)}"
      data-tip="${esc(t.hour||'')}: ${esc(t.count)}"></div>`).join('');

    body.innerHTML = `<div class="heatmap-wrap">
      <div class="heatmap-row">
        <div class="heatmap-label"></div>
        <div class="heatmap-cells">${cells}</div>
      </div>
      <div style="display:flex;justify-content:flex-end;gap:8px;margin-top:8px;font-family:var(--font-mono);font-size:9px;color:var(--muted)">
        <span style="color:var(--accent3)">■</span> Low
        <span style="color:var(--warn)">■</span> Med
        <span style="color:var(--accent2)">■</span> High
      </div>
    </div>`;
  }

  return {
    renderStats, renderAlerts, renderAttacks, renderIPs,
    renderTimeline, renderIncidents, renderNotes, renderClock,
    renderGauge, renderHeatmap,
  };
})();
