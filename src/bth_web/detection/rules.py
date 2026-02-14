import re
from typing import Optional, Dict, Any, List

SIGNATURES = {
    "SQL Injection": [
        r"union\s+select",
        r"or\s+['\"]?1['\"]?\s*=\s*['\"]?1['\"]?",
        r"insert\s+into",
        r"xp_cmdshell",
        r"sleep\(",
        r"benchmark\(",
    ],
    "XSS": [
        r"<\s*script",
        r"javascript:",
        r"onerror\s*=",
        r"onload\s*=",
    ],
    "Directory Traversal": [
        r"\.\./",
        r"%2e%2e%2f",
        r"/etc/passwd",
        r"boot\.ini",
        r"winnt/system32",
    ],
}

def detect_signature(url: str) -> Optional[str]:
    u = url or ""
    for name, patterns in SIGNATURES.items():
        for p in patterns:
            if re.search(p, u, re.IGNORECASE):
                return name
    return None

def behavioral_detections(metrics: dict, thresholds: dict) -> List[Dict[str, Any]]:
    dets: List[Dict[str, Any]] = []

    unique_paths = metrics.get("unique_paths", 0)
    ratio_404 = metrics.get("ratio_404", 0.0)
    login_attempts = metrics.get("login_attempts", 0)
    login_fail_ratio = metrics.get("login_fail_ratio", 0.0)

    # Scanner: lots of unique paths + high 404 ratio
    if (
        unique_paths >= thresholds.get("scanner_unique_paths_per_min", 30)
        and ratio_404 >= thresholds.get("scanner_404_ratio", 0.6)
    ):
        dets.append({
            "type": "Recon/Scanning",
            "severity": "high",
            "reason": f"High unique path probing ({unique_paths}) with high 404 ratio ({ratio_404:.2f})",
            "mitre": ["T1595"],  # Active Scanning (approx mapping)
        })

    # Bruteforce: lots of login attempts with high failure ratio
    if (
        login_attempts >= thresholds.get("bruteforce_login_attempts_per_5min", 15)
        and login_fail_ratio >= thresholds.get("bruteforce_fail_ratio", 0.8)
    ):
        dets.append({
            "type": "Brute Force",
            "severity": "high",
            "reason": f"High login attempts ({login_attempts}) with fail ratio ({login_fail_ratio:.2f})",
            "mitre": ["T1110"],
        })

    return dets

def make_detection(ev: dict, det_type: str, severity: str, reason: str, **extra) -> Dict[str, Any]:
    d = {
        "ts": ev.get("ts"),
        "src_ip": ev.get("src_ip"),
        "user_agent": ev.get("user_agent"),
        "path": ev.get("path"),
        "url": ev.get("url"),
        "detection_type": det_type,
        "severity": severity,
        "reason": reason,
    }
    d.update(extra)
    return d
