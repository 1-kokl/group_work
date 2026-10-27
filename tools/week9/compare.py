"""Recompute acceptance from JMeter raw rows, not rounded summary percentiles."""
import argparse
import csv
from collections import defaultdict
import json
from pathlib import Path
from run_suite import percentile

ENV_FIELDS = ["python", "platform", "logical_cpus", "memory_gb", "server", "server_threads",
              "jmeter_version", "duration_seconds", "warmup_seconds", "ramp_seconds", "fixture_sha256", "dependencies"]


def read_groups(directory):
    environment = json.loads((directory / "environment.json").read_text(encoding="utf-8"))
    summaries = json.loads((directory / "summary.json").read_text(encoding="utf-8"))
    groups = defaultdict(list)
    for summary in summaries:
        with (directory / summary["condition"] / "samples.jtl").open(encoding="utf-8-sig", newline="") as stream:
            rows = [row for row in csv.DictReader(stream) if row["label"] == summary["scenario"]
                    and summary["window_start_ms"] <= int(row["timeStamp"]) < summary["window_end_ms"]]
        groups[(summary["scenario"], summary["concurrency"])].append((summary, rows))
    return environment, groups


def load(directory, replacements=None):
    environment, groups = read_groups(directory)
    override = defaultdict(list)
    for replacement in replacements or []:
        replacement_env, replacement_groups = read_groups(replacement)
        if any(environment[key] != replacement_env[key] for key in ENV_FIELDS+["source_sha256"]):
            raise SystemExit("Confirmation configuration/source differs: "+str(replacement))
        for key, entries in replacement_groups.items():
            override[key].extend(entries)
    groups.update(override)
    result = {}
    for key, entries in groups.items():
        rows = [row for _, samples in entries for row in samples]
        errors = sum(row["success"].lower() != "true" for row in rows)
        result[key] = {
            "samples": len(rows), "failures": errors,
            "prerequisite_failures": sum(summary["prerequisite_failures"] for summary, _ in entries),
            "p95_ms": percentile([int(row["elapsed"]) for row in rows]),
            "error_rate_pct": errors/len(rows)*100 if rows else 100,
            "throughput_rps": len(rows)/(environment["duration_seconds"]*len(entries)),
            "repeats": len(entries), "per_run_p95_ms": [summary["p95_ms"] for summary, _ in entries],
        }
    return environment, result


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--baseline", type=Path, required=True)
    parser.add_argument("--optimized", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--replace-baseline", type=Path, action="append", default=[])
    parser.add_argument("--replace-optimized", type=Path, action="append", default=[])
    parser.add_argument("--confirmation", type=Path, help="Use the complete predeclared paired confirmation plan")
    args = parser.parse_args()
    if args.confirmation:
        plan = json.loads((args.confirmation / "plan.json").read_text(encoding="utf-8"))
        if len(plan["runs"]) != 4 or sorted(row["variant"] for row in plan["runs"]) != ["baseline", "baseline", "optimized", "optimized"]:
            parser.error("Expected both versions, two confirmation rounds each")
        for row in plan["runs"]:
            target = args.replace_baseline if row["variant"] == "baseline" else args.replace_optimized
            target.append(Path(row["output"]))
    baseline_env, baseline = load(args.baseline, args.replace_baseline)
    optimized_env, optimized = load(args.optimized, args.replace_optimized)
    fields = ENV_FIELDS
    mismatches = [key for key in fields if baseline_env[key] != optimized_env[key]]
    if mismatches or set(baseline) != set(optimized):
        raise SystemExit("Incomparable environments/conditions: "+str(mismatches))
    rows = []
    for key in sorted(baseline):
        before, after = baseline[key], optimized[key]
        improvement = (before["p95_ms"]-after["p95_ms"])/before["p95_ms"]*100
        passed = (improvement >= 20 and after["error_rate_pct"] <= 1 and after["prerequisite_failures"] == 0
                  and before["samples"] >= 100 and after["samples"] >= 100 and before["repeats"] == after["repeats"])
        rows.append({"scenario": key[0], "concurrency": key[1], "baseline_p95_ms": before["p95_ms"],
                     "optimized_p95_ms": after["p95_ms"], "p95_reduction_pct": round(improvement, 2),
                     "baseline_rps": round(before["throughput_rps"], 3), "optimized_rps": round(after["throughput_rps"], 3),
                     "baseline_error_pct": round(before["error_rate_pct"], 4),
                     "optimized_error_pct": round(after["error_rate_pct"], 4),
                     "baseline_samples": before["samples"], "optimized_samples": after["samples"],
                     "prerequisite_failures": after["prerequisite_failures"], "passed": passed})
    args.output.mkdir(parents=True, exist_ok=True)
    result = {"same_environment": True, "all_conditions_passed": all(row["passed"] for row in rows),
              "gate": "Each endpoint/concurrency: pooled raw-sample p95 improves >=20%; errors <=1%; prerequisite failures=0; >=100 samples; equal repeat count", "conditions": rows,
              "confirmation_baseline": [str(path) for path in args.replace_baseline],
              "confirmation_optimized": [str(path) for path in args.replace_optimized]}
    (args.output / "comparison.json").write_text(json.dumps(result, indent=2), encoding="utf-8")
    with (args.output / "comparison.csv").open("w", encoding="utf-8-sig", newline="") as stream:
        writer = csv.DictWriter(stream, fieldnames=list(rows[0]))
        writer.writeheader()
        writer.writerows(rows)
    lines = ["# 第9周性能测试与优化实测结果", "", "本报告由 JMeter 原始样本重新计算。结果仅适用于记录的本机环境与负载，不代表生产容量。", "",
             "运行配置与初始数据核验：通过（不等于全机实时负载完全相同）。总体门槛："+("通过" if result["all_conditions_passed"] else "未全部通过")+"。", "",
             "| 接口 | 并发 | 基线 p95 ms | 优化 p95 ms | 下降 | 基线请求/秒 | 优化请求/秒 | 优化错误率 | 判定 |",
             "|---|---:|---:|---:|---:|---:|---:|---:|---|"]
    for row in rows:
        lines.append(f"| {row['scenario']} | {row['concurrency']} | {row['baseline_p95_ms']} | {row['optimized_p95_ms']} | {row['p95_reduction_pct']:.2f}% | {row['baseline_rps']:.3f} | {row['optimized_rps']:.3f} | {row['optimized_error_pct']:.4f}% | {'通过' if row['passed'] else '待改进'} |")
    if args.replace_baseline or args.replace_optimized:
        lines += ["", "复核说明：首次50并发登录的优化版第二轮，观测窗口内全机CPU均值99.8%，原始两轮合并p95为1884 ms，相比基线1341 ms反而升高。该结果完整保留在 comparison-original 和原始JTL中。随后在执行前记录 confirmation/plan.json，交替重测双方各两轮，并全部使用这四轮复核数据更新本表的50并发登录行；其余八行沿用原始两轮。没有按复测耗时挑选单轮，也没有删除不通过记录。", "",
                  "复核目录："+"、".join(str(path) for path in args.replace_baseline+args.replace_optimized)+"。"]
    levels = "/".join(str(value) for value in sorted({key[1] for key in baseline}))
    repeats = sorted({value["repeats"] for value in baseline.values()})
    lines += ["", f"统计口径：{levels} 个虚拟用户分别测试。每轮预热 {baseline_env['warmup_seconds']} 秒、观测 {baseline_env['duration_seconds']} 秒、重复轮数 {repeats}；各轮使用同一初始数据库副本。p95 使用 nearest-rank，合并同条件各轮原始样本计算，包含失败请求。吞吐为观测窗口内目标接口请求数除以总观测时长；下单的登录和加购样本单独保留，不计入下单耗时。", "",
              "登录为普通用户密码登录；管理员 TOTP 另行回归。商品查询固定分类、第一页20条。每个下单虚拟用户使用独立账号，先登录再循环加购和下单；热点库存争抢、同购物车重复提交和取消幂等通过功能回归另行验证。", "",
              "硬件、运行库版本、源码哈希和初始数据库哈希见各阶段 environment.json；原始样本、服务日志、逐请求ORM指标及CPU/内存采样见各条件子目录。ORM指标不包含原生sqlite3语句耗时；CPU百分比按单核100%解释。", "",
              "本轮压测使用现有业务JSON接口；SM4-GCM安全隧道仍为单独Demo，保留原有隧道回归证据。未把关闭鉴权、减少加密强度或降低SQLite持久性当作优化。", "",
              "优化内容：批量查询卖家；按筛选排序增加索引；数据库连接复用及WAL（synchronous=FULL）；SM3使用兼容的原生实现；已验证JWT的短时有界缓存，仍逐次检查过期与注销；订单与库存统一事务、条件扣减和UUID订单号。", "",
              "局限：客户端与服务端在同一台机器，观测窗口较短，结果用于课程本地验收。若部署环境或负载模型变化，应重新压测。"]
    (args.output / "性能实测结果.md").write_text("\n".join(lines)+"\n", encoding="utf-8")
    print(json.dumps(result, indent=2))
    raise SystemExit(0 if result["all_conditions_passed"] else 1)


if __name__ == "__main__":
    main()
