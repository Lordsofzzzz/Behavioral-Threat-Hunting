#!/usr/bin/env python3
"""Evaluate Log Sentinel using a labeled JSONL dataset."""

import json
import os
import sys
import time
import tracemalloc
from collections import Counter
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from sentinel import LogSentinel  # noqa: E402

DATASET_FILE = Path(__file__).parent / "dataset.jsonl"
OUTPUT_REPORT = Path(__file__).parent / "report.json"


def safe_div(a, b):
    return a / b if b else 0.0


def f1_score(precision, recall):
    return safe_div(2 * precision * recall, precision + recall)


def evaluate(dataset_path=DATASET_FILE):
    if not dataset_path.exists():
        raise FileNotFoundError(f"Dataset not found: {dataset_path}")

    cwd = os.getcwd()
    os.chdir(ROOT)
    sentinel = LogSentinel(str(ROOT / "config.yaml"))
    os.chdir(cwd)

    y_true_attack = []
    y_pred_attack = []

    type_truth = []
    type_pred = []

    totals = Counter()
    latencies = []

    tracemalloc.start()
    start_all = time.perf_counter()

    with dataset_path.open("r", encoding="utf-8") as f:
        for raw in f:
            record = json.loads(raw)
            line = record["line"]
            label = record["label"]
            expected_type = record.get("expected_type")

            totals["records"] += 1

            t0 = time.perf_counter()
            parsed = sentinel.parse_log_line(line)
            alerts = sentinel.detect_attacks(parsed) if parsed else []
            t1 = time.perf_counter()

            latencies.append((t1 - t0) * 1000.0)

            predicted_attack = len(alerts) > 0
            true_attack = label == "attack"

            y_true_attack.append(true_attack)
            y_pred_attack.append(predicted_attack)

            if true_attack:
                type_truth.append(expected_type)
                predicted_types = {a.get("type") for a in alerts}
                if expected_type in predicted_types:
                    type_pred.append(expected_type)
                elif predicted_types:
                    type_pred.append(sorted(predicted_types)[0])
                else:
                    type_pred.append(None)

    elapsed = time.perf_counter() - start_all
    current_mem, peak_mem = tracemalloc.get_traced_memory()
    tracemalloc.stop()

    tp = sum(1 for t, p in zip(y_true_attack, y_pred_attack) if t and p)
    tn = sum(1 for t, p in zip(y_true_attack, y_pred_attack) if (not t) and (not p))
    fp = sum(1 for t, p in zip(y_true_attack, y_pred_attack) if (not t) and p)
    fn = sum(1 for t, p in zip(y_true_attack, y_pred_attack) if t and (not p))

    precision = safe_div(tp, tp + fp)
    recall = safe_div(tp, tp + fn)
    f1 = f1_score(precision, recall)
    accuracy = safe_div(tp + tn, len(y_true_attack))

    avg_latency_ms = safe_div(sum(latencies), len(latencies))
    p95_latency_ms = sorted(latencies)[int(0.95 * (len(latencies) - 1))] if latencies else 0.0
    throughput_rps = safe_div(len(y_true_attack), elapsed)

    by_type_total = Counter(type_truth)
    by_type_hit = Counter(t for t, p in zip(type_truth, type_pred) if t == p and t is not None)

    per_type_recall = {
        attack_type: safe_div(by_type_hit[attack_type], count)
        for attack_type, count in sorted(by_type_total.items())
    }

    results = {
        "dataset": {
            "path": str(dataset_path),
            "total_records": len(y_true_attack),
            "attack_records": sum(1 for x in y_true_attack if x),
            "benign_records": sum(1 for x in y_true_attack if not x),
        },
        "confusion_matrix": {"tp": tp, "tn": tn, "fp": fp, "fn": fn},
        "metrics": {
            "accuracy": round(accuracy, 4),
            "precision": round(precision, 4),
            "recall": round(recall, 4),
            "f1": round(f1, 4),
            "avg_latency_ms": round(avg_latency_ms, 3),
            "p95_latency_ms": round(p95_latency_ms, 3),
            "throughput_rps": round(throughput_rps, 2),
            "peak_memory_kb": round(peak_mem / 1024.0, 2),
        },
        "per_type_recall": {k: round(v, 4) for k, v in per_type_recall.items()},
    }

    OUTPUT_REPORT.write_text(json.dumps(results, indent=2), encoding="utf-8")

    print("Evaluation complete")
    print(json.dumps(results["metrics"], indent=2))
    print(f"report_written={OUTPUT_REPORT}")

    return results


if __name__ == "__main__":
    evaluate()
