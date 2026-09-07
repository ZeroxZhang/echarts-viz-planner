#!/usr/bin/env python3
"""validate_plan.py — echarts-viz-planner api 输出校验器（纯标准库）。

校验三层：
  A. 结构层（--schema）：对照 schemas/plan.schema.json。
     优先用 jsonschema；未安装时退回内置结构校验（必填字段/类型/枚举）。
  B. 事实层（默认开启）：capability_id 是否存在于能力目录、option 的 series 类型
     是否与 capability 匹配、encode 字段是否在数据画像内、status 一致性、零提问、无伪得分。
  C. 体积层：JSON ≤ 6KB。

用法：
    python3 validate_plan.py <plan.json> [--schema] [--allow-size N]
    无参数：自检（校验 schemas/plan.schema.json 本身 + 目录一致性）。

退出码：0 全部通过（警告不阻塞）；1 存在错误。
"""

import json
import os
import re
import sys

SKILL_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SCHEMA_PATH = os.path.join(SKILL_DIR, "schemas", "plan.schema.json")
INDEX_PATH = os.path.join(SKILL_DIR, "catalog", "index.md")
DETAILS_DIR = os.path.join(SKILL_DIR, "catalog", "details")
DEFAULT_SIZE_LIMIT = 6144  # 6KB

STATUS_ENUM = ["ok", "ok_with_assumptions", "insufficient_data", "unsupported", "policy_blocked"]
SCENARIO_ENUM = ["review", "executive", "exploration", "broadcast", "monitoring"]
CONFIDENCE_ENUM = ["high", "medium", "low"]
MATCH_ENUM = ["strong", "medium", "weak"]
ROLE_ENUM = ["primary", "support"]
IMPACT_ENUM = ["high", "medium", "low"]
RENDERER_ENUM = ["canvas", "svg"]
REF_TYPE_ENUM = ["inline", "file", "lark_sheet", "bitable", "aeolus", "hive", "lark_doc", "none"]

# capability_id → 允许的 series.type（None = 非 ECharts 模块，跳过 series 校验）
# 若与 catalog/index.md 不一致，以目录为准；此处漂移会在自检时提示。
SERIES_MAP = {
    "bar.basic": ["bar"], "bar.grouped": ["bar"], "bar.stacked": ["bar"], "bar.pct": ["bar"],
    "bar.rank": ["bar"], "bar.diverging": ["bar"], "bar.waterfall": ["bar"],
    "bar.dynamic": ["bar"], "bar.polar": ["bar"],
    "pictorial.lollipop": ["bar"], "pictorial.pictorial": ["pictorialBar"],
    "radar.radar": ["radar"],
    "ext.bar-range": ["custom"],
    "line.basic": ["line"], "line.multi": ["line"], "line.area": ["line"],
    "line.stacked_area": ["line"], "line.step": ["line"],
    "candlestick.k": ["candlestick"], "themeriver.themeriver": ["themeRiver"],
    "ext.line-range": ["custom"],
    "bar.hist": ["bar"], "boxplot.box": ["boxplot"],
    "ext.violin": ["custom"], "ext.contour": ["custom"], "scatter.beeswarm": ["custom"],
    "pie.basic": ["pie"], "pie.donut": ["pie"], "pie.rose": ["pie"],
    "ext.segmented-donut": ["custom"], "ext.wordcloud": ["custom"],
    "scatter.basic": ["scatter"], "scatter.bubble": ["scatter"], "scatter.quadrant": ["scatter"],
    "effectscatter.ripple": ["effectScatter"],
    "heatmap.matrix": ["heatmap"], "heatmap.calendar": ["heatmap"],
    "parallel.parallel": ["parallel"],
    "sankey.sankey": ["sankey"], "chord.chord": ["chord"], "funnel.funnel": ["funnel"],
    "ext.stage": ["custom"],
    "tree.tree": ["tree"], "treemap.treemap": ["treemap"], "sunburst.sunburst": ["sunburst"],
    "graph.force": ["graph"],
    "map.choropleth": ["map"], "map.scatter": ["map"], "lines.effect": ["lines"],
    "gauge.basic": ["gauge"], "gauge.bullet": ["bar"], "ext.liquidfill": ["custom"],
    "kpi.card": None,
    "table.detail": None, "table.pivot": None, "text.conclusion": None, "infographic": None,
    "custom.custom": ["custom"],
    "gl.bar3d": ["bar3D"], "gl.scatter3d": ["scatter3D"], "gl.surface": ["surface"],
}

# 禁止出现的伪得分字段
FORBIDDEN_SCORE_KEYS = ("score", "score_0_100", "weighted_score", "总得分", "评分")


