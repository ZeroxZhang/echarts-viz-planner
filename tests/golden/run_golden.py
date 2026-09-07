#!/usr/bin/env python3
"""run_golden.py — golden set 回归统计（echarts-viz-planner 验收 §18.1）。

输入：tests/golden/golden_cases.json（用例定义）+ tests/golden/results.json（执行结果）。
执行协议（无 LLM 在环，由 Agent 手动执行）：对每个用例按 skill 工作流选型，
把主方案 capability 与族、提问次数、是否识别「不该画图」、api status 填入 results.json。

门槛（v3 方案 §18.1）：
    top-1 族命中率 ≥ 80%；top-3 族命中率 = 100%；
    「不该画图」用例 100% 正确识别；interactive 澄清提问率 ≤ 30%。

用法：python3 run_golden.py
退出码：0 达到门槛；1 未达到或结果不完整。
"""

import json
import os

HERE = os.path.dirname(os.path.abspath(__file__))
THRESHOLDS = {"top1": 0.80, "top3": 1.00, "no_chart": 1.00, "clarify": 0.30}


def main():
    with open(os.path.join(HERE, "golden_cases.json"), encoding="utf-8") as f:
        cases = json.load(f)["cases"]
    with open(os.path.join(HERE, "results.json"), encoding="utf-8") as f:
        results = json.load(f)["cases"]

    rows = []
    for case in cases:
        cid = case["id"]
        res = results.get(cid)
        if not res:
            rows.append({"id": cid, "name": case["name"], "missing": True})
            continue
        if case.get("expected_status"):
            top1 = res.get("status") == case["expected_status"]
            top3 = top1
        else:
            af = res.get("actual_top1_family")
            top1 = af == case["expected_top1_family"]
            top3 = af in case["expected_top3_families"]
        no_chart = None
        if case["expect_no_chart"]:
            no_chart = bool(res.get("no_chart_recognized"))
        rows.append({
            "id": cid, "name": case["name"], "mode": case["mode"],
            "top1": top1, "top3": top3, "no_chart": no_chart,
            "clarify": res.get("clarifications_asked", 0),
            "expect_clarify": case["expect_clarification"],
        })

    print(f"{'id':<5}{'name':<16}{'mode':<13}{'top1':<6}{'top3':<6}{'no_chart':<9}{'asked':<7}期望澄清")
    for r in rows:
        if r.get("missing"):
            print(f"{r['id']:<5}{r['name']:<16}{'—':<13}{'缺结果':<6}")
            continue
        t1 = "✓" if r["top1"] else "✗"
        t3 = "✓" if r["top3"] else "✗"
        nc = "—" if r["no_chart"] is None else ("✓" if r["no_chart"] else "✗")
        ec = "是" if r["expect_clarify"] else ""
        print(f"{r['id']:<5}{r['name']:<16}{r['mode']:<13}{t1:<6}{t3:<6}{nc:<9}{r['clarify']:<7}{ec}")

    done = [r for r in rows if not r.get("missing")]
    n = len(done)
    top1_rate = sum(r["top1"] for r in done) / n if n else 0
    top3_rate = sum(r["top3"] for r in done) / n if n else 0
    nc_cases = [r for r in done if r["no_chart"] is not None]
    nc_rate = (sum(r["no_chart"] for r in nc_cases) / len(nc_cases)) if nc_cases else 1.0
    inter = [r for r in done if r["mode"] == "interactive"]
    clar_rate = sum(r["clarify"] for r in inter) / len(inter) if inter else 0

    print(f"\n用例数: {n}/{len(cases)}")
    print(f"top-1 族命中率:   {top1_rate:.0%}  (门槛 ≥ {THRESHOLDS['top1']:.0%})  "
          f"{'✅' if top1_rate >= THRESHOLDS['top1'] else '❌'}")
    print(f"top-3 族命中率:   {top3_rate:.0%}  (门槛 = {THRESHOLDS['top3']:.0%})  "
          f"{'✅' if top3_rate >= THRESHOLDS['top3'] else '❌'}")
    print(f"不该画图识别率:   {nc_rate:.0%}  (门槛 = {THRESHOLDS['no_chart']:.0%})  "
          f"{'✅' if nc_rate >= THRESHOLDS['no_chart'] else '❌'}")
    print(f"澄清提问率:       {clar_rate:.0%}  (门槛 ≤ {THRESHOLDS['clarify']:.0%})  "
          f"{'✅' if clar_rate <= THRESHOLDS['clarify'] else '❌'}")

    missing = [r["id"] for r in rows if r.get("missing")]
    if missing:
        print(f"⚠️ 缺结果用例: {missing}")
    passed = (n == len(cases) and top1_rate >= THRESHOLDS["top1"]
              and top3_rate >= THRESHOLDS["top3"]
              and nc_rate >= THRESHOLDS["no_chart"]
              and clar_rate <= THRESHOLDS["clarify"])
    print(f"\n结论: {'达到 §18.1 门槛' if passed else '未达标'}")
    return 0 if passed else 1


if __name__ == "__main__":
    raise SystemExit(main())
