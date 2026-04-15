#!/usr/bin/env python3
"""
Log Sentinel Dashboard Server
Serves the dashboard and provides API endpoints to read alerts.log
"""

import json
import os
import re
import threading
import time
from datetime import datetime
from collections import defaultdict
from http.server import ThreadingHTTPServer, BaseHTTPRequestHandler
from typing import Optional
from urllib.parse import urlparse, parse_qs, urlencode
from urllib.request import urlopen
from urllib.error import URLError, HTTPError


ALERTS_LOG = 'data/alerts.log'
HOST = os.getenv('DASHBOARD_HOST', '0.0.0.0')
PORT = int(os.getenv('DASHBOARD_PORT', '8888'))
INCIDENT_WINDOW_MINUTES = 10
PROMETHEUS_BASE_URL = os.getenv('PROMETHEUS_BASE_URL', 'http://localhost:9090')
GRAFANA_BASE_URL = os.getenv('GRAFANA_BASE_URL', 'http://localhost:3000')

# --- Simple file-level cache for parsed alerts ---
_alerts_cache = []
_alerts_cache_key = (0.0, 0)  # (mtime, file_size) — two-factor key avoids stale cache on coarse-resolution filesystems (e.g. Windows FAT/NTFS)
_cache_lock = threading.Lock()  # guards _alerts_cache + _alerts_cache_key under ThreadingHTTPServer


def parse_alerts():
    """Parse alerts.log into structured data, with (mtime, size)-based caching.
    Thread-safe: uses _cache_lock to prevent concurrent threads from redundantly
    re-parsing the file or clobbering each other's writes."""
    global _alerts_cache, _alerts_cache_key

    alert_file = ALERTS_LOG if os.path.exists(ALERTS_LOG) else 'alerts.log'

    if not os.path.exists(alert_file):
        return []

    try:
        stat = os.stat(alert_file)
        cache_key = (stat.st_mtime, stat.st_size)
    except OSError:
        return []

    with _cache_lock:
        if cache_key == _alerts_cache_key and _alerts_cache:
            return list(_alerts_cache)  # return a copy so callers can mutate safely

        alerts = []

        try:
            with open(alert_file, 'r') as f:
                content = f.read()
        except OSError:
            return list(_alerts_cache)  # return stale cache on read error rather than empty

        # Split on separator lines
        blocks = content.split('=' * 80)

        for block in blocks:
            block = block.strip()
            if not block:
                continue

            alert = {}

            # Timestamp and type
            match = re.search(r'\[(\d{4}-\d{2}-\d{2} \d{2}:\d{2}:\d{2})\] (.+?) - (CRITICAL|WARNING)', block)
            if match:
                alert['time'] = match.group(1)
                alert['type'] = match.group(2)
                alert['severity'] = match.group(3)
            else:
                continue

            # IP
            ip_match = re.search(r'IP: (.+)', block)
            if ip_match:
                alert['ip'] = ip_match.group(1).strip()

            # Pattern
            pattern_match = re.search(r'Pattern: (.+)', block)
            if pattern_match:
                alert['pattern'] = pattern_match.group(1).strip()

            # Path
            path_match = re.search(r'Path: (.+)', block)
            if path_match:
                alert['path'] = path_match.group(1).strip()

            # User-Agent
            ua_match = re.search(r'User-Agent: (.+)', block)
            if ua_match:
                alert['useragent'] = ua_match.group(1).strip()

            # Requests (rate limit)
            req_match = re.search(r'Requests: (\d+) in (\d+)s', block)
            if req_match:
                alert['requests'] = req_match.group(1)
                alert['window'] = req_match.group(2)

            # Risk score
            score_match = re.search(r'Risk Score: (\d+)/100', block)
            if score_match:
                alert['score'] = int(score_match.group(1))

            # Explainable reasons
            reasons_match = re.search(r'Reasons: (.+)', block)
            if reasons_match:
                alert['reasons'] = [part.strip() for part in reasons_match.group(1).split('|') if part.strip()]

            # 404 count
            count_match = re.search(r'404 Count: (\d+)', block)
            if count_match:
                alert['count'] = count_match.group(1)

            alerts.append(alert)

        _alerts_cache = alerts
        _alerts_cache_key = cache_key
        return list(alerts)


