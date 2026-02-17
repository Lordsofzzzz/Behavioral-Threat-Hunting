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
    def __init__(self, config_path='config.yaml'):
        """Initialize the sentinel with configuration"""
        self.config = self.load_config(config_path)
        self.patterns = self.load_patterns()
        self.ip_requests = defaultdict(lambda: deque(maxlen=100))
        self.ip_404s = defaultdict(lambda: deque(maxlen=50))
        self.alert_count = 0
        
        # Nginx log regex pattern
        self.log_pattern = re.compile(
            r'(?P<ip>[\d\.]+|[0-9a-fA-F:]+) - - \[(?P<datetime>[^\]]+)\] '
            r'"(?P<method>\S+) (?P<path>[^\s]+) HTTP/[^"]*" '
            r'(?P<status>\d+) (?P<size>\d+) "(?P<referer>[^"]*)" "(?P<useragent>[^"]*)"'
        )
        
        print(f"{Colors.GREEN}{Colors.BOLD}Log Sentinel Starting...{Colors.RESET}")
        print(f"{Colors.CYAN}Monitoring: {self.config['log_file']}{Colors.RESET}")
        print(f"{Colors.CYAN}Alert log: {self.config['alert_log']}{Colors.RESET}")
        print(f"{Colors.CYAN}Waiting for new log entries...{Colors.RESET}\n")
    
    def load_config(self, config_path):
        """Load configuration from YAML file"""
        try:
            with open(config_path, 'r') as f:
                return yaml.safe_load(f)
        except FileNotFoundError:
            print(f"{Colors.RED}Error: Config file not found at {config_path}{Colors.RESET}")
            sys.exit(1)
        except yaml.YAMLError as e:
            print(f"{Colors.RED}Error parsing config: {e}{Colors.RESET}")
            sys.exit(1)
    
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
                            patterns[attack_type].append(re.compile(line, re.IGNORECASE))
            except FileNotFoundError:
                print(f"{Colors.YELLOW}Warning: Pattern file not found: {filepath}{Colors.RESET}")
        
        total_patterns = sum(len(p) for p in patterns.values())
        print(f"{Colors.GREEN}Loaded {total_patterns} attack patterns{Colors.RESET}")
        return patterns
    
    def parse_log_line(self, line):
        """Parse a single Nginx log line"""
        match = self.log_pattern.match(line)
        if match:
            return match.groupdict()
        return None
    
    def check_patterns(self, text, pattern_list):
        """Check if text matches any pattern in the list"""
        decoded_text = unquote(unquote(text))  # Double decode for encoded attacks
        
        for pattern in pattern_list:
            if pattern.search(text) or pattern.search(decoded_text):
                return pattern.pattern
        return None
    
    def detect_attacks(self, log_entry):
        """Analyze log entry for various attack types"""
        alerts = []
        ip = log_entry['ip']
        path = log_entry['path']
        useragent = log_entry['useragent']
        status = int(log_entry['status'])
        
        # Skip whitelisted IPs
        if ip in self.config.get('whitelist_ips', '').split(','):
            return alerts
        
        # SQL Injection Detection
        if self.config.get('enable_sqli_detection', True):
            matched = self.check_patterns(path, self.patterns.get('sqli', []))
            if matched:
                alerts.append({
                    'type': 'SQL Injection',
                    'severity': 'CRITICAL',
                    'pattern': matched,
                    'ip': ip,
                    'path': path
                })
        
        # XSS Detection
        if self.config.get('enable_xss_detection', True):
            matched = self.check_patterns(path, self.patterns.get('xss', []))
            if matched:
                alerts.append({
                    'type': 'Cross-Site Scripting',
                    'severity': 'CRITICAL',
                    'pattern': matched,
                    'ip': ip,
                    'path': path
                })
        
        # Path Traversal Detection
        if self.config.get('enable_traversal_detection', True):
            matched = self.check_patterns(path, self.patterns.get('traversal', []))
            if matched:
                alerts.append({
                    'type': 'Path Traversal',
                    'severity': 'CRITICAL',
                    'pattern': matched,
                    'ip': ip,
                    'path': path
                })
        
        # Command Injection Detection
        if self.config.get('enable_cmdi_detection', True):
            matched = self.check_patterns(path, self.patterns.get('cmdi', []))
            if matched:
                alerts.append({
                    'type': 'Command Injection',
                    'severity': 'CRITICAL',
                    'pattern': matched,
                    'ip': ip,
                    'path': path
                })
        
        # Scanner Detection (User-Agent)
        if self.config.get('enable_scanner_detection', True):
            matched = self.check_patterns(useragent, self.patterns.get('scanner', []))
            if matched:
                alerts.append({
                    'type': 'Security Scanner',
                    'severity': 'WARNING',
                    'pattern': matched,
                    'ip': ip,
                    'useragent': useragent
                })
        
        # Rate Limiting
        if self.config.get('rate_limit_enabled', True):
            current_time = time.time()
            self.ip_requests[ip].append(current_time)
            
            # Count requests in the last minute
            threshold_time = current_time - self.config.get('rate_limit_window', 60)
            recent_requests = sum(1 for t in self.ip_requests[ip] if t > threshold_time)
            
            if recent_requests > self.config.get('rate_limit_threshold', 60):
                alerts.append({
                    'type': 'Rate Limit Exceeded',
                    'severity': 'WARNING',
                    'ip': ip,
                    'requests': recent_requests,
                    'window': self.config.get('rate_limit_window', 60)
                })
        
        # 404 Spam Detection (Reconnaissance)
        if self.config.get('enable_404_detection', True) and status == 404:
            current_time = time.time()
            self.ip_404s[ip].append(current_time)
            
            # Count 404s in the last minute
            threshold_time = current_time - 60
            recent_404s = sum(1 for t in self.ip_404s[ip] if t > threshold_time)
            
            if recent_404s > self.config.get('max_404_per_minute', 10):
                alerts.append({
                    'type': '404 Spam (Reconnaissance)',
                    'severity': 'WARNING',
                    'ip': ip,
                    'count': recent_404s
                })
        
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
            output += f"{color}Path: {alert['path'][:200]}{Colors.RESET}\n"
        if 'useragent' in alert:
            output += f"{color}User-Agent: {alert['useragent'][:100]}{Colors.RESET}\n"
        if 'requests' in alert:
            output += f"{color}Requests: {alert['requests']} in {alert['window']}s{Colors.RESET}\n"
        if 'count' in alert:
            output += f"{color}404 Count: {alert['count']} in last 60s{Colors.RESET}\n"
        
        output += f"{color}{'='*80}{Colors.RESET}\n"
        return output
    
    def log_alert(self, alert):
        """Write alert to log file"""
        timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        
        with open(self.config['alert_log'], 'a') as f:
            f.write(f"\n{'='*80}\n")
            f.write(f"[{timestamp}] {alert['type']} - {alert['severity']}\n")
            f.write(f"IP: {alert['ip']}\n")
            
            if 'pattern' in alert:
                f.write(f"Pattern: {alert['pattern']}\n")
            if 'path' in alert:
                f.write(f"Path: {alert['path']}\n")
            if 'useragent' in alert:
                f.write(f"User-Agent: {alert['useragent']}\n")
            if 'requests' in alert:
                f.write(f"Requests: {alert['requests']} in {alert['window']}s\n")
            if 'count' in alert:
                f.write(f"404 Count: {alert['count']} in last 60s\n")
    
    def tail_file(self, filename):
        """Tail a file like 'tail -f' - waits forever for new lines"""
        # Create the file if it doesn't exist
        if not os.path.exists(filename):
            open(filename, 'w').close()

        with open(filename, 'r') as f:
            f.seek(0, os.SEEK_END)  # go to end of file
            while True:             # loop forever
                line = f.readline()
                if not line:
                    time.sleep(0.1) # nothing new, wait and try again
                    continue
                yield line.strip()
    
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
                    self.alert_count += 1
                    
                    # Console output
                    if self.config.get('console_output', True):
                        print(self.format_alert(alert))
                    
                    # Log to file
                    self.log_alert(alert)
        
        except KeyboardInterrupt:
            print(f"\n\n{Colors.GREEN}Log Sentinel stopped.{Colors.RESET}")
            print(f"{Colors.CYAN}Total alerts: {self.alert_count}{Colors.RESET}")
            sys.exit(0)


if __name__ == '__main__':
    sentinel = LogSentinel()
    sentinel.run()
