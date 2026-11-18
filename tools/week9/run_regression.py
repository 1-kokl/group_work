"""Run functional/security regressions against isolated files, never demo data."""
import argparse
import json
import os
from pathlib import Path
import subprocess
import sys
from common import configure, ROOT

parser = argparse.ArgumentParser()
parser.add_argument("--output", type=Path, required=True)
args = parser.parse_args()
output = args.output.resolve()
output.mkdir(parents=True, exist_ok=False)
env = os.environ.copy()
env["PYTHONDONTWRITEBYTECODE"] = "1"
env["PYTHONIOENCODING"] = "utf-8"
commands = [
    ("week9", [sys.executable, "-m", "pytest", "tests/week9", "-q", "-p", "no:cacheprovider",
               "--basetemp", str(ROOT / ".local/week9" / (output.name+"-pytest")),
               "--junitxml", str(output / "week9.xml")]),
]
results = []
for name, command in commands:
    with (output / (name+".log")).open("w", encoding="utf-8") as stream:
        result = subprocess.run(command, cwd=ROOT, env=env, stdout=stream, stderr=subprocess.STDOUT, timeout=180)
    results.append({"name": name, "exit_code": result.returncode, "command": command})

# Legacy acceptance tests import run directly, so configure paths BEFORE importing.
for name, script in [("rbac", "test_rbac.py"), ("tunnel", "test_secure_tunnel.py")]:
    data = ROOT / ".local/week9" / (output.name+"-"+name)
    configure(data)
    code = "import runpy; runpy.run_path("+repr(str(ROOT / script))+",run_name='__main__')"
    with (output / (name+".log")).open("w", encoding="utf-8") as stream:
        result = subprocess.run([sys.executable, "-c", code], cwd=ROOT, env=os.environ.copy(),
                                stdout=stream, stderr=subprocess.STDOUT, timeout=180)
    results.append({"name": name, "exit_code": result.returncode, "script": script})
(output / "results.json").write_text(json.dumps(results, indent=2), encoding="utf-8")
print(json.dumps(results, indent=2))
raise SystemExit(0 if all(row["exit_code"] == 0 for row in results) else 1)
