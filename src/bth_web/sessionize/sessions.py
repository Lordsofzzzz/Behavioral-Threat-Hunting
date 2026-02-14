from __future__ import annotations
from dataclasses import dataclass, field
from typing import Dict, Tuple, List
import time

SessionKey = Tuple[str, str]  # (ip, user_agent)

@dataclass
class SessionStats:
    first_ts: float
    last_ts: float
    count: int = 0
    unique_paths: set[str] = field(default_factory=set)
    status_counts: Dict[int, int] = field(default_factory=dict)
    login_attempts: int = 0
    fails: int = 0

    def update(self, ev: dict) -> None:
        ts = float(ev["ts"])
        self.last_ts = ts
        self.count += 1
        self.unique_paths.add(ev.get("path", ""))

        status = int(ev.get("status", 0))
        self.status_counts[status] = self.status_counts.get(status, 0) + 1

        path = (ev.get("path") or "").lower()
        method = (ev.get("method") or "").upper()

        # crude login endpoint heuristic
        if "login" in path and method in {"POST", "GET"}:
            self.login_attempts += 1
            if status in {401, 403}:
                self.fails += 1

    def window_metrics(self, now_ts: float, window_seconds: int) -> dict:
        # For now: approximate rate using total count; in later versions keep a deque of timestamps
        duration = max(1.0, now_ts - self.first_ts)
        per_min = (self.count / duration) * 60.0

        total = sum(self.status_counts.values()) or 1
        c404 = self.status_counts.get(404, 0)
        fail = self.fails
        login = self.login_attempts or 1

        return {
            "reqs_total": self.count,
            "reqs_per_min_est": per_min,
            "unique_paths": len(self.unique_paths),
            "ratio_404": c404 / total,
            "login_attempts": self.login_attempts,
            "login_fail_ratio": fail / login,
        }

class SessionStore:
    def __init__(self, idle_timeout_seconds: int = 900, window_seconds: int = 60):
        self.idle_timeout = idle_timeout_seconds
        self.window_seconds = window_seconds
        self.sessions: Dict[SessionKey, SessionStats] = {}

    def key(self, ev: dict) -> SessionKey:
        return (ev.get("src_ip", ""), ev.get("user_agent", "")[:120])

    def upsert(self, ev: dict) -> SessionStats:
        k = self.key(ev)
        ts = float(ev["ts"])
        sess = self.sessions.get(k)
        if sess is None:
            sess = SessionStats(first_ts=ts, last_ts=ts)
            self.sessions[k] = sess
        sess.update(ev)
        return sess

    def cleanup(self, now_ts: float | None = None) -> int:
        if now_ts is None:
            now_ts = time.time()
        dead = []
        for k, s in self.sessions.items():
            if now_ts - s.last_ts > self.idle_timeout:
                dead.append(k)
        for k in dead:
            del self.sessions[k]
        return len(dead)