class Report:
    def __init__(self):
        self.errors = []
        self.warnings = []

    def error(self, msg):
        self.errors.append(msg)

    def warn(self, msg):
        self.warnings.append(msg)

    def dump(self):
        for e in self.errors:
            print(f"[ERROR] {e}")
        for w in self.warnings:
            print(f"[WARN ] {w}")
        if self.errors:
            print(f"结果: 失败（{len(self.errors)} 错误, {len(self.warnings)} 警告）")
            return 1
        print(f"结果: 通过（{len(self.warnings)} 警告）")
        return 0


def load_catalog_ids():
    """从 index.md 表格与 details/*.yaml 解析全部合法 capability_id。"""
    ids = set()
    try:
        with open(INDEX_PATH, encoding="utf-8") as f:
            in_index = False
            for line in f:
                if line.startswith("## 全量索引"):
                    in_index = True
                    continue
                if in_index and line.startswith("## "):
                    break
                if in_index and line.startswith("|") and "|" in line[1:]:
                    cells = [c.strip() for c in line.strip().strip("|").split("|")]
                    if cells and cells[0] != "id" and re.match(r"^[a-z][a-z0-9-]*(\.[a-z][a-z0-9-]*)*$", cells[0]):
                        ids.add(cells[0])
    except FileNotFoundError:
        pass
    if os.path.isdir(DETAILS_DIR):
        for fn in os.listdir(DETAILS_DIR):
            if not fn.endswith(".yaml"):
                continue
            with open(os.path.join(DETAILS_DIR, fn), encoding="utf-8") as f:
                for line in f:
                    m = re.match(r"^- id:\s*(\S+)", line)
                    if m:
                        ids.add(m.group(1))
    return ids


def _type_check(rep, path, value, expect, required=True):
    if value is None and not required:
        return
    if expect == "string" and not isinstance(value, str):
        rep.error(f"{path}: 应为 string，实为 {type(value).__name__}")
    elif expect == "int" and (not isinstance(value, int) or isinstance(value, bool)):
        rep.error(f"{path}: 应为 integer")
    elif expect == "bool" and not isinstance(value, bool):
        rep.error(f"{path}: 应为 boolean")
    elif expect == "array" and not isinstance(value, list):
        rep.error(f"{path}: 应为 array")
    elif expect == "object" and not isinstance(value, dict):
        rep.error(f"{path}: 应为 object")


def _enum_check(rep, path, value, allowed):
    if value not in allowed:
        rep.error(f"{path}: '{value}' 不在封闭枚举 {allowed}")


