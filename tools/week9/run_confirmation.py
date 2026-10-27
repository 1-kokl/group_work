"""Predeclared paired confirmation of the condition affected by system contention."""
import argparse
from datetime import datetime, timezone
import json
from pathlib import Path
import subprocess
import sys
from common import ROOT

parser = argparse.ArgumentParser()
parser.add_argument("--fixture", type=Path, required=True)
parser.add_argument("--baseline-source", type=Path, required=True)
parser.add_argument("--output", type=Path, required=True)
args = parser.parse_args()
output = args.output.resolve()
output.mkdir(parents=True, exist_ok=False)
plan = {"declared_utc": datetime.now(timezone.utc).isoformat(),
        "reason": "Original optimized login/c50/r2 had 99.8% mean system CPU in the measurement window; retain the original result and independently retest BOTH versions.",
        "scenario": "login", "concurrency": 50, "rounds_per_version": 2,
        "duration_seconds": 20, "warmup_seconds": 5,
        "selection": "Use all four confirmation runs for this one comparison row, regardless of their outcome; retain every original sample. Other rows keep their original two runs.", "runs": []}
for repeat in (1, 2):
    for variant, source in [("baseline", args.baseline_source.resolve()), ("optimized", ROOT)]:
        directory = output / f"{output.name}-{variant}-r{repeat}"
        plan["runs"].append({"variant": variant, "output": str(directory), "source": str(source)})
(output / "plan.json").write_text(json.dumps(plan, indent=2), encoding="utf-8")
for row in plan["runs"]:
    command = [sys.executable, str(ROOT / "tools/week9/run_suite.py"), "--fixture", str(args.fixture.resolve()),
               "--source", row["source"], "--output", row["output"], "--levels", "50", "--scenarios", "login",
               "--duration", "20", "--warmup", "5", "--repeats", "1"]
    subprocess.run(command, cwd=ROOT, check=True)
