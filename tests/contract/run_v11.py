#!/usr/bin/env python3
"""1.1 交接回归：运行真实 CLI，覆盖新旧输出级别、语义、引用及离线校验。

临时文件自动清理；有 jsonschema 时同时覆盖标准库和 Draft 7 路径。
缺少 jsonschema 时明确跳过附加标准校验，不冒称运行过两种后端。
"""

import copy
import importlib.util
import json
from pathlib import Path
import subprocess
import sys
import tempfile

ROOT = Path(__file__).resolve().parents[2]
VALIDATOR = ROOT / "scripts/validate_plan.py"


def plan(kind="echarts"):
    cid = {"echarts": "bar.rank", "table": "table.detail", "text": "text.conclusion",
           "infographic": "infographic", "kpi": "kpi.card"}[kind]
    spec = {"kind": kind, "message": "按部门比较并核对工单数",
            "evidence_refs": ["data.csv"], "boundaries": ["不推断原因"]}
    spec.update({
        "echarts": {"mapping": {"category": "department", "value": "count"},
                    "comparison_basis": "同一期，各部门工单数，单位件"},
        "table": {"columns": [{"field": "department", "label": "部门"},
                              {"field": "count", "label": "工单数"}],
                  "row_organization": "每部门一行，保持源顺序", "lookup_task": "查询每部门工单数"},
        "text": {"text": "本表可查询各部门工单数，不能用于推断原因。"},
        "infographic": {"structure": {"stages": ["登记", "复核"]},
                        "relationship_semantics": "箭头只表示先后步骤", "reading_order": ["登记", "复核"]},
        "kpi": {"metric": "count", "comparison_basis": "无目标值，只报本期计数", "format": "整数，件"},
    }[kind])
    module = {"role": "primary", "capability_id": cid, "question": "各部门工单数是多少？",
              "match": "strong", "rationale": "按读者查数及比较任务组织内容", "spec": spec,
              "carrier_adaptation": {"static": {"essential_information": "部门、数值和单位直接可见"}}}
    if kind in ("echarts", "table", "kpi"):
        module["bindings"] = [{"target": "dataset.source" if kind == "echarts" else "rows",
                               "ref": {"type": "file", "id": "data.csv"},
                               "expects": "array<object>", "required_fields": ["department", "count"]}]
    return {"contract_version": "1.1", "mode": "api", "output_level": "decision", "status": "ok",
            "summary": "呈现部门工单数", "echarts": {"version": "6.1.0", "deps": [], "renderer": "svg"},
            "intent": {"goal": "比较部门", "scenario": "executive", "inferred": False, "confidence": "high"},
            "data": {"ref": {"type": "file", "id": "data.csv"}, "transform_policy": "propose",
                     "profile": {"rows": 4, "dimensions": ["department"], "measures": ["count"]},
                     "binding": {"mode": "dataset.source", "expects": "array<object>",
                                 "required_fields": ["department", "count"]}},
            "constraints": {"static": True, "offline": True}, "plan": [module]}


