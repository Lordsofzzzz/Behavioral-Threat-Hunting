# Evaluation Harness

This folder provides a reproducible benchmark for final-year reporting.

## Files
- `generate_dataset.py` — creates `dataset.jsonl` with labeled benign + attack records
- `evaluate.py` — runs detection and outputs metrics + `report.json`
- `report_template.md` — ready-to-fill section for your project report/viva

## Metrics Reported
- Accuracy, Precision, Recall, F1
- Average and P95 detection latency (ms)
- Throughput (records/sec)
- Peak memory usage (KB)
- Recall by attack type

## Run
From `log-sentinel`:

```bash
python evaluation/generate_dataset.py
python evaluation/evaluate.py
```

Outputs:
- `evaluation/dataset.jsonl`
- `evaluation/report.json`
