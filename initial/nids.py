import sqlite3
from datetime import datetime
import time
import re
import os
import geoip2.database

# ==============================
# PATH CONFIGURATION (PROFESSIONAL FIX)
# ==============================
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
LOG_FILE = os.path.join(BASE_DIR, "access.log")
DB_FILE = os.path.join(BASE_DIR, "nids.db")
GEO_DB = os.path.join(BASE_DIR, "GeoLite2-City.mmdb")

# ==============================
# ATTACK SIGNATURES
# ==============================
signatures = {
    "SQL Injection": [
        r"union.*select",
        r"OR\s+['\"]1['\"]\s*=\s*['\"]1",
        r"insert\s+into",
        r"xp_cmdshell"
    ],
    "XSS (Cross Site Scripting)": [
        r"<script>",
        r"javascript:",
        r"onerror=",
        r"onload="
    ],
    "Directory Traversal": [
        r"\.\./",
        r"/etc/passwd",
        r"boot\.ini"
    ]
}

# ==============================
# DATABASE INITIALIZATION
# ==============================
def init_database():
    conn = sqlite3.connect(DB_FILE)
    cursor = conn.cursor()

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS alerts (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            timestamp TEXT,
            ip TEXT,
            country TEXT,
            city TEXT,
            url TEXT,
            threat_type TEXT
        )
    """)

    cursor.execute("CREATE INDEX IF NOT EXISTS idx_ip ON alerts(ip)")
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_threat ON alerts(threat_type)")

    conn.commit()
    conn.close()

# ==============================
# GEOLOCATION LOOKUP
# ==============================
def get_geolocation(ip):
    try:
        with geoip2.database.Reader(GEO_DB) as reader:
            response = reader.city(ip)
            country = response.country.name
            city = response.city.name
            return country, city
    except:
        return "Unknown", "Unknown"

# ==============================
# SAVE ALERT
# ==============================
def save_alert(ip, url, threat_type):
    conn = sqlite3.connect(DB_FILE)
    cursor = conn.cursor()

    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    country, city = get_geolocation(ip)

    cursor.execute("""
        INSERT INTO alerts (timestamp, ip, country, city, url, threat_type)
        VALUES (?, ?, ?, ?, ?, ?)
    """, (timestamp, ip, country, city, url, threat_type))

    conn.commit()
    conn.close()

# ==============================
# LOG PARSING
# ==============================
def parse_log_line(line):
    regex = r'^(\S+) .*?\"(?:GET|POST|PUT|HEAD) (.*?) HTTP'
    match = re.search(regex, line)
    if match:
        return match.group(1), match.group(2)
    return None, None

# ==============================
# THREAT DETECTION
# ==============================
def check_for_threats(ip, url):
    for threat_name, patterns in signatures.items():
        for pattern in patterns:
            if re.search(pattern, url, re.I):
                return threat_name
    return None

# ==============================
# MAIN MONITORING FUNCTION
# ==============================
def monitor_log():
    print(f"[*] Monitoring {LOG_FILE} for attacks...")
    print("[*] Press Ctrl+C to stop.")

    try:
        f = open(LOG_FILE, "r")
    except FileNotFoundError:
        print("[!] access.log not found.")
        return

    f.seek(0, os.SEEK_END)

    while True:
        line = f.readline()
        if not line:
            time.sleep(0.1)
            continue

        ip, url = parse_log_line(line)

        if ip and url:
            threat = check_for_threats(ip, url)

            if threat:
                country, city = get_geolocation(ip)

                print("\n[!!!] ALERT DETECTED [!!!]")
                print(f"Type: {threat}")
                print(f"IP: {ip}")
                print(f"Location: {country}, {city}")
                print(f"URL: {url}")
                print("-" * 30)

                save_alert(ip, url, threat)

# ==============================
# ENTRY POINT
# ==============================
if __name__ == "__main__":
    init_database()
    monitor_log()