def main():
    cases = []

    def add(name, value, error=None, refs=None):
        cases.append((name, copy.deepcopy(value), error, refs or {}))

    def changed(name, mutate, error, kind="echarts"):
        value = plan(kind)
        mutate(value)
        add(name, value, error)

    for kind in ("echarts", "table", "text", "infographic", "kpi"):
        add(kind + " decision", plan(kind))
    value = plan()
    value["output_level"] = "implementation"
    value["plan"][0]["option"] = {"series": [{"type": "bar"}]}
    add("implementation option", value)
    del value["output_level"]
    add("缺省仍为 implementation", value)
    changed("缺省实现不可缺 option", lambda p: p.pop("output_level"), "implementation 需要")
    changed("显式实现不可缺 option", lambda p: p.update(output_level="implementation"), "implementation 需要")
    changed("1.0 不接受 decision", lambda p: p.update(contract_version="1.0"), "implementation")
    changed("缺选型理由", lambda p: p["plan"][0].pop("rationale"), "rationale")
    changed("缺语义规格", lambda p: p["plan"][0].pop("spec"), "恰好")
    changed("内联与引用不能同时存在", lambda p: p["plan"][0].update(spec_ref={"path": "other.json"}), "恰好")
    changed("kind 不匹配能力", lambda p: p["plan"][0].update(capability_id="text.conclusion"), "spec.kind=text")
    changed("空图表映射", lambda p: p["plan"][0]["spec"].update(mapping={}), "不能为空")
    for kind, field in (("table", "columns"), ("text", "text"), ("infographic", "relationship_semantics"), ("kpi", "metric")):
        changed("缺 " + kind + " 语义", lambda p, f=field: p["plan"][0]["spec"].pop(f), field, kind)
    changed("空信息图内容", lambda p: p["plan"][0]["spec"].update(structure={"nodes": []}), "实际内容", "infographic")
    for kind in ("echarts", "table", "kpi"):
        changed(kind + " 缺模块绑定", lambda p: p["plan"][0].pop("bindings"), "模块级 bindings", kind)
    changed("空绑定引用", lambda p: p["plan"][0]["bindings"][0]["ref"].update(id=""), "不能为空")
    changed("静态核心信息不可缺", lambda p: p["plan"][0].pop("carrier_adaptation"), "essential_information")
    changed("交互不强制静态适配", lambda p: (p["constraints"].update(static=False), p["plan"][0].pop("carrier_adaptation")), None)
    changed("未知能力", lambda p: p["plan"][0].update(capability_id="bar.invented"), "不在能力目录")
    changed("禁止回传原始数据", lambda p: p["data"].update(inline=[{"count": 1}]), "禁止回传数据本体")
    changed("禁止虚构评分", lambda p: p["plan"][0].update(score=99), "score")
    changed("禁止阻断性提问", lambda p: p.update(open_questions=[{"q": "单位？", "default_used": "件", "blocking": True}]), "False")
    changed("无数据需说明缺口", lambda p: p.update(status="insufficient_data", plan=[]), "missing")
    value = plan()
    value.update(status="insufficient_data", plan=[], missing=[{"what": "数据", "why_needed": "查数", "how_to_get": "提供导出"}])
    add("无数据正常返回", value)
    changed("本体超限", lambda p: p.update(summary="x" * 7000), "上限")
    add("null 根对象", None, "应为")
    add("数组根对象", [], "应为")
    changed("畸形模块", lambda p: p.update(plan=[None]), "应为")

    value = plan("infographic")
    spec = value["plan"][0].pop("spec")
    spec["structure"]["notes"] = "详" * 2500
    value["plan"][0]["spec_ref"] = {"path": "specs/flow.json"}
    add("真实相对引用且规格超过6KB", value, refs={"specs/flow.json": spec})
    add("丢失引用", value, "无法读取")
    add("引用JSON null", value, "应为", {"specs/flow.json": None})
    add("引用损坏JSON", value, "无法读取", {"specs/flow.json": "{broken"})
    bad_spec = copy.deepcopy(spec)
    bad_spec.pop("reading_order")
    add("引用也检查语义", value, "reading_order", {"specs/flow.json": bad_spec})

    value = plan()
    value["output_level"] = "implementation"
    value["plan"][0]["implementation_ref"] = {"path": "impl/option.json"}
    option = {"option": {"series": [{"type": "bar"}], "aria": {"description": "静" * 2500}}}
    add("独立实现引用且内容超过6KB", value, refs={"impl/option.json": option})
    add("丢失实现引用", value, "无法读取")
    add("实现引用null", value, "option 对象", {"impl/option.json": None})
    add("实现option畸形", value, "应为", {"impl/option.json": {"option": {"series": [None]}}})
    add("实现series与能力不符", value, "与 capability 不符", {"impl/option.json": {"option": {"series": [{"type": "pie"}]}}})

    value = plan()
    value["plan"][0]["capability_id"] = "ext.bar-range"
    dep = "@echarts-x/custom-bar-range@1.2.1"
    value["echarts"]["deps"] = [dep]
    value["constraints"].update(allow_extensions=True, runtime={"available_dependencies": [dep]})
    add("扩展精确版本可用", value)
    value["echarts"]["deps"] = ["@echarts-x/custom-bar-range@1.2.0"]
    add("扩展错版本", value, "精确依赖")
    value["echarts"]["deps"] = [dep]
    value["constraints"]["runtime"]["available_dependencies"] = []
    add("支持但未安装扩展", value, "available_dependencies")
    value["constraints"].pop("runtime")
    value["constraints"]["allow_extensions"] = False
    add("策略禁用扩展", value, "allow_extensions=false")

    value = plan()
    value["plan"][0]["capability_id"] = "gl.bar3d"
    value["echarts"]["deps"] = ["echarts-gl@2.1.0"]
    value["constraints"]["allow_3d"] = True
    add("显式允许3D", value)
    del value["constraints"]["allow_3d"]
    add("默认禁用3D", value, "allow_3d=true")
    value = plan()
    value["plan"][0].update(capability_id="custom.custom", option={"series": [{"type": "custom", "renderItem": "function() {}"}]})
    add("函数字符串不冒充实现", value, "函数字符串")

    backends = [("stdlib", [sys.executable, "-S"], ["--schema", "--builtin-only"])]
    if importlib.util.find_spec("jsonschema"):
        backends.append(("jsonschema", [sys.executable], ["--schema"]))
    else:
        print("[SKIP] 未安装 jsonschema；仅验证纯标准库路径")
    failures = []
    with tempfile.TemporaryDirectory(prefix="viz-contract-v11-") as tmp:
        base = Path(tmp)
        for index, (name, value, error, refs) in enumerate(cases):
            case_dir = base / str(index)
            case_dir.mkdir()
            file = case_dir / "plan.json"
            file.write_text(json.dumps(value, ensure_ascii=False), encoding="utf-8")
            for relative, content in refs.items():
                ref = case_dir / relative
                ref.parent.mkdir(parents=True, exist_ok=True)
                ref.write_text(content if isinstance(content, str) else json.dumps(content, ensure_ascii=False), encoding="utf-8")
            before = {p: p.read_bytes() for p in case_dir.rglob("*") if p.is_file()}
            for backend, python, flags in backends:
                result = subprocess.run(python + [str(VALIDATOR), str(file)] + flags,
                                        cwd=base, text=True, capture_output=True, timeout=30)
                output = result.stdout + result.stderr
                ok = result.returncode == 0 if error is None else result.returncode == 1 and error in output
                ok = ok and "Traceback" not in output
                if not ok:
                    failures.append(f"{name} / {backend}: {output}")
            if any(p.read_bytes() != content for p, content in before.items()):
                failures.append(name + ": 校验器改写了输入")
    for failure in failures:
        print("[FAIL] " + failure)
    print(f"{len(cases)} 用例 × {len(backends)} 后端 = {len(cases) * len(backends)} 次，失败 {len(failures)}")
    return 1 if failures else 0


if __name__ == "__main__":
    sys.exit(main())
