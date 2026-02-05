import time
import re
import os

# CONFIGURATION
LOG_FILE = "access.log"

# ATTACK SIGNATURES (Regex patterns)
signatures = {
    "SQL Injection": [
        r"union.*select",       # UNION based
        r"OR\s+['\"]1['\"]\s*=\s*['\"]1", # Basic OR check
        r"insert\s+into",       # INSERT attempts
        r"xp_cmdshell"          # MSSQL specific
    ],
    "XSS (Cross Site Scripting)": [
        r"<script>",
        r"javascript:",
        r"onerror=",
        r"onload="
    ],
    "Directory Traversal": [
        r"\.\./",               # Standard ../
        r"/etc/passwd",         # Linux shadow file
        r"boot\.ini"            # Windows boot file
    ]
}

def parse_log_line(line):
    """
    Extracts the IP and URL from a standard Combined Log Format line.
    Regex explanation:
    ^(\S+) -> Capture the IP at the start
    .*?\"(GET|POST|PUT|HEAD) -> Skip to the Method
    \s+    -> Space
    (.*?)\s+ -> Capture the URL
    """
    regex = r'^(\S+) .*?\"(?:GET|POST|PUT|HEAD) (.*?) HTTP'
    match = re.search(regex, line)
    if match:
        return match.group(1), match.group(2) # Returns (IP, URL)
    return None, None

def check_for_threats(ip, url):
    """
    Scans the URL against our signatures.
    """
    for threat_name, patterns in signatures.items():
        for pattern in patterns:
            # re.I means case-insensitive (detects SELECT and select)
            if re.search(pattern, url, re.I):
                return threat_name
    return None

def monitor_log():
    print(f"[*] Monitoring {LOG_FILE} for attacks...")
    print("[*] Press Ctrl+C to stop.")

    # 1. Open the file
    try:
        f = open(LOG_FILE, "r")
    except FileNotFoundError:
        print(f"[!] Error: {LOG_FILE} not found. Run log_generator.py first!")
        return

    # 2. Go to the end of the file (skip old logs)
    f.seek(0, os.SEEK_END)

    # 3. Infinite Loop
    while True:
        line = f.readline()
        if not line:
            time.sleep(0.1) # Sleep briefly if no new data
            continue

        # We have a new line! Process it.
        ip, url = parse_log_line(line)

        if ip and url:
            threat = check_for_threats(ip, url)
            
            if threat:
                print(f"\n[!!!] ALERT DETECTED [!!!]")
                print(f"Type: {threat}")
                print(f"IP:   {ip}")
                print(f"URL:  {url}")
                print("-" * 30)
            else:
                # Optional: Print safe traffic just to see it working
                # print(f"[OK] {url}")
                pass

if __name__ == "__main__":
    monitor_log()
