"""Bounded ZAP active/passive API scan of a fresh loopback-only fixture."""
import argparse
from datetime import datetime, timezone
import json
import os
from pathlib import Path
import secrets
import shutil
import subprocess
import sys
import time
from common import ROOT, LOCAL, TOOL_PACKAGES

sys.path.insert(0, str(TOOL_PACKAGES))
import requests

parser = argparse.ArgumentParser()
parser.add_argument("--output", type=Path, required=True)
parser.add_argument("--fixture", type=Path, required=True)
parser.add_argument("--zap", type=Path, default=ROOT / ".local/tools/ZAP_2.17.0")
parser.add_argument("--port", type=int, default=5101)
parser.add_argument("--proxy-port", type=int, default=8099)
args = parser.parse_args()
output = args.output.resolve()
output.mkdir(parents=True, exist_ok=False)
data = LOCAL / (output.name+"-zap-data")
data.mkdir(parents=True, exist_ok=False)
for name in ["app.sqlite3", "audit.sqlite3"]:
    shutil.copy2(args.fixture / name, data / name)
shutil.copytree(args.fixture / "keys", data / "keys")
zap_home = LOCAL / (output.name+"-zap-home")
zap_home.mkdir(parents=True, exist_ok=False)
api_key = secrets.token_hex(24)
session = requests.Session()
session.trust_env = False
target = f"http://127.0.0.1:{args.port}"
proxy = f"http://127.0.0.1:{args.proxy_port}"
env = os.environ.copy()
env["PYTHONDONTWRITEBYTECODE"] = "1"
env["PYTHONIOENCODING"] = "utf-8"
processes = []
streams = []
state = {"started_utc": datetime.now(timezone.utc).isoformat(), "target": target,
         "scope": ["GET /api/ecommerce/products", "POST /api/v1/auth/login (nonexistent synthetic username)"],
         "authenticated": False, "active_limit_minutes_per_endpoint": 2, "threads_per_host": 2,
         "status": "running", "scan_ids": [], "limitations": ["Public API paths only; not a full authenticated application scan", "No real user, payment or production database is used"]}


def api(component, kind, action, params=None, raw=False):
    url = f"{proxy}/{'OTHER' if raw else 'JSON'}/{component}/{kind}/{action}/"
    response = session.get(url, params={"apikey": api_key, **(params or {})}, timeout=30)
    if response.status_code >= 400:
        try:
            detail = response.json()
        except ValueError:
            detail = {"status": response.status_code}
        raise RuntimeError(f"ZAP {component}/{action}: {detail}")
    if raw:
        return response.text
    value = response.json()
    if isinstance(value, dict) and "code" in value and "message" in value:
        raise RuntimeError(f"ZAP {component}/{action}: {value}")
    return value


def start(command, name, cwd=ROOT):
    stream = (output / name).open("w", encoding="utf-8")
    streams.append(stream)
    process = subprocess.Popen(command, cwd=cwd, env=env, stdout=stream, stderr=subprocess.STDOUT)
    processes.append(process)
    return process


