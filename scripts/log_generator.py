import os
import time
import random

LOG_FILE = os.getenv("LOG_FILE", "access.log")

ATTACKS = [
    "/login.php?user=admin' OR '1'='1",
    "/search?q=<script>alert('XSS')</script>",
    "/../../etc/passwd",
    "/admin.php?id=1 UNION SELECT 1,2,3--",
    "/cgi-bin/test-cgi?%2e%2e/%2e%2e/%2e%2e/winnt/system32/cmd.exe?/c+dir",
]

SAFE = [
    "/index.html",
    "/about.php",
    "/contact.html",
    "/products/item123",
    "/style.css",
    "/images/logo.png",
]

USER_AGENTS = [
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64)",
    "Mozilla/5.0 (X11; Linux x86_64)",
    "curl/8.0.1",
    "python-requests/2.31.0",
]


def ensure_log_dir(path: str) -> None:
    d = os.path.dirname(path)
    if d:
        os.makedirs(d, exist_ok=True)


def write_line(ip: str, url: str, status: int, ua: str) -> None:
    # Example:
    # 127.0.0.1 - - [13/Feb/2026:12:07:00 +0000] "GET / HTTP/1.1" 200 1024 "-" "UA"
    timestamp = time.strftime("%d/%b/%Y:%H:%M:%S +0000")
    line = f'{ip} - - [{timestamp}] "GET {url} HTTP/1.1" {status} 1024 "-" "{ua}"\n'

    with open(LOG_FILE, "a", encoding="utf-8") as f:
        f.write(line)
        f.flush()


def main() -> None:
    ensure_log_dir(LOG_FILE)
    print(f"[*] Writing simulated traffic to {LOG_FILE} (Ctrl+C to stop)")

    while True:
        is_attack = random.random() < 0.30

        if is_attack:
            ip = "192.168.1.66"
            url = random.choice(ATTACKS)
            status = random.choice([200, 400, 403, 404, 500])
        else:
            ip = "10.0.0.5"
            url = random.choice(SAFE)
            status = 200

        ua = random.choice(USER_AGENTS)
        write_line(ip, url, status, ua)

        print(f"Wrote: {ip} {status} {url}")
        time.sleep(2)


if __name__ == "__main__":
    main()
