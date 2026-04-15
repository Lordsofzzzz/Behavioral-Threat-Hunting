#!/usr/bin/env python3
"""Docker demo simulator for Log Sentinel.
Writes representative attack traffic into data/test_access.log.
"""

import time
import os
from datetime import datetime, timezone

LOG_FILE = "data/test_access.log"
START_DELAY_SECONDS = 6
DELAY_BETWEEN_EVENTS = 0.7


def write_line(ip, path, status, useragent):
    ts = datetime.now(timezone.utc).strftime("%d/%b/%Y:%H:%M:%S +0000")
    line = f'{ip} - - [{ts}] "GET {path} HTTP/1.1" {status} 1234 "-" "{useragent}"\n'
    os.makedirs(os.path.dirname(LOG_FILE), exist_ok=True)
    with open(LOG_FILE, "a", encoding="utf-8") as f:
        f.write(line)


def main():
    print(f"[simulator] waiting {START_DELAY_SECONDS}s for sentinel startup...")
    time.sleep(START_DELAY_SECONDS)

    events = [
        ("192.168.1.10", "/home", 200, "Mozilla/5.0"),
        ("192.168.1.10", "/products?id=3", 200, "Mozilla/5.0"),
        ("203.0.113.10", "/login.php?id=1%27%20UNION%20SELECT%201--", 200, "curl/8.0"),
        ("10.0.0.5", "/comment?text=<script>alert(1)</script>", 200, "Firefox/120.0"),
        ("172.16.1.9", "/download?file=../../../../etc/passwd", 404, "wget/1.20"),
        ("198.51.100.22", "/ping?host=8.8.8.8;cat /etc/passwd", 500, "Python/3.11"),
        ("198.18.0.9", "/admin", 404, "sqlmap/1.7"),
    ]

    # Create a small burst to trigger behavioral/rate-style logic
    burst_ip = "198.18.0.30"
    for i in range(18):
        path = "/home" if i < 15 else "/admin/hidden"
        events.append((burst_ip, path, 200, "Mozilla/5.0"))

    for ip, path, status, ua in events:
        write_line(ip, path, status, ua)
        print(f"[simulator] wrote: {ip} {path}")
        time.sleep(DELAY_BETWEEN_EVENTS)

    print("[simulator] done. Check dashboard at http://localhost:8888")


if __name__ == "__main__":
    main()