try:
    server = start([sys.executable, str(ROOT / "tools/week9/server.py"), "--data", str(data),
                    "--port", str(args.port), "--metrics", str(output / "requests.jsonl")], "server.log")
    for _ in range(100):
        try:
            if session.get(target+"/api/v1/tunnel/config", timeout=1).status_code == 200:
                break
        except requests.RequestException:
            if server.poll() is not None:
                raise RuntimeError("Test server exited")
            time.sleep(.2)
    else:
        raise RuntimeError("Test server readiness timeout")
    jar = (args.zap / "zap-2.17.0.jar").resolve()
    if not jar.exists():
        raise RuntimeError("Install and checksum-verify ZAP 2.17.0 first")
    zap = start([shutil.which("java"), "-Xmx768m", "-Djava.awt.headless=true", "-jar", str(jar),
                 "-daemon", "-silent", "-host", "127.0.0.1", "-port", str(args.proxy_port),
                 "-dir", str(zap_home), "-config", "api.key="+api_key,
                 "-config", "autoupdate.checkOnStart=false", "-config", "autoupdate.checkAddonUpdates=false"],
                "zap-console.log", cwd=args.zap.resolve())
    for _ in range(180):
        try:
            state["zap_version"] = api("core", "view", "version")["version"]
            break
        except (requests.RequestException, ValueError):
            if zap.poll() is not None:
                raise RuntimeError("ZAP exited; inspect zap-console.log")
            time.sleep(1)
    else:
        raise RuntimeError("ZAP startup timeout")
    context = api("context", "action", "newContext", {"contextName": "local-week7"})["contextId"]
    api("context", "action", "includeInContext", {"contextName": "local-week7", "regex":
        rf"http://127\.0\.0\.1:{args.port}/api/(ecommerce/products|v1/auth/login)(\?.*)?"})
    api("context", "action", "setContextInScope", {"contextName": "local-week7", "booleanInScope": "true"})
    api("ascan", "action", "setOptionThreadPerHost", {"Integer": "2"})
    api("ascan", "action", "setOptionMaxScanDurationInMins", {"Integer": "2"})
    api("ascan", "action", "setOptionMaxRuleDurationInMins", {"Integer": "1"})
    proxies = {"http": proxy}
    product_url = target+"/api/ecommerce/products?page=1&per_page=20&category=category-03"
    api("core", "action", "accessUrl", {"url": product_url, "followRedirects": "false"})
    body = '{"username":"zap_nonexistent_user","password":"synthetic-invalid"}'
    message = (f"POST {target}/api/v1/auth/login HTTP/1.1\r\nHost: 127.0.0.1:{args.port}\r\n"
               f"Content-Type: application/json\r\nContent-Length: {len(body.encode())}\r\n\r\n{body}")
    sent = api("core", "action", "sendRequest", {"request": message, "followRedirects": "false"})
    state["login_seed_message_count"] = len(next(iter(sent.values())))
    state["discovered_urls"] = api("core", "view", "urls", {"baseurl": target})["urls"]
    state["active_scope"] = [product_url]
    for url, extra in [(product_url, {})]:
        scan = api("ascan", "action", "scan", {"url": url, "recurse": "false", "inScopeOnly": "true", "contextId": context, **extra})["scan"]
        state["scan_ids"].append(scan)
        deadline = time.monotonic()+160
        while api("ascan", "view", "status", {"scanId": scan})["status"] != "100":
            if time.monotonic() > deadline:
                api("ascan", "action", "stop", {"scanId": scan})
                state.setdefault("stopped_at_time_limit", []).append(scan)
                break
            time.sleep(2)
        print("ZAP endpoint scan completed:", url, flush=True)
    deadline = time.monotonic()+90
    while int(api("pscan", "view", "recordsToScan")["recordsToScan"]) > 0:
        if time.monotonic() > deadline:
            raise RuntimeError("Passive scan backlog did not drain")
        time.sleep(1)
    alerts = api("core", "view", "alerts", {"baseurl": target, "start": 0, "count": 10000})
    (output / "zap-alerts.json").write_text(json.dumps(alerts, indent=2), encoding="utf-8")
    (output / "zap-report.json").write_text(api("core", "other", "jsonreport", raw=True), encoding="utf-8")
    (output / "zap-report.html").write_text(api("core", "other", "htmlreport", raw=True), encoding="utf-8")
    state["status"] = "completed"
    state["alerts_count"] = len(alerts.get("alerts", []))
except Exception as error:
    state["status"] = "failed"
    state["error"] = str(error)
    raise
finally:
    state["finished_utc"] = datetime.now(timezone.utc).isoformat()
    (output / "zap-state.json").write_text(json.dumps(state, indent=2), encoding="utf-8")
    try:
        api("core", "action", "shutdown")
    except Exception:
        pass
    for process in reversed(processes):
        try:
            process.wait(timeout=3)
        except subprocess.TimeoutExpired:
            process.terminate()
            try:
                process.wait(timeout=10)
            except subprocess.TimeoutExpired:
                process.kill()
    for stream in streams:
        stream.close()
print(json.dumps(state, indent=2))
