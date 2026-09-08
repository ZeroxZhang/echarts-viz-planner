#!/usr/bin/env python3
"""validate_plan.py — echarts-viz-planner api 输出校验器（纯标准库）。

校验三层：
  A. 结构层（--schema）：对照 schemas/plan.schema.json。
     始终运行内置 schema 子集检查；jsonschema 可用时附加标准 Draft 7 检查。
  B. 事实层（默认开启）：capability_id 是否存在于能力目录、option 的 series 类型
     是否与 capability 匹配、encode 字段是否在数据画像内、status 一致性、零提问、无伪得分。
  C. 体积层：JSON ≤ 6KB。

用法：
    python3 validate_plan.py <plan.json> [--schema] [--builtin-only] [--allow-size N]
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


def load_catalog_dependencies():
    """从目录状态列读取唯一的精确依赖版本，不维护第二份版本表。"""
    deps = {}
    with open(INDEX_PATH, encoding="utf-8") as f:
        for line in f:
            cells = [cell.strip() for cell in line.strip().strip("|").split("|")]
            if len(cells) == 6 and cells[0] in SERIES_MAP:
                match = re.search(r"ext:([^\s]+)", cells[-1])
                if match: deps[cells[0]] = match.group(1)
    return deps


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


def schema_check(value, schema, rep, path="(root)"):
    """本地 schema 使用的 Draft 7 子集；无 jsonschema 时检查相同结构约束。"""
    checks = {"object": lambda v: isinstance(v, dict), "array": lambda v: isinstance(v, list),
              "string": lambda v: isinstance(v, str), "integer": lambda v: isinstance(v, int) and not isinstance(v, bool),
              "boolean": lambda v: isinstance(v, bool), "null": lambda v: v is None}
    types = schema.get("type", [])
    types = [types] if isinstance(types, str) else types
    if types and not any(checks[k](value) for k in types):
        rep.error(f"{path}: 应为 {types}"); return
    if "const" in schema and (value != schema["const"] or type(value) is not type(schema["const"])):
        rep.error(f"{path}: 应为 {schema['const']!r}")
    if "enum" in schema and value not in schema["enum"]:
        rep.error(f"{path}: 不在枚举 {schema['enum']}")
    if isinstance(value, str) and len(value) < schema.get("minLength", 0):
        rep.error(f"{path}: 字符串不能为空")
    if isinstance(value, int) and value < schema.get("minimum", value):
        rep.error(f"{path}: 小于最小值")
    if isinstance(value, dict):
        for key in schema.get("required", []):
            if key not in value: rep.error(f"{path}: 缺少 {key}")
        if len(value) < schema.get("minProperties", 0): rep.error(f"{path}: 对象不能为空")
        props = schema.get("properties", {})
        for key, val in value.items():
            child = props.get(key, schema.get("additionalProperties", {}))
            if child is False: rep.error(f"{path}.{key}: 未允许的字段")
            elif isinstance(child, dict): schema_check(val, child, rep, f"{path}.{key}")
    if isinstance(value, list):
        if len(value) < schema.get("minItems", 0): rep.error(f"{path}: 数组元素不足")
        for i, val in enumerate(value): schema_check(val, schema.get("items", {}), rep, f"{path}[{i}]")
    def matches(sub):
        test = Report(); schema_check(value, sub, test, path); return not test.errors
    for sub in schema.get("allOf", []): schema_check(value, sub, rep, path)
    if "anyOf" in schema and not any(matches(sub) for sub in schema["anyOf"]): rep.error(f"{path}: 不满足 anyOf")
    if "oneOf" in schema and sum(matches(sub) for sub in schema["oneOf"]) != 1: rep.error(f"{path}: 应恰好满足一种结构")
    if "not" in schema and matches(schema["not"]): rep.error(f"{path}: 不允许该结构")
    if "if" in schema:
        schema_check(value, schema.get("then" if matches(schema["if"]) else "else", {}), rep, path)


def builtin_schema_check(plan, rep):
    with open(SCHEMA_PATH, encoding="utf-8") as f:
        schema_check(plan, json.load(f), rep)


def read_reference(ref, base_dir, rep, path):
    target = os.path.join(base_dir, ref["path"])
    try:
        with open(target, encoding="utf-8") as f: return json.load(f)
    except (OSError, ValueError) as exc:
        rep.error(f"{path}: 无法读取 JSON 规格 {target}: {exc}")
        return None


def v11_check(plan, rep, base_dir):
    """语义交接检查；引用规格与内联规格执行相同校验。"""
    if plan.get("contract_version") != "1.1": return
    def meaningful(node):
        if isinstance(node, str): return bool(node.strip())
        if isinstance(node, dict): return any(meaningful(v) for v in node.values())
        if isinstance(node, list): return any(meaningful(v) for v in node)
        return False
    with open(SCHEMA_PATH, encoding="utf-8") as f:
        spec_schema = json.load(f)["properties"]["plan"]["items"]["properties"]["spec"]
    for i, module in enumerate(plan["plan"]):
        prefix = f"plan[{i}]"
        spec = module.get("spec")
        if "spec_ref" in module: spec = read_reference(module["spec_ref"], base_dir, rep, prefix + ".spec_ref")
        # 成功读取的 JSON null 也必须失败；不能与读取错误共用跳过分支。
        local = Report(); schema_check(spec, spec_schema, local, prefix + ".spec")
        rep.errors.extend(local.errors)
        if local.errors: continue
        if spec["kind"] == "infographic" and not meaningful(spec["structure"]):
            rep.error(f"{prefix}.spec.structure: 需要可制作的实际内容，空集合不构成规格")
        cid = module["capability_id"]
        expected = "table" if cid.startswith("table.") else {"text.conclusion":"text", "infographic":"infographic", "kpi.card":"kpi"}.get(cid, "echarts")
        if spec["kind"] != expected: rep.error(f"{prefix}: capability {cid} 要求 spec.kind={expected}")
        if expected in ("echarts", "table", "kpi") and not module.get("bindings"):
            rep.error(f"{prefix}: {expected} 需要模块级 bindings")
        if "implementation_ref" in module:
            implementation = read_reference(module["implementation_ref"], base_dir, rep, prefix + ".implementation_ref")
            if not isinstance(implementation, dict) or not isinstance(implementation.get("option"), dict):
                rep.error(f"{prefix}.implementation_ref: 文件必须包含 option 对象")
            else:
                with open(SCHEMA_PATH, encoding="utf-8") as f:
                    option_schema = json.load(f)["properties"]["plan"]["items"]["properties"]["option"]
                before = len(rep.errors)
                schema_check(implementation["option"], option_schema, rep, prefix + ".implementation_ref.option")
                if len(rep.errors) > before: continue
                module["option"] = implementation["option"]
        if expected == "echarts" and plan.get("output_level", "implementation") == "implementation":
            if not module.get("option"):
                rep.error(f"{prefix}: implementation 需要 option 或可读 implementation_ref")
        if any(s.get("type") == "custom" for s in module.get("option", {}).get("series", []) if isinstance(s, dict)):
            for series in module.get("option", {}).get("series", []):
                if isinstance(series, dict) and isinstance(series.get("renderItem"), str) and ("=>" in series["renderItem"] or "function" in series["renderItem"]):
                    rep.error(f"{prefix}: JSON 中的函数字符串不是可执行 renderItem；使用上游注册的 renderer 并说明实现依赖")
        static = plan.get("constraints", {}).get("static", False)
        if static:
            adaptation = module.get("carrier_adaptation", {}).get("static", {})
            if not isinstance(adaptation, dict) or not isinstance(adaptation.get("essential_information"), str) or not adaptation["essential_information"].strip():
                rep.error(f"{prefix}: static 模式需要 carrier_adaptation.static.essential_information，说明核心信息如何无需交互可见")


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
    catalog_deps = load_catalog_dependencies()
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
        # 1.1 在 decision 和 implementation 同样检查准确依赖及显式约束。
        deps = plan.get("echarts", {}).get("deps") or []
        if plan.get("contract_version") == "1.1":
            required_dep = catalog_deps.get(cid)
            constraints = plan.get("constraints", {})
            if required_dep:
                if required_dep not in deps:
                    rep.error(f"{p}: 目录要求精确依赖 {required_dep}")
                if constraints.get("allow_extensions") is False:
                    rep.error(f"{p}: allow_extensions=false 禁止该扩展")
                available = constraints.get("runtime", {}).get("available_dependencies")
                if isinstance(available, list) and required_dep not in available:
                    rep.error(f"{p}: {required_dep} 不在上游 available_dependencies 中")
            if cid.startswith("gl.") and constraints.get("allow_3d") is not True:
                rep.error(f"{p}: echarts-gl 需要显式 allow_3d=true")
        else:
            if cid.startswith("ext.") and not any(d.startswith("@echarts-x/") for d in deps):
                rep.error(f"{p}: 扩展候选 '{cid}' 必须在 echarts.deps 声明 @echarts-x 依赖")
            if cid.startswith("gl."):
                rep.error(f"{p}: echarts-gl 默认禁用，'{cid}' 仅在上游 allow_3d=true 时可用")

        option = item.get("option") or {}
        series = option.get("series")
        if not isinstance(series, list) or not series:
            if plan.get("output_level", "implementation") == "implementation":
                (rep.error if plan.get("contract_version") == "1.1" else rep.warn)(f"{p}: option 缺少 series")
            continue
        for s in series:
            stype = s.get("type") if isinstance(s, dict) else None
            if stype not in allowed:
                rep.error(f"{p}: series.type '{stype}' 与 capability 不符，允许 {allowed}")

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
    # 总是先做类型检查，阻止畸形 JSON 在事实校验中触发 AttributeError。
    builtin_schema_check(plan, rep)
    if rep.errors: return rep.dump()
    if use_schema and "--builtin-only" not in argv:
        try:
            import jsonschema
            with open(SCHEMA_PATH, encoding="utf-8") as f:
                schema = json.load(f)
            for err in jsonschema.Draft7Validator(schema).iter_errors(plan):
                rep.error(f"schema: {'/'.join(map(str, err.path)) or '(root)'}: {err.message}")
        except ImportError:
            pass
    # 体积检查针对交接本体，引用解析后只用于内容验证。
    original_size = len(json.dumps(plan, ensure_ascii=False).encode("utf-8"))
    v11_check(plan, rep, os.path.dirname(os.path.abspath(path)))
    if rep.errors: return rep.dump()
    fact_check(plan, rep, max(size_limit, len(json.dumps(plan, ensure_ascii=False).encode("utf-8"))))
    if original_size > size_limit: rep.error(f"输出 {original_size}B 超过 {size_limit}B 上限")
    if plan["plan"] and not any(p["role"] == "primary" for p in plan["plan"]): rep.error("plan: 至少需要一个 primary")
    for forbid in FORBIDDEN_SCORE_KEYS: _walk_keys(plan, "(root)", forbid, rep)
    return rep.dump()


if __name__ == "__main__":
    sys.exit(main(sys.argv))
