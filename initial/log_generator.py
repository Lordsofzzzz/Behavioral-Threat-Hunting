import time
import random

# The file we will write to
log_file = "access.log"

# Sample malicious payloads
attacks = [
    "/login.php?user=admin' OR '1'='1",
    "/search?q=<script>alert('XSS')</script>",
    "/../../etc/passwd",
    "/admin.php?id=1 UNION SELECT 1,2,3--",
    "/cgi-bin/test-cgi?%2e%2e/%2e%2e/%2e%2e/winnt/system32/cmd.exe?/c+dir"
]

# Sample safe URLs
safe = [
    "/index.html",
    "/about.php",
    "/contact.html",
    "/products/item123",
    "/style.css"
]

print(f"[*] Simulating traffic to {log_file}...")

while True:
    # 30% chance of attack, 70% chance of safe traffic
    if random.random() < 0.3:
        url = random.choice(attacks)
        ip = "192.168.1.66" # The "Attacker" IP
        status = 200
    else:
        url = random.choice(safe)
        ip = "10.0.0.5"     # The "Safe" IP
        status = 200

    # Common Log Format (standard Nginx/Apache format)
    # IP - - [Date] "METHOD URL PROTOCOL" Status Bytes
    timestamp = time.strftime("%d/%b/%Y:%H:%M:%S +0000")
    log_entry = f'{ip} - - [{timestamp}] "GET {url} HTTP/1.1" {status} 1024\n'

    with open(log_file, "a") as f:
        f.write(log_entry)
        print(f"Written: {url}")

    time.sleep(2) # Wait 2 seconds between logs
