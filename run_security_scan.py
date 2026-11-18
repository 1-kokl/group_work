"""
一键安全扫描脚本 —— 任务书第 7 周节点「SAST / DAST 与依赖扫描」可复现入口。

用法：
    PYTHONUTF8=1 python run_security_scan.py

会依次执行（缺工具则跳过并提示安装命令）：
    1. SAST      : bandit 静态扫描后端 Python 代码 -> bandit_report.json
    2. 依赖扫描   : pip-audit 扫描 Python 依赖 -> pipaudit_report.json
    3. 依赖扫描   : npm audit 扫描前端依赖（需在 ecommerce-frontend/ 且已 npm install）
    4. DAST      : 提示运行仓库内已有的动态攻击脚本（重放 / 中间人篡改 / 安全隧道）

产出文件均落在项目根目录，供 docs/05、docs/06 引用。
"""
import json
import os
import shutil
import subprocess
import sys

ROOT = os.path.dirname(os.path.abspath(__file__))


def have(cmd):
    return shutil.which(cmd) is not None


def run(cmd, cwd=None):
    print(f"\n$ {' '.join(cmd)}")
    return subprocess.run(cmd, cwd=cwd or ROOT)


def sast_bandit():
    print("\n" + "=" * 70)
    print("[1] SAST — bandit 静态扫描")
    print("=" * 70)
    if not have("bandit"):
        try:
            import bandit  # noqa
        except ImportError:
            print("未安装 bandit，可执行: pip install bandit")
            return
    run([sys.executable, "-m", "bandit", "-r", "app", "-f", "json",
         "-o", "bandit_report.json", "--exit-zero"])
    print("已生成 bandit_report.json")


def dep_pip_audit():
    print("\n" + "=" * 70)
    print("[2] 依赖扫描 — pip-audit（Python）")
    print("=" * 70)
    if not have("pip-audit"):
        try:
            import pip_audit  # noqa
        except ImportError:
            print("未安装 pip-audit，可执行: pip install pip-audit")
            return
    # requirements.txt 含中文注释会导致解析失败，这里只审计核心依赖
    req = os.path.join(ROOT, "requirements_core.txt")
    if not os.path.exists(req):
        core = [
            "Flask==3.1.3", "flask-cors==6.0.2", "Flask-JWT-Extended==4.7.1",
            "flask-restx==1.3.2", "flask-sqlalchemy==3.1.1", "flask-swagger-ui==5.32.2",
            "gmssl==3.2.2", "cryptography==45.0.6", "SQLAlchemy==2.0.48",
            "pytz==2025.1", "PyJWT==2.12.1", "requests==2.32.3",
            "PyYAML==6.0.2", "Werkzeug==3.1.6", "Jinja2==3.1.6",
        ]
        with open(req, "w", encoding="utf-8") as f:
            f.write("\n".join(core) + "\n")
    run([sys.executable, "-m", "pip_audit", "-r", req,
         "--format", "json", "-o", "pipaudit_report.json"])
    print("已生成 pipaudit_report.json")


def dep_npm_audit():
    print("\n" + "=" * 70)
    print("[3] 依赖扫描 — npm audit（前端）")
    print("=" * 70)
    fe = os.path.join(ROOT, "ecommerce-frontend")
    if not os.path.isdir(os.path.join(fe, "node_modules")):
        print("前端 node_modules 不存在，跳过（需先 cd ecommerce-frontend && npm install）")
        print("复现命令: cd ecommerce-frontend && npm audit --json > npm_audit_report.json")
        return
    if not (have("npm") or have("npm.cmd")):
        print("未找到 npm，跳过")
        return
    run(["npm", "audit", "--json"], cwd=fe)
    print("npm audit 完成")


def dast_hint():
    print("\n" + "=" * 70)
    print("[4] DAST — 动态攻击脚本（仓库内已有，需先启动后端与银行）")
    print("=" * 70)
    print("  # 启动服务")
    print("  python run.py            # 后端 5000")
    print("  python mock_bank.py      # 银行 8080")
    print("  # 动态安全测试")
    print("  PYTHONUTF8=1 python test_secure_tunnel.py   # 安全隧道（篡改/重放/过期/AAD，8 项）")
    print("  PYTHONUTF8=1 python test_mitm_attack.py     # 中间人篡改")
    print("  PYTHONUTF8=1 python test_replay_attack.py   # 重放攻击")
    print("  # 更完整 DAST 基线可引入 OWASP ZAP：")
    print("  #   zap-baseline.py -t http://localhost:5000")


def main():
    sast_bandit()
    dep_pip_audit()
    dep_npm_audit()
    dast_hint()
    print("\n" + "=" * 70)
    print("扫描完成。汇总见 docs/05_SAST_DAST_基线报告.md 与 docs/06_漏洞清单.md")
    print("=" * 70)


if __name__ == "__main__":
    main()
