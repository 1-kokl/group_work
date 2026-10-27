"""Run real JMeter against a fresh isolated data copy for every condition."""
import argparse
import csv
import hashlib
import importlib.metadata
import json
import math
import os
from pathlib import Path
import platform
import shutil
import subprocess
import sys
import threading
import time
from urllib.request import urlopen
from common import ROOT, LOCAL, TOOL_PACKAGES

sys.path.insert(0, str(TOOL_PACKAGES))
import psutil


def percentile(values, percent=95):
    values = sorted(values)
    return values[max(0, math.ceil(len(values)*percent/100)-1)] if values else None


def summarize(jtl, scenario, warmup, total_duration):
    with jtl.open(encoding="utf-8-sig", newline="") as stream:
        rows = list(csv.DictReader(stream))
    if not rows:
        raise RuntimeError("JMeter did not produce any samples")
    start = min(int(row["timeStamp"]) for row in rows)
    cutoff = start + warmup*1000
    # Use request START timestamps and a fixed observation window, including failures.
    end = start + total_duration*1000
    measured = [r for r in rows if r["label"] == scenario and cutoff <= int(r["timeStamp"]) < end]
    errors = [r for r in measured if r["success"].lower() != "true"]
    elapsed = [int(r["elapsed"]) for r in measured]
    prerequisites = [r for r in rows if r["label"] != scenario and r["success"].lower() != "true"]
    return {
        "samples": len(measured), "failures": len(errors), "prerequisite_failures": len(prerequisites),
        "error_rate_pct": round(len(errors)/len(measured)*100, 4) if measured else 100,
        "p50_ms": percentile(elapsed, 50), "p95_ms": percentile(elapsed),
        "p99_ms": percentile(elapsed, 99), "mean_ms": round(sum(elapsed)/len(elapsed), 3) if elapsed else None,
        "throughput_rps": round(len(measured)/(total_duration-warmup), 3),
        "window_start_ms": cutoff, "window_end_ms": end,
        "error_codes": {code: sum(r["responseCode"] == code for r in errors) for code in {r["responseCode"] for r in errors}},
    }


