#!/usr/bin/env python3
"""
Log Sentinel - Lightweight Network Intrusion Detection System
Monitors Nginx access logs in real-time for web-based attacks
"""

import re
import time
import sys
import os
from collections import defaultdict, deque
from datetime import datetime
from urllib.parse import unquote
import yaml


class Colors:
    """ANSI color codes for terminal output"""
    RED = '\033[91m'
    YELLOW = '\033[93m'
    GREEN = '\033[92m'
    BLUE = '\033[94m'
    MAGENTA = '\033[95m'
    CYAN = '\033[96m'
    WHITE = '\033[97m'
    RESET = '\033[0m'
    BOLD = '\033[1m'


class LogSentinel:
    DEFAULT_CONFIG = {
        'log_file': 'data/test_access.log',
        'alert_log': 'data/alerts.log',
        'console_output': True,
        'enable_sqli_detection': True,
        'enable_xss_detection': True,
        'enable_traversal_detection': True,
        'enable_cmdi_detection': True,
        'enable_scanner_detection': True,
        'rate_limit_enabled': True,
        'rate_limit_threshold': 60,
        'rate_limit_window': 60,
        'enable_404_detection': True,
        'max_404_per_minute': 10,
        'min_alert_level': 1,
        'whitelist_ips': '127.0.0.1,::1',
        'dedup_enabled': True,
        'dedup_window_seconds': 30,
        'max_path_length': 200,
        'enable_behavioral_detection': True,
        'behavior_baseline_min_requests': 20,
        'behavior_rate_spike_multiplier': 2.5,
        'behavior_new_endpoint_min_history': 15,
        'behavior_new_ua_min_history': 15
    }

    def __init__(self, config_path='config.yaml'):
        """Initialize the sentinel with configuration"""
        self.config = self.validate_config(self.load_config(config_path))
        self.patterns = self.load_patterns()
        self.ip_requests = defaultdict(lambda: deque(maxlen=100))
        self.ip_404s = defaultdict(lambda: deque(maxlen=50))
        self.ip_baseline_rate = defaultdict(float)
        self.ip_total_requests = defaultdict(int)
        self.ip_known_paths = defaultdict(set)
        self.ip_known_useragents = defaultdict(set)
        self.recent_alerts = {}
        self.alert_count = 0
        self.suppressed_duplicates = 0
        self.whitelist_ips = {
            ip.strip() for ip in str(self.config.get('whitelist_ips', '')).split(',') if ip.strip()
        }
        self._alert_log_handle = None  # persistent file handle for alert logging
        
        # Primary Nginx combined log regex pattern
        self.log_pattern_combined = re.compile(
            r'(?P<ip>[\d\.]+|[0-9a-fA-F:]+) - - \[(?P<datetime>[^\]]+)\] '
            r'"(?P<method>\S+) (?P<path>[^\s]+) HTTP/[^"]*" '
            r'(?P<status>\d+) (?P<size>\d+) "(?P<referer>[^"]*)" "(?P<useragent>[^"]*)"'
        )

        # Fallback: common format without referer/user-agent
        self.log_pattern_common = re.compile(
            r'(?P<ip>[\d\.]+|[0-9a-fA-F:]+) - - \[(?P<datetime>[^\]]+)\] '
            r'"(?P<method>\S+) (?P<path>[^\s]+) HTTP/[^"]*" '
            r'(?P<status>\d+) (?P<size>\d+|-)'
        )
        
        print(f"{Colors.GREEN}{Colors.BOLD}Log Sentinel Starting...{Colors.RESET}")
        print(f"{Colors.CYAN}Monitoring: {self.config['log_file']}{Colors.RESET}")
        print(f"{Colors.CYAN}Alert log: {self.config['alert_log']}{Colors.RESET}")
        print(f"{Colors.CYAN}Waiting for new log entries...{Colors.RESET}\n")
    
    def load_config(self, config_path):
        """Load configuration from YAML file"""
        try:
            with open(config_path, 'r') as f:
                loaded = yaml.safe_load(f) or {}
                if not isinstance(loaded, dict):
                    raise yaml.YAMLError("Top-level config must be a YAML mapping")
                return loaded
        except FileNotFoundError:
            print(f"{Colors.RED}Error: Config file not found at {config_path}{Colors.RESET}")
            sys.exit(1)
        except yaml.YAMLError as e:
            print(f"{Colors.RED}Error parsing config: {e}{Colors.RESET}")
            sys.exit(1)

    def validate_config(self, loaded_config):
        """Merge defaults and validate key configuration values"""
        config = dict(self.DEFAULT_CONFIG)
        config.update(loaded_config)

        integer_fields = [
            'rate_limit_threshold',
            'rate_limit_window',
            'max_404_per_minute',
            'min_alert_level',
            'dedup_window_seconds',
            'max_path_length',
            'behavior_baseline_min_requests',
            'behavior_new_endpoint_min_history',
            'behavior_new_ua_min_history'
        ]

        float_fields = ['behavior_rate_spike_multiplier']

        for field in integer_fields:
            try:
                config[field] = int(config.get(field, self.DEFAULT_CONFIG[field]))
            except (TypeError, ValueError):
                print(f"{Colors.YELLOW}Warning: Invalid value for {field}, using default {self.DEFAULT_CONFIG[field]}{Colors.RESET}")
                config[field] = self.DEFAULT_CONFIG[field]

        for field in float_fields:
            try:
                config[field] = float(config.get(field, self.DEFAULT_CONFIG[field]))
            except (TypeError, ValueError):
                print(f"{Colors.YELLOW}Warning: Invalid value for {field}, using default {self.DEFAULT_CONFIG[field]}{Colors.RESET}")
                config[field] = self.DEFAULT_CONFIG[field]

        bool_fields = [
            'console_output',
            'enable_sqli_detection',
            'enable_xss_detection',
            'enable_traversal_detection',
            'enable_cmdi_detection',
            'enable_scanner_detection',
            'rate_limit_enabled',
            'enable_404_detection',
            'dedup_enabled',
            'enable_behavioral_detection'
        ]

        for field in bool_fields:
            value = config.get(field, self.DEFAULT_CONFIG[field])
            if isinstance(value, bool):
                continue
            if isinstance(value, str):
                config[field] = value.strip().lower() in ('true', '1', 'yes', 'on')
            else:
                config[field] = bool(value)

        if config['rate_limit_threshold'] <= 0:
            config['rate_limit_threshold'] = self.DEFAULT_CONFIG['rate_limit_threshold']
        if config['rate_limit_window'] <= 0:
            config['rate_limit_window'] = self.DEFAULT_CONFIG['rate_limit_window']
        if config['max_404_per_minute'] <= 0:
            config['max_404_per_minute'] = self.DEFAULT_CONFIG['max_404_per_minute']
        if config['dedup_window_seconds'] < 0:
            config['dedup_window_seconds'] = self.DEFAULT_CONFIG['dedup_window_seconds']
        if config['max_path_length'] < 50:
            config['max_path_length'] = self.DEFAULT_CONFIG['max_path_length']
        if config['behavior_baseline_min_requests'] < 5:
            config['behavior_baseline_min_requests'] = self.DEFAULT_CONFIG['behavior_baseline_min_requests']
        if config['behavior_new_endpoint_min_history'] < 5:
            config['behavior_new_endpoint_min_history'] = self.DEFAULT_CONFIG['behavior_new_endpoint_min_history']
        if config['behavior_new_ua_min_history'] < 5:
            config['behavior_new_ua_min_history'] = self.DEFAULT_CONFIG['behavior_new_ua_min_history']
        if config['behavior_rate_spike_multiplier'] < 1.2:
            config['behavior_rate_spike_multiplier'] = self.DEFAULT_CONFIG['behavior_rate_spike_multiplier']

        if not config.get('log_file'):
            print(f"{Colors.RED}Error: 'log_file' must be configured{Colors.RESET}")
            sys.exit(1)
        if not config.get('alert_log'):
            print(f"{Colors.RED}Error: 'alert_log' must be configured{Colors.RESET}")
            sys.exit(1)

        return config
    
    def load_patterns(self):
        """Load attack patterns from rule files"""
        patterns = {}
        rule_files = {
            'sqli': 'rules/sqli_patterns.txt',
            'xss': 'rules/xss_patterns.txt',
            'traversal': 'rules/traversal_patterns.txt',
            'cmdi': 'rules/cmdi_patterns.txt',
            'scanner': 'rules/scanner_patterns.txt'
        }
        
        for attack_type, filepath in rule_files.items():
            patterns[attack_type] = []
            try:
                with open(filepath, 'r') as f:
                    for line in f:
                        line = line.strip()
                        if line and not line.startswith('#'):
                            try:
                                patterns[attack_type].append(re.compile(line, re.IGNORECASE))
                            except re.error:
                                print(f"{Colors.YELLOW}Warning: Invalid regex in {filepath}: {line}{Colors.RESET}")
            except FileNotFoundError:
                print(f"{Colors.YELLOW}Warning: Pattern file not found: {filepath}{Colors.RESET}")
        
        total_patterns = sum(len(p) for p in patterns.values())
        print(f"{Colors.GREEN}Loaded {total_patterns} attack patterns{Colors.RESET}")
        return patterns
    
    def parse_log_line(self, line):
        """Parse a single Nginx log line"""
        match = self.log_pattern_combined.match(line)
        if match:
            return match.groupdict()

        fallback = self.log_pattern_common.match(line)
        if fallback:
            entry = fallback.groupdict()
            entry['referer'] = '-'
            entry['useragent'] = '-'
            return entry
        return None

    def normalize_path(self, path):
        """Normalize request path for robust detection"""
        decoded = unquote(unquote(path or ''))
        normalized = decoded.replace('\\\\', '/')
        normalized = re.sub(r'/+', '/', normalized)
        return normalized
    
    def check_patterns(self, text, pattern_list):
        """Check if text matches any pattern in the list"""
        raw_text = text or ''
        decoded_text = unquote(unquote(raw_text))  # Double decode for encoded attacks

        for pattern in pattern_list:
            if pattern.search(raw_text) or pattern.search(decoded_text):
                return pattern.pattern
        return None

    def score_to_severity(self, score):
        """Map score to severity labels used by dashboard"""
        return 'CRITICAL' if score >= 80 else 'WARNING'

    def score_alert(self, alert_type, path='', useragent='', recent_requests=0, recent_404s=0, anomaly_ratio=1.0):
        """Build a risk score from detection context"""
        type_base = {
            'SQL Injection': 90,
            'Cross-Site Scripting': 90,
            'Path Traversal': 88,
            'Command Injection': 92,
            'Security Scanner': 70,
            'Rate Limit Exceeded': 60,
            '404 Spam (Reconnaissance)': 65,
            'Behavioral Anomaly': 72
        }
        score = type_base.get(alert_type, 60)

        decoded_path = unquote(unquote(path or ''))
        if decoded_path != (path or ''):
            score += 5
        if len(decoded_path) > 120:
            score += 5
        if any(token in decoded_path.lower() for token in ['union', '<script', '../', ';', '|', '$(']):
            score += 5

        if recent_requests >= self.config.get('rate_limit_threshold', 60) * 2:
            score += 10
        if recent_404s >= self.config.get('max_404_per_minute', 10) * 2:
            score += 8

        if anomaly_ratio >= 3:
            score += 12
        elif anomaly_ratio >= 2:
            score += 8

        if useragent and useragent != '-' and len(useragent) < 12:
            score += 3

        return min(score, 100)

    def build_reasons(self, matched_pattern=None, decoded=False, recent_requests=0, recent_404s=0, notes=None):
        """Build explainable reason codes for an alert"""
        reasons = []

        if matched_pattern:
            reasons.append(f"matched-pattern:{matched_pattern}")
        if decoded:
            reasons.append("decoded-encoded-payload")
        if recent_requests:
            window = self.config.get('rate_limit_window', 60)
            reasons.append(f"request-rate:{recent_requests}/{window}s")
        if recent_404s:
            reasons.append(f"recent-404-count:{recent_404s}/60s")
        if notes:
            reasons.extend(notes)

        return reasons

    def should_emit_alert(self, alert):
        """Suppress duplicate alerts and enforce min_alert_level"""
        # Enforce minimum alert level
        severity_rank = {'INFO': 0, 'WARNING': 1, 'CRITICAL': 2}
        min_level = self.config.get('min_alert_level', 1)
        alert_rank = severity_rank.get(alert.get('severity', 'WARNING'), 1)
        if alert_rank < min_level:
            return False

        if not self.config.get('dedup_enabled', True):
            return True

        key_parts = [
            alert.get('type', ''),
            alert.get('ip', ''),
            alert.get('pattern', ''),
            alert.get('path', ''),
            alert.get('useragent', '')
        ]
        fingerprint = '|'.join(key_parts)
        current_time = time.time()
        window = self.config.get('dedup_window_seconds', 30)

        last_seen = self.recent_alerts.get(fingerprint)
        self.recent_alerts[fingerprint] = current_time

        # Prune stale entries to prevent unbounded memory growth
        if len(self.recent_alerts) > 10000:
            cutoff = current_time - window
            self.recent_alerts = {
                k: v for k, v in self.recent_alerts.items() if v > cutoff
            }

        if last_seen and current_time - last_seen < window:
            self.suppressed_duplicates += 1
            return False
        return True
    
    def detect_attacks(self, log_entry):
        """Analyze log entry for various attack types using streamlined detection logic"""
        alerts = []
        ip = log_entry['ip']
        if ip in self.whitelist_ips:
            return alerts

        path = log_entry.get('path', '')
        normalized_path = self.normalize_path(path)
        useragent = log_entry.get('useragent', '-')
        status = int(log_entry['status'])
        is_decoded = normalized_path != (path or '')

        current_time = time.time()
        self.ip_requests[ip].append(current_time)
        threshold_time = current_time - self.config.get('rate_limit_window', 60)
        recent_requests = sum(1 for t in self.ip_requests[ip] if t > threshold_time)

        previous_baseline = self.ip_baseline_rate[ip]
        if previous_baseline == 0:
            self.ip_baseline_rate[ip] = float(recent_requests)
        else:
            self.ip_baseline_rate[ip] = (0.9 * previous_baseline) + (0.1 * float(recent_requests))

        history_count = self.ip_total_requests[ip]
        self.ip_total_requests[ip] += 1

        # 1. Pattern-based detection (DRY)
        attack_map = {
            'sqli': 'SQL Injection',
            'xss': 'Cross-Site Scripting',
            'traversal': 'Path Traversal',
            'cmdi': 'Command Injection',
            'scanner': 'Security Scanner'
        }

        for rule_key, alert_type in attack_map.items():
            if self.config.get(f'enable_{rule_key}_detection', True):
                text_to_check = useragent if rule_key == 'scanner' else normalized_path
                matched = self.check_patterns(text_to_check, self.patterns.get(rule_key, []))
                if matched:
                    score = self.score_alert(alert_type, path=normalized_path, useragent=useragent)
                    alert = {
                        'type': alert_type,
                        'severity': self.score_to_severity(score),
                        'score': score,
                        'pattern': matched,
                        'reasons': self.build_reasons(matched_pattern=matched, decoded=is_decoded),
                        'ip': ip
                    }
                    if rule_key == 'scanner':
                        alert['useragent'] = useragent
                    else:
                        alert['path'] = normalized_path
                    alerts.append(alert)

        # 2. Rate Limiting
        if self.config.get('rate_limit_enabled', True):
            if recent_requests > self.config.get('rate_limit_threshold', 60):
                score = self.score_alert('Rate Limit Exceeded', path=normalized_path, useragent=useragent, recent_requests=recent_requests)
                alerts.append({
                    'type': 'Rate Limit Exceeded',
                    'severity': self.score_to_severity(score),
                    'score': score,
                    'reasons': self.build_reasons(recent_requests=recent_requests),
                    'ip': ip,
                    'requests': recent_requests,
                    'window': self.config.get('rate_limit_window', 60)
                })

        # 3. 404 Spam Detection
        if self.config.get('enable_404_detection', True) and status == 404:
            self.ip_404s[ip].append(current_time)
            threshold_404 = current_time - 60
            recent_404s = sum(1 for t in self.ip_404s[ip] if t > threshold_404)

            if recent_404s > self.config.get('max_404_per_minute', 10):
                score = self.score_alert('404 Spam (Reconnaissance)', path=normalized_path, useragent=useragent, recent_404s=recent_404s)
                alerts.append({
                    'type': '404 Spam (Reconnaissance)',
                    'severity': self.score_to_severity(score),
                    'score': score,
                    'reasons': self.build_reasons(recent_404s=recent_404s),
                    'ip': ip,
                    'count': recent_404s
                })

        # 4. Behavioral anomaly detection
        if self.config.get('enable_behavioral_detection', True):
            self._check_behavioral_anomalies(alerts, ip, normalized_path, useragent, history_count, recent_requests, previous_baseline)

        self.ip_known_paths[ip].add(normalized_path)
        if useragent != '-':
            self.ip_known_useragents[ip].add(useragent)

        return alerts

    def _check_behavioral_anomalies(self, alerts, ip, path, useragent, history_count, recent_requests, previous_baseline):
        """Helper to detect behavioral deviations"""
        path_history_threshold = self.config.get('behavior_new_endpoint_min_history', 15)
        ua_history_threshold = self.config.get('behavior_new_ua_min_history', 15)
        baseline_min = self.config.get('behavior_baseline_min_requests', 20)
        spike_multiplier = self.config.get('behavior_rate_spike_multiplier', 2.5)

        # New Endpoint
        if history_count >= path_history_threshold and path not in self.ip_known_paths[ip]:
            score = self.score_alert('Behavioral Anomaly', path=path, useragent=useragent, recent_requests=recent_requests)
            alerts.append({'type': 'Behavioral Anomaly', 'severity': self.score_to_severity(score), 'score': score,
                          'reasons': self.build_reasons(notes=['new-endpoint-for-ip', f'ip-history:{history_count}']),
                          'ip': ip, 'path': path})

        # New User-Agent
        if useragent != '-' and history_count >= ua_history_threshold and useragent not in self.ip_known_useragents[ip]:
            score = self.score_alert('Behavioral Anomaly', path=path, useragent=useragent, recent_requests=recent_requests)
            alerts.append({'type': 'Behavioral Anomaly', 'severity': self.score_to_severity(score), 'score': score,
                          'reasons': self.build_reasons(notes=['new-useragent-for-ip', f'ip-history:{history_count}']),
                          'ip': ip, 'useragent': useragent, 'path': path})

        # Rate Spike
        if history_count >= baseline_min and previous_baseline > 0:
            anomaly_ratio = recent_requests / max(previous_baseline, 1.0)
            if anomaly_ratio >= spike_multiplier:
                score = self.score_alert('Behavioral Anomaly', path=path, useragent=useragent, recent_requests=recent_requests, anomaly_ratio=anomaly_ratio)
                alerts.append({
                    'type': 'Behavioral Anomaly', 'severity': self.score_to_severity(score), 'score': score,
                    'reasons': self.build_reasons(recent_requests=recent_requests, notes=[f'baseline-rate:{previous_baseline:.1f}', f'spike-ratio:{anomaly_ratio:.2f}x']),
                    'ip': ip, 'path': path, 'requests': recent_requests, 'window': self.config.get('rate_limit_window', 60)
                })

        self.ip_known_paths[ip].add(normalized_path)
        if useragent != '-':
            self.ip_known_useragents[ip].add(useragent)
        
        return alerts
    
    def format_alert(self, alert):
        """Format alert for console output"""
        timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        
        if alert['severity'] == 'CRITICAL':
            color = Colors.RED
            symbol = '!!'
        else:
            color = Colors.YELLOW
            symbol = '! '
        
        output = f"\n{color}{Colors.BOLD}{symbol} ALERT: {alert['type']} [{alert['severity']}]{Colors.RESET}\n"
        output += f"{color}Time: {timestamp}{Colors.RESET}\n"
        output += f"{color}IP: {alert['ip']}{Colors.RESET}\n"
        
        if 'pattern' in alert:
            output += f"{color}Pattern: {alert['pattern']}{Colors.RESET}\n"
        if 'path' in alert:
            output += f"{color}Path: {alert['path'][:self.config.get('max_path_length', 200)]}{Colors.RESET}\n"
        if 'useragent' in alert:
            output += f"{color}User-Agent: {alert['useragent'][:100]}{Colors.RESET}\n"
        if 'score' in alert:
            output += f"{color}Risk Score: {alert['score']}/100{Colors.RESET}\n"
        if 'reasons' in alert:
            output += f"{color}Reasons: {' | '.join(alert['reasons'][:4])}{Colors.RESET}\n"
        if 'requests' in alert:
            output += f"{color}Requests: {alert['requests']} in {alert['window']}s{Colors.RESET}\n"
        if 'count' in alert:
            output += f"{color}404 Count: {alert['count']} in last 60s{Colors.RESET}\n"
        
        output += f"{color}{'='*80}{Colors.RESET}\n"
        return output
    
    def log_alert(self, alert):
        """Write alert to log file using a persistent handle, rotation-safe."""
        timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        alert_path = self.config['alert_log']
        alert_dir = os.path.dirname(alert_path)
        if alert_dir:
            os.makedirs(alert_dir, exist_ok=True)

        # Detect log rotation: if the file on disk has a different inode than our
        # open handle (or has been deleted), close and reopen so writes go to the
        # new file rather than the old rotated-away one.
        if self._alert_log_handle is not None and not self._alert_log_handle.closed:
            try:
                handle_inode = os.fstat(self._alert_log_handle.fileno()).st_ino
                disk_inode = os.stat(alert_path).st_ino
                if handle_inode != disk_inode:
                    self._alert_log_handle.close()
                    self._alert_log_handle = None
            except OSError:
                self._alert_log_handle.close()
                self._alert_log_handle = None

        # Open persistent handle on first use or after rotation
        if self._alert_log_handle is None or self._alert_log_handle.closed:
            self._alert_log_handle = open(alert_path, 'a')

        f = self._alert_log_handle
        f.write(f"\n{'='*80}\n")
        f.write(f"[{timestamp}] {alert['type']} - {alert['severity']}\n")
        f.write(f"IP: {alert['ip']}\n")

        if 'pattern' in alert:
            f.write(f"Pattern: {alert['pattern']}\n")
        if 'path' in alert:
            f.write(f"Path: {alert['path']}\n")
        if 'useragent' in alert:
            f.write(f"User-Agent: {alert['useragent']}\n")
        if 'score' in alert:
            f.write(f"Risk Score: {alert['score']}/100\n")
        if 'reasons' in alert:
            f.write(f"Reasons: {' | '.join(alert['reasons'])}\n")
        if 'requests' in alert:
            f.write(f"Requests: {alert['requests']} in {alert['window']}s\n")
        if 'count' in alert:
            f.write(f"404 Count: {alert['count']} in last 60s\n")

        f.flush()  # ensure data is written to disk immediately
    
    def tail_file(self, filename):
        """Tail a file like 'tail -f', handles log rotation by detecting inode/size changes."""
        file_dir = os.path.dirname(filename)
        if file_dir:
            os.makedirs(file_dir, exist_ok=True)

        if not os.path.exists(filename):
            open(filename, 'w').close()

        f = open(filename, 'r')
        f.seek(0, os.SEEK_END)
        current_inode = os.fstat(f.fileno()).st_ino

        try:
            while True:
                line = f.readline()
                if not line:
                    time.sleep(0.1)
                    # Check for log rotation: file replaced or truncated
                    try:
                        new_stat = os.stat(filename)
                    except FileNotFoundError:
                        time.sleep(0.5)
                        continue
                    if new_stat.st_ino != current_inode or new_stat.st_size < f.tell():
                        f.close()
                        f = open(filename, 'r')
                        current_inode = os.fstat(f.fileno()).st_ino
                    continue
                yield line.strip()
        finally:
            f.close()
    
    def run(self):
        """Main monitoring loop"""
        try:
            for line in self.tail_file(self.config['log_file']):
                if not line or line.startswith('#'):
                    continue
                
                # Parse log entry
                log_entry = self.parse_log_line(line)
                if not log_entry:
                    continue
                
                # Detect attacks
                alerts = self.detect_attacks(log_entry)
                
                # Process alerts
                for alert in alerts:
                    if not self.should_emit_alert(alert):
                        continue

                    self.alert_count += 1
                    
                    # Console output
                    if self.config.get('console_output', True):
                        print(self.format_alert(alert))
                    
                    # Log to file
                    self.log_alert(alert)
        
        except KeyboardInterrupt:
            print(f"\n\n{Colors.GREEN}Log Sentinel stopped.{Colors.RESET}")
            print(f"{Colors.CYAN}Total alerts: {self.alert_count}{Colors.RESET}")
            print(f"{Colors.CYAN}Suppressed duplicates: {self.suppressed_duplicates}{Colors.RESET}")
            if self._alert_log_handle and not self._alert_log_handle.closed:
                self._alert_log_handle.close()
            sys.exit(0)


if __name__ == '__main__':
    sentinel = LogSentinel()
    sentinel.run()