def builtin_schema_check(plan, rep):
    """内置结构校验：覆盖 schemas/plan.schema.json 的关键约束。"""
    for key in ("contract_version", "mode", "status", "summary", "echarts", "intent", "data", "plan"):
        if key not in plan:
            rep.error(f"缺少必填字段: {key}")
    _type_check(rep, "summary", plan.get("summary"), "string")
    if plan.get("contract_version") != "1.0":
        rep.error(f"contract_version: 应为 1.0，实为 {plan.get('contract_version')!r}")
    if plan.get("mode") != "api":
        rep.error(f"mode: api 模式输出必须回显 'api'，实为 {plan.get('mode')!r}")
    _enum_check(rep, "status", plan.get("status"), STATUS_ENUM)

    ech = plan.get("echarts", {})
    _type_check(rep, "echarts", ech, "object")
    if ech.get("version") != "6.1.0":
        rep.error(f"echarts.version: 应为 6.1.0，实为 {ech.get('version')!r}")
    _type_check(rep, "echarts.deps", ech.get("deps"), "array")
    _enum_check(rep, "echarts.renderer", ech.get("renderer"), RENDERER_ENUM)

    intent = plan.get("intent", {})
    _type_check(rep, "intent", intent, "object")
    _type_check(rep, "intent.goal", intent.get("goal"), "string")
    _enum_check(rep, "intent.scenario", intent.get("scenario"), SCENARIO_ENUM)
    _type_check(rep, "intent.inferred", intent.get("inferred"), "bool")
    _enum_check(rep, "intent.confidence", intent.get("confidence"), CONFIDENCE_ENUM)

    data = plan.get("data", {})
    _type_check(rep, "data", data, "object")
    ref = data.get("ref", {})
    _enum_check(rep, "data.ref.type", ref.get("type"), REF_TYPE_ENUM)
    profile = data.get("profile", {})
    _type_check(rep, "data.profile", profile, "object")
    _type_check(rep, "data.profile.rows", profile.get("rows"), "int")
    _type_check(rep, "data.profile.dimensions", profile.get("dimensions"), "array")
    _type_check(rep, "data.profile.measures", profile.get("measures"), "array")
    binding = data.get("binding", {})
    _type_check(rep, "data.binding", binding, "object")
    _type_check(rep, "data.binding.required_fields", binding.get("required_fields"), "array")

    plist = plan.get("plan")
    _type_check(rep, "plan", plist, "array")
    if isinstance(plist, list):
        status_need_plan = plan.get("status") in ("ok", "ok_with_assumptions", "policy_blocked")
        if not plist and status_need_plan:
            rep.error(f"plan: status={plan.get('status')} 时不能为空数组（insufficient_data/unsupported 可为空）")
        primary = [p for p in plist if isinstance(p, dict) and p.get("role") == "primary"]
        if plist and not primary:
            rep.error("plan: 至少一个 role=primary")
        for i, item in enumerate(plist):
            p = f"plan[{i}]"
            if not isinstance(item, dict):
                rep.error(f"{p}: 应为 object"); continue
            _enum_check(rep, f"{p}.role", item.get("role"), ROLE_ENUM)
            _type_check(rep, f"{p}.capability_id", item.get("capability_id"), "string")
            _type_check(rep, f"{p}.question", item.get("question"), "string")
            _enum_check(rep, f"{p}.match", item.get("match"), MATCH_ENUM)
            _type_check(rep, f"{p}.option", item.get("option"), "object", required=False)
            for forbid in FORBIDDEN_SCORE_KEYS:
                _walk_keys(item, p, forbid, rep)

    for key, cls in (("alternatives", dict), ("rejected", dict), ("assumptions", dict),
                     ("open_questions", dict)):
        arr = plan.get(key)
        if arr is None:
            continue
        _type_check(rep, key, arr, "array")
        if isinstance(arr, list):
            for i, item in enumerate(arr):
                if not isinstance(item, dict):
                    rep.error(f"{key}[{i}]: 应为 object")
    _type_check(rep, "risks", plan.get("risks"), "array", required=False)
    _type_check(rep, "audit", plan.get("audit"), "object", required=False)

    # 条件约束（与 schema allOf 一致）
    status = plan.get("status")
    if status == "ok_with_assumptions":
        if not plan.get("assumptions"):
            rep.error("status=ok_with_assumptions 时 assumptions 必须非空")
    if status == "insufficient_data":
        if not plan.get("missing"):
            rep.error("status=insufficient_data 时 missing 必须非空")
    for i, q in enumerate(plan.get("open_questions", []) or []):
        if isinstance(q, dict) and q.get("blocking") is not False:
            rep.error(f"open_questions[{i}].blocking: api 模式禁止提问，必须为 false")


def _walk_keys(node, path, forbid, rep):
    if isinstance(node, dict):
        for k, v in node.items():
            if forbid in str(k).lower():
                rep.error(f"{path}.{k}: api 模式禁止伪数字得分字段")
            _walk_keys(v, f"{path}.{k}", forbid, rep)
    elif isinstance(node, list):
        for i, v in enumerate(node):
            _walk_keys(v, f"{path}[{i}]", forbid, rep)


