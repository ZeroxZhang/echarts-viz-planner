#!/usr/bin/env python3
"""run_contract.py — api 契约回归（§18.2 六用例，保持简单）。

设计：只做三件事——跑 validate_plan.py --schema、幂等（同文件两次校验输出一致）、
体积（≤6KB）；负例（超大数据/回传数据本体）用临时文件合成，期望校验失败。
不引入框架、不比较业务内容。

用法：python3 run_contract.py
退出码：0 全部符合预期；1 存在不符合预期。
"""

import json
import os
import subprocess
import sys
import tempfile

HERE = os.path.dirname(os.path.abspath(__file__))
SKILL = os.path.dirname(os.path.dirname(HERE))
VALIDATOR = os.path.join(SKILL, "scripts", "validate_plan.py")
FIXTURES = os.path.join(HERE, "fixtures")
SIZE_LIMIT = 6144

CASES = [
    ("完整输入", "c01-complete.json", "pass"),
    ("缺 goal", "c02-no-goal.json", "pass"),
    ("数据不可访问", "c03-inaccessible.json", "pass"),
    ("allow_extensions:false", "c04-extensions-blocked.json", "pass"),
]


def validate(path):
    r = subprocess.run([sys.executable, VALIDATOR, path, "--schema"],
                       capture_output=True, text=True)
    return r.returncode, r.stdout


def main():
    fails = []
    print(f"{'用例':<22}{'期望':<8}{'结果':<8}{'说明'}")
    for name, fn, expect in CASES:
        path = os.path.join(FIXTURES, fn)
        code, out = validate(path)
        ok = (code == 0) if expect == "pass" else (code != 0)
        size = os.path.getsize(path)
        size_ok = size <= SIZE_LIMIT
        if expect == "pass" and not size_ok:
            ok = False
        print(f"{name:<22}{expect:<8}{'✓' if ok else '✗':<8}"
              f"{f'{size}B' + (' 体积超限!' if not size_ok else '')}")
        if not ok:
            fails.append(f"{name}: exit={code}, size={size}B")

    # 幂等：c01 连续校验两次，输出一致
    p1 = os.path.join(FIXTURES, "c01-complete.json")
    _, out1 = validate(p1)
    _, out2 = validate(p1)
    idem = out1 == out2
    print(f"{'幂等（同输入两次校验）':<22}{'pass':<8}{'✓' if idem else '✗':<8}"
          f"输出{'一致' if idem else '不一致'}")
    if not idem:
        fails.append("幂等: 两次校验输出不一致")

    # 负例 1：超大数据（合成 >6KB 的 summary/rejected）
    with tempfile.NamedTemporaryFile("w", suffix=".json", delete=False) as f:
        json.dump({
            "contract_version": "1.0", "mode": "api", "status": "ok",
            "summary": "x" * 7000,
            "echarts": {"version": "6.1.0", "deps": [], "renderer": "canvas"},
            "intent": {"goal": "x", "scenario": "review", "inferred": False, "confidence": "high"},
            "data": {"ref": {"type": "file", "id": "x.csv"},
                     "profile": {"rows": 1, "dimensions": ["a"], "measures": ["b"]},
                     "binding": {"mode": "dataset.source", "expects": "array", "required_fields": []}},
            "plan": [{"role": "primary", "capability_id": "bar.basic", "question": "x",
                      "match": "strong", "option": {"series": [{"type": "bar"}]}}],
        }, f)
        big = f.name
    code, _ = validate(big)
    ok = code != 0
    print(f"{'超大数据（>6KB 应拒绝）':<22}{'fail':<8}{'✓' if ok else '✗':<8}{f'exit={code}'}")
    if not ok:
        fails.append("超大数据: 校验未拒绝")
    os.unlink(big)

    # 负例 2：回传数据本体（data.inline 应拒绝）
    with tempfile.NamedTemporaryFile("w", suffix=".json", delete=False) as f:
        json.dump({
            "contract_version": "1.0", "mode": "api", "status": "ok",
            "summary": "x",
            "echarts": {"version": "6.1.0", "deps": [], "renderer": "canvas"},
            "intent": {"goal": "x", "scenario": "review", "inferred": False, "confidence": "high"},
            "data": {"ref": {"type": "inline", "id": "x"},
                     "inline": [{"a": 1, "b": 2}],   # 禁止回传的数据本体
                     "profile": {"rows": 1, "dimensions": ["a"], "measures": ["b"]},
                     "binding": {"mode": "dataset.source", "expects": "array", "required_fields": []}},
            "plan": [{"role": "primary", "capability_id": "bar.basic", "question": "x",
                      "match": "strong", "option": {"series": [{"type": "bar"}]}}],
        }, f)
        inline = f.name
    code, _ = validate(inline)
    ok = code != 0
    print(f"{'回传数据本体（应拒绝）':<22}{'fail':<8}{'✓' if ok else '✗':<8}{f'exit={code}'}")
    if not ok:
        fails.append("回传数据本体: 校验未拒绝")
    os.unlink(inline)

    print(f"\n结论: {'6/6 符合预期' if not fails else '失败: ' + '; '.join(fails)}")
    return 1 if fails else 0


if __name__ == "__main__":
    sys.exit(main())
