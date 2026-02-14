import re
from dataclasses import dataclass
from typing import Optional, Dict, Any
from dateutil import parser as dtparser

# Example:
# 127.0.0.1 - - [13/Feb/2026:12:07:00 +0000] "GET /path?x=1 HTTP/1.1" 200 1024 "-" "UA"
LOG_RE = re.compile(
    r'^(?P<ip>\S+)\s+\S+\s+\S+\s+\[(?P<ts>[^\]]+)\]\s+'
    r'"(?P<method>[A-Z]+)\s+(?P<url>\S+)\s+(?P<proto>[^"]+)"\s+'
    r'(?P<status>\d{3})\s+(?P<size>\d+|-)\s+"(?P<referer>[^"]*)"\s+"(?P<ua>[^"]*)"$'
)

@dataclass(frozen=True)
class HttpEvent:
    ts: float
    src_ip: str
    method: str
    url: str
    path: str
    query: str
    status: int
    user_agent: str
    referer: str

def split_url(url: str) -> tuple[str, str]:
    if "?" in url:
        path, query = url.split("?", 1)
        return path, query
    return url, ""

def parse_nginx_line(line: str) -> Optional[HttpEvent]:
    line = line.strip()
    if not line:
        return None

    m = LOG_RE.match(line)
    if not m:
        return None

    ip = m.group("ip")
    ts_str = m.group("ts")  # 13/Feb/2026:12:07:00 +0000
    method = m.group("method")
    url = m.group("url")
    status = int(m.group("status"))
    ua = m.group("ua") or ""
    referer = m.group("referer") or ""

    # Parse timestamp robustly
    # Convert "13/Feb/2026:12:07:00 +0000" into epoch seconds
    # dateutil can parse if we replace first ":" after date with space
    # "13/Feb/2026:12:07:00 +0000" -> "13/Feb/2026 12:07:00 +0000"
    ts_norm = ts_str.replace(":", " ", 1)
    dt = dtparser.parse(ts_norm)
    ts = dt.timestamp()

    path, query = split_url(url)

    return HttpEvent(
        ts=ts,
        src_ip=ip,
        method=method,
        url=url,
        path=path,
        query=query,
        status=status,
        user_agent=ua,
        referer=referer,
    )

def event_to_dict(ev: HttpEvent) -> Dict[str, Any]:
    return {
        "ts": ev.ts,
        "src_ip": ev.src_ip,
        "method": ev.method,
        "url": ev.url,
        "path": ev.path,
        "query": ev.query,
        "status": ev.status,
        "user_agent": ev.user_agent,
        "referer": ev.referer,
        "source": "nginx",
    }
