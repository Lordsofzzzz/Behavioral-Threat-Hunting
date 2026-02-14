import argparse
import json
import os
import time
from typing import List, Dict, Any, Optional

import yaml

from bth_web.ingest.nginx_parser import parse_nginx_line, event_to_dict
from bth_web.sessionize.sessions import SessionStore
from bth_web.detection.rules import detect_signature, behavioral_detections, make_detection
from bth_web.reporting.report import write_json


def ensure_dir(path: str) -> None:
    d = os.path.dirname(path)
    if d:
        os.makedirs(d, exist_ok=True)


def load_config(path: str) -> dict:
    with open(path, "r", encoding="utf-8") as f:
        return yaml.safe_load(f) or {}


def wait_for_file(path: str, poll_seconds: float = 1.0, timeout_seconds: Optional[int] = None) -> None:
    """
    Wait until 'path' exists. If timeout_seconds is None, wait forever.
    """
    start = time.time()
    while not os.path.exists(path):
        if timeout_seconds is not None and (time.time() - start) > timeout_seconds:
            raise TimeoutError(f"Timed out waiting for file: {path}")
        print(f"[!] {path} not found yet. Waiting for generator...")
        time.sleep(poll_seconds)


def cmd_ingest(args: argparse.Namespace) -> int:
    ensure_dir(args.out)

    written = 0
    with open(args.log, "r", encoding="utf-8", errors="ignore") as f_in, \
         open(args.out, "w", encoding="utf-8") as f_out:
        for line in f_in:
            ev = parse_nginx_line(line)
            if not ev:
                continue
            f_out.write(json.dumps(event_to_dict(ev)) + "\n")
            written += 1

    print(f"[+] Wrote {written} events to {args.out}")
    return 0


def cmd_detect(args: argparse.Namespace) -> int:
    cfg = load_config(args.config)
    thresholds = cfg.get("thresholds") or {}
    sess_cfg = cfg.get("session") or {}

    store = SessionStore(
        idle_timeout_seconds=int(sess_cfg.get("idle_timeout_seconds", 900)),
        window_seconds=int(sess_cfg.get("window_seconds", 60)),
    )

    ensure_dir(args.out)
    detections: List[Dict[str, Any]] = []

    with open(args.infile, "r", encoding="utf-8", errors="ignore") as f:
        for line in f:
            ev = json.loads(line)
            store.upsert(ev)

            # Signature (per event)
            sig = detect_signature(ev.get("url", ""))
            if sig:
                detections.append(
                    make_detection(ev, sig, "medium", f"Matched signature: {sig}")
                )

            # Behavioral (per session snapshot)
            sess = store.sessions[store.key(ev)]
            metrics = sess.window_metrics(float(ev["ts"]), store.window_seconds)
            for bd in behavioral_detections(metrics, thresholds):
                detections.append(
                    make_detection(
                        ev,
                        bd["type"],
                        bd["severity"],
                        bd["reason"],
                        mitre=bd.get("mitre", []),
                        metrics=metrics,
                    )
                )

    write_json(args.out, detections)
    print(f"[+] Wrote {len(detections)} detections to {args.out}")
    return 0


def cmd_monitor(args: argparse.Namespace) -> int:
    cfg = load_config(args.config)
    thresholds = cfg.get("thresholds") or {}
    sess_cfg = cfg.get("session") or {}

    store = SessionStore(
        idle_timeout_seconds=int(sess_cfg.get("idle_timeout_seconds", 900)),
        window_seconds=int(sess_cfg.get("window_seconds", 60)),
    )

    log_path = args.log
    print(f"[*] Monitoring {log_path} (Ctrl+C to stop)")

    # Key fix: WAIT for file instead of exiting -> no restart loop in Docker
    wait_for_file(log_path, poll_seconds=1.0, timeout_seconds=None)

    with open(log_path, "r", encoding="utf-8", errors="ignore") as f:
        # Tail from end
        f.seek(0, os.SEEK_END)

        while True:
            line = f.readline()
            if not line:
                time.sleep(0.1)
                continue

            parsed = parse_nginx_line(line)
            if not parsed:
                continue

            ev = event_to_dict(parsed)
            store.upsert(ev)

            # Signature alerts
            sig = detect_signature(ev.get("url", ""))
            if sig:
                d = make_detection(ev, sig, "medium", f"Matched signature: {sig}")
                print(f"[ALERT] {d['severity']} {d['detection_type']} {d['src_ip']} {d['url']}")

            # Behavioral alerts
            sess = store.sessions[store.key(ev)]
            metrics = sess.window_metrics(float(ev["ts"]), store.window_seconds)
            for bd in behavioral_detections(metrics, thresholds):
                print(f"[ALERT] {bd['severity']} {bd['type']} {ev['src_ip']} :: {bd['reason']}")

            store.cleanup(float(ev["ts"]))


def main() -> int:
    p = argparse.ArgumentParser(prog="bth-web", description="Behavioral Threat Hunting for Web Logs")
    sub = p.add_subparsers(dest="cmd", required=True)

    sp = sub.add_parser("ingest", help="Parse nginx access.log -> JSONL events")
    sp.add_argument("--log", default="access.log")
    sp.add_argument("--out", default="output/events.jsonl")
    sp.set_defaults(func=cmd_ingest)

    sp = sub.add_parser("detect", help="Run detections on JSONL events -> JSON report")
    sp.add_argument("--in", dest="infile", default="output/events.jsonl")
    sp.add_argument("--out", default="output/detections.json")
    sp.add_argument("--config", default="configs/default.yaml")
    sp.set_defaults(func=cmd_detect)

    sp = sub.add_parser("monitor", help="Tail access.log and alert live")
    sp.add_argument("--log", default="access.log")
    sp.add_argument("--config", default="configs/default.yaml")
    sp.set_defaults(func=cmd_monitor)

    args = p.parse_args()
    return args.func(args)


if __name__ == "__main__":
    raise SystemExit(main())
