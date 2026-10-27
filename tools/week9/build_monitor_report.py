"""Summarize the captured process and ORM measurements for each condition."""
import argparse
import csv
import json
from pathlib import Path
from run_suite import percentile

parser = argparse.ArgumentParser()
parser.add_argument("--baseline", type=Path, required=True)
parser.add_argument("--optimized", type=Path, required=True)
parser.add_argument("--output", type=Path, required=True)
parser.add_argument("--confirmation", type=Path)
args = parser.parse_args()
rows = []
directories = [("baseline", args.baseline), ("optimized", args.optimized)]
if args.confirmation:
    plan = json.loads((args.confirmation / "plan.json").read_text(encoding="utf-8"))
    directories += [(row["variant"]+"_confirmation", Path(row["output"])) for row in plan["runs"]]
for variant, directory in directories:
    for condition in json.loads((directory / "summary.json").read_text(encoding="utf-8")):
        path = directory / condition["condition"]
        begin, end = condition["window_start_ms"], condition["window_end_ms"]
        with (path / "resources.csv").open(encoding="utf-8", newline="") as stream:
            samples = [row for row in csv.DictReader(stream) if begin <= int(row["timestamp_ms"]) < end]
        requests = [json.loads(line) for line in (path / "requests.jsonl").read_text(encoding="utf-8").splitlines()]
        routes = {"login": "/api/v1/auth/login", "products": "/api/ecommerce/products", "orders": "/api/ecommerce/orders"}
        requests = [row for row in requests if row["route"] == routes[condition["scenario"]] and begin <= row["timestamp_ms"] < end]
        rows.append({"variant": variant, "run_directory": str(directory), "condition": condition["condition"],
                     "cpu_mean_pct_one_core": round(sum(float(row["server_cpu_pct_one_core"]) for row in samples)/len(samples), 2) if samples else None,
                     "rss_peak_mb": max(float(row["rss_mb"]) for row in samples) if samples else None,
                     "route_p95_ms": percentile([row["duration_ms"] for row in requests]),
                     "orm_sql_mean_count": round(sum(row["orm_sql_count"] for row in requests)/len(requests), 3) if requests else None,
                     "orm_sql_p95_ms": percentile([row["orm_sql_ms"] for row in requests]),
                     "resource_samples": len(samples), "route_samples": len(requests)})
args.output.mkdir(parents=True, exist_ok=True)
(args.output / "monitor-summary.json").write_text(json.dumps(rows, indent=2), encoding="utf-8")
with (args.output / "monitor-summary.csv").open("w", encoding="utf-8-sig", newline="") as stream:
    writer = csv.DictWriter(stream, fieldnames=list(rows[0]))
    writer.writeheader()
    writer.writerows(rows)
print("Monitoring summarized:", len(rows), "conditions")