def run_condition(args, scenario, concurrency, repeat):
    condition = f"{scenario}-c{concurrency}-r{repeat}"
    output = args.output / condition
    output.mkdir(parents=True, exist_ok=False)
    data = LOCAL / "runs" / args.output.name / condition
    data.mkdir(parents=True, exist_ok=False)
    for name in ["app.sqlite3", "audit.sqlite3", "fixture.json"]:
        shutil.copy2(args.fixture / name, data / name)
    shutil.copytree(args.fixture / "keys", data / "keys")
    env = os.environ.copy()
    env["PYTHONDONTWRITEBYTECODE"] = "1"
    env["PYTHONIOENCODING"] = "utf-8"
    server_log = (output / "server.log").open("w", encoding="utf-8")
    command = [sys.executable, str(ROOT / "tools/week9/server.py"), "--source", str(args.source),
               "--data", str(data), "--port", str(args.port), "--metrics", str(output / "requests.jsonl")]
    server = subprocess.Popen(command, cwd=ROOT, env=env, stdout=server_log, stderr=subprocess.STDOUT)
    stop = threading.Event()
    monitor = None
    try:
        for attempt in range(150):
            if server.poll() is not None:
                raise RuntimeError("Acceptance server exited; inspect "+str(output / "server.log"))
            try:
                with urlopen(f"http://127.0.0.1:{args.port}/api/v1/tunnel/config", timeout=1) as response:
                    if response.status == 200:
                        break
            except OSError:
                time.sleep(.2)
        else:
            raise RuntimeError("Acceptance server did not become ready")
        process = psutil.Process(server.pid)

        def sample_resources():
            process.cpu_percent()
            with (output / "resources.csv").open("w", encoding="utf-8", newline="") as stream:
                writer = csv.writer(stream)
                writer.writerow(["timestamp_ms", "server_cpu_pct_one_core", "rss_mb", "threads", "system_cpu_pct"])
                while not stop.wait(1):
                    writer.writerow([round(time.time()*1000), process.cpu_percent(),
                                     round(process.memory_info().rss/1024**2, 3), process.num_threads(), psutil.cpu_percent()])
                    stream.flush()
        monitor = threading.Thread(target=sample_resources, daemon=True)
        monitor.start()
        total_duration = args.warmup + args.duration
        jtl = output / "samples.jtl"
        jmeter = args.jmeter / "bin/ApacheJMeter.jar"
        cmd = [args.java, "-Xms256m", "-Xmx512m", "-Djava.awt.headless=true", "-jar", str(jmeter),
               "-n", "-t", str(ROOT / f"performance/jmeter/{scenario}.jmx"), "-l", str(jtl),
               "-j", str(output / "jmeter.log"), f"-Jport={args.port}", f"-Jthreads={concurrency}",
               f"-Jduration={total_duration}", "-Jramp=2", "-Jsampleresult.timestamp.start=true",
               "-Jjmeter.save.saveservice.output_format=csv", "-Jjmeter.save.saveservice.timestamp_format=ms",
               "-Jjmeter.save.saveservice.print_field_names=true", "-Jjmeter.save.saveservice.response_data=false",
               "-Jjmeter.save.saveservice.response_data.on_error=false", "-Jjmeter.save.saveservice.samplerData=false",
               "-Jjmeter.save.saveservice.requestHeaders=false", "-Jjmeter.save.saveservice.responseHeaders=false",
               "-Jjmeter.save.saveservice.assertion_results_failure_message=true"]
        (output / "command.json").write_text(json.dumps(cmd, indent=2), encoding="utf-8")
        with (output / "jmeter-console.log").open("w", encoding="utf-8") as stream:
            result = subprocess.run(cmd, cwd=args.jmeter / "bin", env=env, stdout=stream,
                                    stderr=subprocess.STDOUT, timeout=total_duration+90)
        if result.returncode:
            raise RuntimeError("JMeter failed; inspect "+str(output / "jmeter-console.log"))
        summary = summarize(jtl, scenario, args.warmup, total_duration)
        summary.update(scenario=scenario, concurrency=concurrency, repeat=repeat, condition=condition)
        (output / "summary.json").write_text(json.dumps(summary, indent=2), encoding="utf-8")
        print(json.dumps(summary), flush=True)
        return summary
    finally:
        stop.set()
        if monitor:
            monitor.join(timeout=3)
        server.terminate()
        try:
            server.wait(timeout=10)
        except subprocess.TimeoutExpired:
            server.kill()
            server.wait(timeout=10)
        server_log.close()


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--source", type=Path, default=ROOT)
    parser.add_argument("--fixture", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--jmeter", type=Path, default=ROOT / ".local/tools/apache-jmeter-5.6.3")
    parser.add_argument("--java", default=shutil.which("java"))
    parser.add_argument("--levels", default="10,30,50")
    parser.add_argument("--scenarios", default="login,products,orders")
    parser.add_argument("--duration", type=int, default=30)
    parser.add_argument("--warmup", type=int, default=5)
    parser.add_argument("--repeats", type=int, default=2)
    parser.add_argument("--port", type=int, default=5099)
    args = parser.parse_args()
    for name in ["source", "fixture", "output", "jmeter"]:
        setattr(args, name, getattr(args, name).resolve())
    if args.output.exists():
        parser.error("Output exists; choose a new output directory to preserve earlier evidence")
    if not args.java or not (args.jmeter / "bin/ApacheJMeter.jar").exists():
        parser.error("Java and JMeter are required; see performance/README.md")
    args.output.mkdir(parents=True)
    metadata = {
        "started_at": time.strftime("%Y-%m-%dT%H:%M:%S%z"), "python": sys.version,
        "platform": platform.platform(), "logical_cpus": psutil.cpu_count(),
        "memory_gb": round(psutil.virtual_memory().total/1024**3, 2),
        "server": "waitress", "server_threads": 16, "java": args.java,
        "jmeter_version": "5.6.3", "source": str(args.source),
        "duration_seconds": args.duration, "warmup_seconds": args.warmup, "ramp_seconds": 2,
        "fixture_sha256": hashlib.sha256((args.fixture / "app.sqlite3").read_bytes()).hexdigest(),
        "dependencies": {name: importlib.metadata.version(name) for name in
                         ["Flask", "Flask-SQLAlchemy", "SQLAlchemy", "gmssl", "cryptography", "psutil", "waitress"]},
        "source_sha256": {str(p.relative_to(args.source)): hashlib.sha256(p.read_bytes()).hexdigest()
                          for p in [args.source / "run.py", *sorted((args.source / "app").rglob("*.py"))]},
    }
    (args.output / "environment.json").write_text(json.dumps(metadata, indent=2), encoding="utf-8")
    summaries = []
    for repeat in range(1, args.repeats+1):
        for concurrency in map(int, args.levels.split(",")):
            for scenario in args.scenarios.split(","):
                summaries.append(run_condition(args, scenario, concurrency, repeat))
                (args.output / "summary.json").write_text(json.dumps(summaries, indent=2), encoding="utf-8")


if __name__ == "__main__":
    main()