def fact_check(plan, rep, size_limit):
    catalog_ids = load_catalog_ids()
    plist = plan.get("plan", [])
    used = set()
    for i, item in enumerate(plist):
        if not isinstance(item, dict):
            continue
        cid = item.get("capability_id")
        if not cid:
            continue
        p = f"plan[{i}].capability_id"
        used.add(cid)
        if cid not in catalog_ids:
            rep.error(f"{p}: '{cid}' 不在能力目录 catalog/index.md 中")
        allowed = SERIES_MAP.get(cid, "UNKNOWN")
        if allowed == "UNKNOWN":
            rep.warn(f"{p}: '{cid}' 无 series 映射（校验器与目录漂移），跳过 series 校验")
            continue
        if allowed is None:
            continue  # 非 ECharts 模块
        option = item.get("option") or {}
        series = option.get("series")
        if not isinstance(series, list) or not series:
            rep.warn(f"{p}: option 缺少 series（api 模式应给可直接运行的 option）")
            continue
        for s in series:
            stype = s.get("type") if isinstance(s, dict) else None
            if stype not in allowed:
                rep.error(f"{p}: series.type '{stype}' 与 capability 不符，允许 {allowed}")
        # 扩展依赖声明
        if cid.startswith("ext."):
            deps = plan.get("echarts", {}).get("deps") or []
            if not any(d.startswith("@echarts-x/") for d in deps):
                rep.error(f"{p}: 扩展候选 '{cid}' 必须在 echarts.deps 声明 @echarts-x 依赖")
        if cid.startswith("gl."):
            rep.error(f"{p}: echarts-gl 默认禁用，'{cid}' 仅在上游 allow_3d=true 时可用")

    # encode 的值（字段名）应在数据画像内；键（source/target/columns 等）是角色名
    profile = plan.get("data", {}).get("profile", {}) or {}
    known_fields = set(profile.get("dimensions", []) or []) | set(profile.get("measures", []) or [])
    if profile.get("time_field"):
        known_fields.add(profile["time_field"])
    for i, item in enumerate(plist):
        if not isinstance(item, dict) or not isinstance(item.get("encode"), dict):
            continue
        for v in item["encode"].values():
            vals = v if isinstance(v, list) else [v]
            for f in vals:
                if isinstance(f, str) and known_fields and f not in known_fields and f != "value":
                    rep.warn(f"plan[{i}].encode: 字段 '{f}' 不在 data.profile 中（可能为派生字段，请核对口径）")

    # alternatives / rejected 引用的 capability 也应存在
    for key in ("alternatives", "rejected"):
        for i, item in enumerate(plan.get(key, []) or []):
            cid = item.get("capability_id") if isinstance(item, dict) else None
            if cid and cid not in catalog_ids and cid != "none":
                rep.warn(f"{key}[{i}].capability_id: '{cid}' 不在能力目录中")
    # policy_blocked 理由规范
    for i, item in enumerate(plan.get("rejected", []) or []):
        if isinstance(item, dict) and item.get("reason") == "policy_blocked":
            rep.warn(f"rejected[{i}]: policy_blocked 应同时给出原生替代（放 alternatives）")

    # 数据回传禁令：检测是否回传了数据本体（data.inline 携带行数据）
    raw = json.dumps(plan, ensure_ascii=False)
    if len(raw.encode("utf-8")) > size_limit:
        rep.error(f"输出 {len(raw.encode('utf-8'))}B 超过 {size_limit}B 上限（6KB），请裁剪 rejected/audit 明细")
    if "inline" in plan.get("data", {}):
        rep.error("api 模式禁止回传数据本体：请删除 data.inline 行数据，只保留 data.ref + data.binding")

    # audit 计数一致性（存在时）
    audit = plan.get("audit") or {}
    if audit:
        if audit.get("candidates", 0) < len(plist):
            rep.warn(f"audit.candidates({audit.get('candidates')}) 小于 plan 长度({len(plist)})")
        if audit.get("rejected", 0) < len(plan.get("rejected", []) or []):
            rep.warn("audit.rejected 小于 rejected 明细长度")
    if len(used) != len(set(used)):
        rep.warn("plan 中存在重复 capability_id")


def main(argv):
    if len(argv) < 2:
        # 自检：schema 文件合法 + SERIES_MAP 与目录一致性
        print("自检模式")
        rep = Report()
        try:
            with open(SCHEMA_PATH, encoding="utf-8") as f:
                json.load(f)
            print("[OK  ] schemas/plan.schema.json 是合法 JSON")
        except (FileNotFoundError, json.JSONDecodeError) as e:
            rep.error(f"schema 读取失败: {e}")
        catalog_ids = load_catalog_ids()
        if catalog_ids:
            missing = catalog_ids - set(SERIES_MAP.keys())
            for cid in sorted(missing):
                rep.warn(f"目录中存在但 SERIES_MAP 缺映射: {cid}（validate_plan.py 需同步）")
            print(f"[INFO] 目录能力数: {len(catalog_ids)}, 校验器映射数: {len(SERIES_MAP)}")
        return rep.dump()

    path = argv[1]
    use_schema = "--schema" in argv
    size_limit = DEFAULT_SIZE_LIMIT
    if "--allow-size" in argv:
        size_limit = int(argv[argv.index("--allow-size") + 1])
    try:
        with open(path, encoding="utf-8") as f:
            plan = json.load(f)
    except FileNotFoundError:
        print(f"文件不存在: {path}", file=sys.stderr)
        return 1
    except json.JSONDecodeError as e:
        print(f"JSON 解析失败: {e}", file=sys.stderr)
        return 1

    rep = Report()
    if use_schema:
        try:
            import jsonschema  # noqa: F401
            with open(SCHEMA_PATH, encoding="utf-8") as f:
                schema = json.load(f)
            v = jsonschema.Draft7Validator(schema)
            for err in sorted(v.iter_errors(plan), key=lambda e: list(e.path)):
                rep.error(f"schema: {'/'.join(map(str, err.path)) or '(root)'}: {err.message}")
        except ImportError:
            builtin_schema_check(plan, rep)
    fact_check(plan, rep, size_limit)
    return rep.dump()


if __name__ == "__main__":
    sys.exit(main(sys.argv))