def parse_alert_time(alert):
    """Convert alert time field to datetime"""
    try:
        return datetime.strptime(alert.get('time', ''), '%Y-%m-%d %H:%M:%S')
    except (TypeError, ValueError):
        return None


def build_incidents(alerts, window_minutes=INCIDENT_WINDOW_MINUTES):
    """Correlate alerts into incidents by IP and time window"""
    if not alerts:
        return []

    alerts_with_time = []
    for alert in alerts:
        alert_time = parse_alert_time(alert)
        if alert_time:
            alerts_with_time.append((alert_time, alert))

    if not alerts_with_time:
        return []

    grouped_by_ip = defaultdict(list)
    for alert_time, alert in alerts_with_time:
        ip = alert.get('ip', 'unknown')
        grouped_by_ip[ip].append((alert_time, alert))

    incidents = []
    window_seconds = window_minutes * 60

    for ip, entries in grouped_by_ip.items():
        entries.sort(key=lambda item: item[0])

        current = None
        incident_index = 0

        for alert_time, alert in entries:
            if current is None:
                incident_index += 1
                current = {
                    'id': f"INC-{ip}-{incident_index}",
                    'ip': ip,
                    'start': alert_time,
                    'end': alert_time,
                    'alerts': [alert]
                }
                continue

            gap = (alert_time - current['end']).total_seconds()
            if gap <= window_seconds:
                current['alerts'].append(alert)
                current['end'] = alert_time
            else:
                incidents.append(current)
                incident_index += 1
                current = {
                    'id': f"INC-{ip}-{incident_index}",
                    'ip': ip,
                    'start': alert_time,
                    'end': alert_time,
                    'alerts': [alert]
                }

        if current is not None:
            incidents.append(current)

    formatted = []
    for incident in incidents:
        incident_alerts = incident['alerts']
        types = sorted({a.get('type', 'Unknown') for a in incident_alerts})
        severities = [a.get('severity', 'WARNING') for a in incident_alerts]
        max_score = max((a.get('score', 0) for a in incident_alerts), default=0)
        reasons = []
        for alert in incident_alerts:
            reasons.extend(alert.get('reasons', []))

        severity = 'CRITICAL' if 'CRITICAL' in severities else 'WARNING'
        unique_reasons = list(dict.fromkeys(reasons))[:4]

        formatted.append({
            'id': incident['id'],
            'ip': incident['ip'],
            'start': incident['start'].strftime('%Y-%m-%d %H:%M:%S'),
            'end': incident['end'].strftime('%Y-%m-%d %H:%M:%S'),
            'alert_count': len(incident_alerts),
            'types': types,
            'severity': severity,
            'max_score': max_score,
            'reasons': unique_reasons
        })

    formatted.sort(key=lambda item: item['end'], reverse=True)
    return formatted


