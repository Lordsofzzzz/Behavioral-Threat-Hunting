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
from urllib.parse import urlparse, parse_qs

ALERTS_LOG = 'data/alerts.log'
HOST = os.getenv('DASHBOARD_HOST', '0.0.0.0')
PORT = int(os.getenv('DASHBOARD_PORT', '8888'))
INCIDENT_WINDOW_MINUTES = 10


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


def parse_alert_time(time_str):
    """Convert alert time field to datetime"""
    try:
        return datetime.strptime(time_str, '%Y-%m-%d %H:%M:%S')
    except (TypeError, ValueError):
        return None


def build_incidents(alerts, window_minutes=INCIDENT_WINDOW_MINUTES):
    """Correlate alerts into incidents by IP and time window"""
    if not alerts:
        return []

    alerts_with_time = []
    for alert in alerts:
        alert_time = parse_alert_time(alert.get('time', ''))
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
    """Build summary statistics from alerts."""
    if not alerts:
        return {
            'total': 0, 'critical': 0, 'warning': 0, 'avg_score': 0,
            'behavioral_anomalies': 0, 'incident_count': 0, 'top_ips': [],
            'attack_types': [], 'timeline': []
        }

    critical = sum(1 for a in alerts if a.get('severity') == 'CRITICAL')
    warning = sum(1 for a in alerts if a.get('severity') == 'WARNING')
    avg_score = int(sum(a.get('score', 0) for a in alerts) / len(alerts))
    behavioral_anomalies = sum(1 for a in alerts if a.get('type') == 'Behavioral Anomaly')

    ip_counts = defaultdict(int)
    type_counts = defaultdict(int)
    hour_counts = defaultdict(int)

    for a in alerts:
        if 'ip' in a: ip_counts[a['ip']] += 1
        if 'type' in a: type_counts[a['type']] += 1
        if 'time' in a:
            try: hour_counts[a['time'][:13]] += 1
            except: pass

    top_ips = sorted(ip_counts.items(), key=lambda x: x[1], reverse=True)[:10]
    attack_types = sorted(type_counts.items(), key=lambda x: x[1], reverse=True)
    timeline = sorted(hour_counts.items())[-24:]

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