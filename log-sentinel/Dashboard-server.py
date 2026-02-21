#!/usr/bin/env python3
"""
Log Sentinel Dashboard Server
Serves the dashboard and provides API endpoints to read alerts.log
"""

import json
import os
import re
from datetime import datetime
from collections import defaultdict
from http.server import HTTPServer, BaseHTTPRequestHandler


ALERTS_LOG = 'data/alerts.log'
HOST = 'localhost'
PORT = 8888
INCIDENT_WINDOW_MINUTES = 10


def parse_alerts():
    """Parse alerts.log into structured data"""
    alerts = []

    alert_file = ALERTS_LOG if os.path.exists(ALERTS_LOG) else 'alerts.log'

    if not os.path.exists(alert_file):
        return alerts

    with open(alert_file, 'r') as f:
        content = f.read()

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

    return alerts


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


def build_stats(alerts):
    """Build summary statistics from alerts"""
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
        if self.path == '/':
            self.serve_dashboard()
        elif self.path == '/api/alerts':
            self.serve_alerts()
        elif self.path == '/api/stats':
            self.serve_stats()
        elif self.path == '/api/incidents':
            self.serve_incidents()
        else:
            self.send_response(404)
            self.end_headers()

    def serve_dashboard(self):
        dashboard_path = os.path.join(os.path.dirname(__file__), 'dashboard.html')
        with open(dashboard_path, 'rb') as f:
            content = f.read()
        self.send_response(200)
        self.send_header('Content-Type', 'text/html')
        self.end_headers()
        self.wfile.write(content)

    def serve_alerts(self):
        alerts = parse_alerts()
        alerts.reverse()  # newest first
        data = json.dumps(alerts[-100:])  # last 100
        self.send_response(200)
        self.send_header('Content-Type', 'application/json')
        self.send_header('Access-Control-Allow-Origin', '*')
        self.end_headers()
        self.wfile.write(data.encode())

    def serve_stats(self):
        alerts = parse_alerts()
        stats = build_stats(alerts)
        data = json.dumps(stats)
        self.send_response(200)
        self.send_header('Content-Type', 'application/json')
        self.send_header('Access-Control-Allow-Origin', '*')
        self.end_headers()
        self.wfile.write(data.encode())

    def serve_incidents(self):
        alerts = parse_alerts()
        incidents = build_incidents(alerts)
        data = json.dumps(incidents[:100])
        self.send_response(200)
        self.send_header('Content-Type', 'application/json')
        self.send_header('Access-Control-Allow-Origin', '*')
        self.end_headers()
        self.wfile.write(data.encode())

    def log_message(self, format, *args):
        pass  # suppress request logs


if __name__ == '__main__':
    server = HTTPServer((HOST, PORT), DashboardHandler)
    print(f"Log Sentinel Dashboard running at http://{HOST}:{PORT}")
    print("Press Ctrl+C to stop.")
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        print("\nDashboard stopped.")