def build_stats(alerts, incidents=None):
    """Build summary statistics from alerts.
    Pass pre-built incidents to avoid calling build_incidents twice per /api/stats request."""
    if not alerts:
        return {
            'total': 0,
            'critical': 0,
            'warning': 0,
            'avg_score': 0,
            'behavioral_anomalies': 0,
            'incident_count': 0,
            'top_ips': [],
            'attack_types': [],
            'timeline': []
        }

    critical = sum(1 for a in alerts if a.get('severity') == 'CRITICAL')
    warning = sum(1 for a in alerts if a.get('severity') == 'WARNING')
    avg_score = int(sum(a.get('score', 0) for a in alerts) / len(alerts))
    behavioral_anomalies = sum(1 for a in alerts if a.get('type') == 'Behavioral Anomaly')

    # Top attacking IPs
    ip_counts = defaultdict(int)
    for a in alerts:
        if 'ip' in a:
            ip_counts[a['ip']] += 1
    top_ips = sorted(ip_counts.items(), key=lambda x: x[1], reverse=True)[:10]

    # Attack type breakdown
    type_counts = defaultdict(int)
    for a in alerts:
        if 'type' in a:
            type_counts[a['type']] += 1
    attack_types = sorted(type_counts.items(), key=lambda x: x[1], reverse=True)

    # Timeline - group by hour
    hour_counts = defaultdict(int)
    for a in alerts:
        if 'time' in a:
            try:
                hour = a['time'][:13]  # YYYY-MM-DD HH
                hour_counts[hour] += 1
            except Exception:
                pass
    timeline = sorted(hour_counts.items())[-24:]  # last 24 hours

    # Use pre-built incidents if provided, otherwise build once
    if incidents is None:
        incidents = build_incidents(alerts)

    return {
        'total': len(alerts),
        'critical': critical,
        'warning': warning,
        'avg_score': avg_score,
        'behavioral_anomalies': behavioral_anomalies,
        'incident_count': len(incidents),
        'top_ips': [{'ip': ip, 'count': count} for ip, count in top_ips],
        'attack_types': [{'type': t, 'count': count} for t, count in attack_types],
        'timeline': [{'hour': h, 'count': count} for h, count in timeline]
    }


def _parse_duration_to_seconds(duration: str, default_seconds=3600):
    """Parse simple duration strings like 15m, 1h, 2d into seconds."""
    if not duration:
        return default_seconds
    m = re.fullmatch(r'\s*(\d+)\s*([smhd])\s*', str(duration))
    if not m:
        return default_seconds
    value = int(m.group(1))
    unit = m.group(2)
    mult = {'s': 1, 'm': 60, 'h': 3600, 'd': 86400}.get(unit, 3600)
    return max(60, value * mult)


def _safe_metric_name(name: str):
    """Allow only Prometheus metric identifier format."""
    if re.fullmatch(r'[a-zA-Z_:][a-zA-Z0-9_:]*', str(name or '')):
        return name
    return None


def _safe_label_name(name: str):
    """Allow only Prometheus label identifier format."""
    if re.fullmatch(r'[a-zA-Z_][a-zA-Z0-9_]*', str(name or '')):
        return name
    return None


def _prom_get_json(path: str, params=None, timeout=8):
    params = params or {}
    query = urlencode(params)
    url = f"{PROMETHEUS_BASE_URL}{path}"
    if query:
        url = f"{url}?{query}"

    with urlopen(url, timeout=timeout) as resp:
        return json.loads(resp.read().decode('utf-8'))


def _build_grafana_embed_url(uid: str, panel_id: Optional[str] = None, theme='dark'):
    base = GRAFANA_BASE_URL.rstrip('/')
    if panel_id:
        return f"{base}/d-solo/{uid}?panelId={panel_id}&theme={theme}"
    return f"{base}/d/{uid}?theme={theme}"


