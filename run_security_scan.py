"""Reproducible local SAST and dependency evidence; findings are not silently fixed."""
import argparse
import importlib.metadata
import hashlib
import json
import os
from pathlib import Path
import shutil
import subprocess
import sys
from datetime import datetime, timezone

ROOT = Path(__file__).resolve().parent
TOOLS = ROOT / ".local/tools/python"
sys.path.insert(0, str(TOOLS))
CORE = ["Flask", "Flask-Cors", "Flask-JWT-Extended", "flask-restx", "Flask-SQLAlchemy",
        "flask-swagger-ui", "SQLAlchemy", "cryptography", "gmssl", "PyJWT", "pycryptodome",
        "requests", "Werkzeug", "psutil", "pytz"]


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--output", type=Path, default=ROOT / "evidence/week7" / datetime.now(timezone.utc).strftime("scan-%Y%m%dT%H%M%SZ"))
    parser.add_argument("--frontend", action="store_true", help="Resolve the frontend manifest in an isolated directory and run npm audit")
    args = parser.parse_args()
    output = args.output.resolve()
    output.mkdir(parents=True, exist_ok=False)
    env = os.environ.copy()
    env["PYTHONDONTWRITEBYTECODE"] = "1"
    env["PYTHONIOENCODING"] = "utf-8"
    env["PYTHONPATH"] = str(TOOLS)
    packages = {name: importlib.metadata.version(name) for name in CORE}
    requirements = "\n".join(f"{name}=={version}" for name, version in packages.items())+"\n"
    (output / "effective-requirements.txt").write_text(requirements, encoding="utf-8")
    actions = []

    def run(name, command, accepted=(0, 1), timeout=300, cwd=ROOT):
        with (output / (name+".stdout.log")).open("w", encoding="utf-8") as stdout, (output / (name+".stderr.log")).open("w", encoding="utf-8") as stderr:
            try:
                result = subprocess.run(command, cwd=cwd, env=env, stdout=stdout, stderr=stderr, timeout=timeout)
                row = {"name": name, "exit_code": result.returncode, "completed": result.returncode in accepted, "command": command}
            except (OSError, subprocess.TimeoutExpired) as error:
                row = {"name": name, "completed": False, "error": str(error), "command": command}
        actions.append(row)
        print(json.dumps(row), flush=True)
        return row

    run("bandit", [sys.executable, "-m", "bandit", "-r", "app", "run.py", "mock_bank.py", "-f", "json", "-o", str(output / "bandit_report.json")])
    run("pip-audit", [sys.executable, "-m", "pip_audit", "-r", str(output / "effective-requirements.txt"),
                      "--no-deps", "--disable-pip", "--format", "json", "--progress-spinner", "off",
                      "--timeout", "20", "--cache-dir", str(ROOT / ".local/tools/pip-audit-cache"),
                      "-o", str(output / "pipaudit_report.json")])
    if args.frontend:
        npm = shutil.which("npm.cmd") or shutil.which("npm")
        frontend = ROOT / ".local/week7" / (output.name+"-frontend")
        frontend.mkdir(parents=True, exist_ok=False)
        shutil.copy2(ROOT / "ecommerce-frontend/package.json", frontend / "package.json")
        # No lifecycle scripts, node_modules, or production credentials are needed.
        if npm:
            resolution = run("npm-lock", [npm, "install", "--package-lock-only", "--ignore-scripts", "--legacy-peer-deps",
                                          "--no-audit", "--no-fund", "--cache", str(ROOT / ".local/tools/npm-cache")], accepted=(0,), timeout=600, cwd=frontend)
            if resolution["completed"]:
                shutil.copy2(frontend / "package-lock.json", output / "frontend-package-lock.json")
                run("npm-audit", [npm, "audit", "--json", "--legacy-peer-deps", "--cache", str(ROOT / ".local/tools/npm-cache")], cwd=frontend)
                shutil.copy2(output / "npm-audit.stdout.log", output / "npm_audit_report.json")
        else:
            actions.append({"name": "npm-audit", "completed": False, "error": "npm not installed"})
    state = {
        "State": {"objective": "Close local week7 reproducibility gaps", "scope": "Owned local repository and synthetic loopback test service",
                  "authorization": "User requested local completion on 2026-10-22", "phase": "Evidence collection",
                  "confirmed_findings": "See actual raw scanner output; not inferred from earlier reports",
                  "open_questions": "Manual triage and patch prioritization for any remaining alerts",
                  "next_step_menu": ["Review current findings", "Apply scoped fixes and retest", "Prepare final acceptance package"]},
        "timestamp_utc": datetime.now(timezone.utc).isoformat(), "runtime_packages": packages,
        "source_sha256": {str(p.relative_to(ROOT)): hashlib.sha256(p.read_bytes()).hexdigest()
                          for p in [ROOT / "run.py", ROOT / "mock_bank.py", *sorted((ROOT / "app").rglob("*.py"))]},
        "tools": {name: importlib.metadata.version(name) for name in ["bandit", "pip-audit"]},
        "actions": actions,
        "limits": ["Python audit covers pinned direct runtime packages, not a complete transitive lock",
                   "Frontend audit resolves package.json now; it is not an audit of previously shipped dist assets",
                   "Exit 1 from scanners indicates findings; operational errors are separately checked"],
    }
    (output / "scan-state.json").write_text(json.dumps(state, indent=2), encoding="utf-8")
    required = ["bandit_report.json", "pipaudit_report.json"]
    completed = all(row["completed"] for row in actions) and all((output / name).is_file() for name in required)
    for name in required + (["npm_audit_report.json"] if args.frontend else []):
        try:
            value = json.loads((output / name).read_text(encoding="utf-8-sig"))
            if "error" in value:
                completed = False
        except (ValueError, OSError):
            completed = False
    raise SystemExit(0 if completed else 2)


if __name__ == "__main__":
    main()