class DashboardHandler(BaseHTTPRequestHandler):

    def do_GET(self):
        try:
            parsed = urlparse(self.path)
            path = parsed.path
            self._query = parse_qs(parsed.query)

            if path == '/':
                self.serve_dashboard()
            elif path == '/api/alerts':
                self.serve_alerts()
            elif path == '/api/stats':
                self.serve_stats()
            elif path == '/api/incidents':
                self.serve_incidents()
            elif path == '/api/prometheus/metrics':
                self.serve_prometheus_metrics()
            elif path == '/api/prometheus/query-range':
                self.serve_prometheus_query_range()
            elif path == '/api/grafana/embed-preview':
                self.serve_grafana_embed_preview()
            else:
                self.send_response(404)
                self.end_headers()
        except Exception:
            self.send_response(500)
            self.send_header('Content-Type', 'application/json')
            self.send_header('Access-Control-Allow-Origin', '*')
            self.end_headers()
            try:
                self.wfile.write(b'{"error":"internal server error"}')
            except (BrokenPipeError, ConnectionResetError):
                pass

    def serve_dashboard(self):
        dashboard_path = os.path.join(os.path.dirname(__file__), 'dashboard.html')
        try:
            with open(dashboard_path, 'rb') as f:
                content = f.read()
        except FileNotFoundError:
            self.send_response(404)
            self.send_header('Content-Type', 'text/plain')
            self.send_header('Access-Control-Allow-Origin', '*')
            self.end_headers()
            try:
                self.wfile.write(b'dashboard.html not found. Make sure it is in the same directory as Dashboard-server.py.')
            except (BrokenPipeError, ConnectionResetError):
                pass
            return
        self.send_response(200)
        self.send_header('Content-Type', 'text/html')
        self.send_header('Content-Length', str(len(content)))
        self.send_header('Access-Control-Allow-Origin', '*')
        self.end_headers()
        try:
            self.wfile.write(content)
        except (BrokenPipeError, ConnectionResetError):
            pass

    def _send_json(self, payload: str):
        """Helper: send a JSON response with correct headers."""
        encoded = payload.encode()
        self.send_response(200)
        self.send_header('Content-Type', 'application/json')
        self.send_header('Access-Control-Allow-Origin', '*')
        self.send_header('Content-Length', str(len(encoded)))
        self.end_headers()
        try:
            self.wfile.write(encoded)
        except (BrokenPipeError, ConnectionResetError):
            pass

    def serve_alerts(self):
        alerts = parse_alerts()
        alerts.reverse()  # newest first

        # Optional query param filters: ?severity=CRITICAL&ip=1.2.3.4&limit=50
        q = getattr(self, '_query', {})
        severity_filter = q.get('severity', [None])[0]
        ip_filter = q.get('ip', [None])[0]
        try:
            limit = int(q.get('limit', [100])[0])
            limit = max(1, min(limit, 1000))
        except (ValueError, TypeError):
            limit = 100

        if severity_filter:
            alerts = [a for a in alerts if a.get('severity', '').upper() == severity_filter.upper()]
        if ip_filter:
            alerts = [a for a in alerts if a.get('ip', '') == ip_filter]

        self._send_json(json.dumps(alerts[:limit]))

    def serve_stats(self):
        alerts = parse_alerts()
        incidents = build_incidents(alerts)          # build once
        stats = build_stats(alerts, incidents=incidents)  # reuse, don't rebuild
        self._send_json(json.dumps(stats))

    def serve_incidents(self):
        alerts = parse_alerts()
        incidents = build_incidents(alerts)
        self._send_json(json.dumps(incidents[:100]))

    def serve_prometheus_metrics(self):
        q = getattr(self, '_query', {})
        prefix = (q.get('prefix', [''])[0] or '').strip()
        limit_raw = q.get('limit', ['200'])[0]

        try:
            limit = max(1, min(int(limit_raw), 1000))
        except (TypeError, ValueError):
            limit = 200

        try:
            payload = _prom_get_json('/api/v1/label/__name__/values')
            if payload.get('status') != 'success':
                raise ValueError('prometheus non-success status')

            names = payload.get('data', [])
            if prefix:
                pfx = prefix.lower()
                names = [n for n in names if str(n).lower().startswith(pfx)]

            names = sorted(set(names))[:limit]
            self._send_json(json.dumps({'items': names}))
        except (URLError, HTTPError, TimeoutError, ValueError) as exc:
            self.send_response(502)
            self.send_header('Content-Type', 'application/json')
            self.send_header('Access-Control-Allow-Origin', '*')
            self.end_headers()
            self.wfile.write(json.dumps({'error': f'prometheus unavailable: {exc}'}).encode('utf-8'))

    def serve_prometheus_query_range(self):
        q = getattr(self, '_query', {})
        metric = _safe_metric_name((q.get('metric', [''])[0] or '').strip())
        dimension_raw = (q.get('dimension', ['none'])[0] or 'none').strip()
        range_raw = (q.get('range', ['1h'])[0] or '1h').strip()
        step_raw = (q.get('step', ['60s'])[0] or '60s').strip()

        if not metric:
            self.send_response(400)
            self.send_header('Content-Type', 'application/json')
            self.send_header('Access-Control-Allow-Origin', '*')
            self.end_headers()
            self.wfile.write(b'{"error":"invalid metric name"}')
            return

        dim = None
        if dimension_raw.lower() not in ('', 'none'):
            dim = _safe_label_name(dimension_raw)
            if not dim:
                self.send_response(400)
                self.send_header('Content-Type', 'application/json')
                self.send_header('Access-Control-Allow-Origin', '*')
                self.end_headers()
                self.wfile.write(b'{"error":"invalid dimension label"}')
                return

        # Build conservative PromQL from metric + optional grouping label.
        promql = f'sum by ({dim}) ({metric})' if dim else metric

        duration_seconds = _parse_duration_to_seconds(range_raw, default_seconds=3600)
        step_seconds = _parse_duration_to_seconds(step_raw, default_seconds=60)
        end_ts = int(time.time())
        start_ts = end_ts - duration_seconds

        try:
            payload = _prom_get_json(
                '/api/v1/query_range',
                params={
                    'query': promql,
                    'start': start_ts,
                    'end': end_ts,
                    'step': f'{step_seconds}s',
                },
            )
            if payload.get('status') != 'success':
                raise ValueError('prometheus non-success status')

            result = payload.get('data', {}).get('result', [])
            series = []
            for item in result:
                metric_meta = item.get('metric', {})
                if dim:
                    label = metric_meta.get(dim, '(unknown)')
                else:
                    label = metric

                points = []
                for ts, val in item.get('values', []):
                    try:
                        points.append({'ts': int(float(ts)), 'value': float(val)})
                    except (TypeError, ValueError):
                        continue
                series.append({'label': label, 'points': points})

            self._send_json(json.dumps({
                'metric': metric,
                'dimension': dim or 'none',
                'query': promql,
                'range': range_raw,
                'step': f'{step_seconds}s',
                'series': series,
            }))
        except (URLError, HTTPError, TimeoutError, ValueError) as exc:
            self.send_response(502)
            self.send_header('Content-Type', 'application/json')
            self.send_header('Access-Control-Allow-Origin', '*')
            self.end_headers()
            self.wfile.write(json.dumps({'error': f'prometheus query failed: {exc}'}).encode('utf-8'))

    def serve_grafana_embed_preview(self):
        q = getattr(self, '_query', {})
        uid = (q.get('uid', [''])[0] or '').strip()
        panel_id = (q.get('panelId', [''])[0] or '').strip() or None
        theme = (q.get('theme', ['dark'])[0] or 'dark').strip()

        if not re.fullmatch(r'[A-Za-z0-9_-]{3,}', uid):
            self.send_response(400)
            self.send_header('Content-Type', 'application/json')
            self.send_header('Access-Control-Allow-Origin', '*')
            self.end_headers()
            self.wfile.write(b'{"error":"invalid grafana uid"}')
            return

        if panel_id and not re.fullmatch(r'\d+', panel_id):
            self.send_response(400)
            self.send_header('Content-Type', 'application/json')
            self.send_header('Access-Control-Allow-Origin', '*')
            self.end_headers()
            self.wfile.write(b'{"error":"invalid panel id"}')
            return

        if theme not in ('dark', 'light'):
            theme = 'dark'

        self._send_json(json.dumps({
            'embed_url': _build_grafana_embed_url(uid, panel_id=panel_id, theme=theme)
        }))

    def log_message(self, format, *args):
        pass  # suppress request logs


if __name__ == '__main__':
    server = ThreadingHTTPServer((HOST, PORT), DashboardHandler)
    print(f"Log Sentinel Dashboard running at http://{HOST}:{PORT}")
    print("Press Ctrl+C to stop.")
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        print("\nDashboard stopped.")