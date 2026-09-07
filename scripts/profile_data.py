#!/usr/bin/env python3
"""profile_data.py — 本地表格数据画像（echarts-viz-planner 取数环节，interactive/api 通用）。

用途：对本地 CSV / JSON 数组 / JSONL 产出结构化画像，供选型 Step 1/3 使用。
约束：纯标准库（csv/json），Excel 仅在 pandas 可用时支持，否则给出转换指引。

用法：
    python3 profile_data.py <文件路径> [--max-rows N] [--sample-seed S]

输出（stdout）：JSON 画像
{
  "file": "...", "format": "csv|json|jsonl|xlsx",
  "rows": 4820, "sampled": false,
  "columns": [
    { "name": "channel", "type": "string", "null_count": 0, "missing_rate": 0.0,
      "unique": 12, "cardinality": 12, "numeric_range": null, "max_len": 8 }
  ],
  "duplicates": 0, "possible_time_fields": ["date"],
  "suggested_dimensions": ["channel", "stage"], "suggested_measures": ["users"],
  "warnings": ["类目数 200 超过阈值，建议聚合或抽样"]
}
退出码：0 成功；1 文件不可读；2 格式不支持。
"""

import csv
import io
import json
import math
import sys
from datetime import datetime


DATE_FORMATS = (
    "%Y-%m-%d", "%Y/%m/%d", "%Y-%m-%d %H:%M:%S", "%Y/%m/%d %H:%M:%S",
    "%Y-%m-%d %H:%M", "%Y年%m月%d日", "%d-%m-%Y",
)
TIME_HINT_NAMES = ("date", "time", "日期", "时间", "day", "month", "week", "dt", "period")


def _parse_number(s):
    try:
        f = float(s)
        return f
    except (TypeError, ValueError):
        return None


def _parse_datetime(s):
    s = s.strip()
    for fmt in DATE_FORMATS:
        try:
            return datetime.strptime(s, fmt)
        except ValueError:
            continue
    return None


def _classify(values):
    """返回 (type, extra)：type ∈ numeric|integer|datetime|string|bool；extra 为统计。"""
    non_null = [v for v in values if v not in (None, "")]
    if not non_null:
        return "string", {}
    nums, ints, dts, bools = [], [], [], []
    for v in non_null:
        s = str(v).strip()
        if s.lower() in ("true", "false"):
            bools.append(s.lower() == "true")
            continue
        n = _parse_number(s)
        if n is not None:
            nums.append(n)
            if n.is_integer():
                ints.append(n)
            continue
        if _parse_datetime(s) is not None:
            dts.append(s)
    total = len(non_null)
    if len(bools) == total:
        return "bool", {"true_count": sum(bools)}
    if len(nums) == total:
        if len(ints) == total:
            return "integer", _num_stats(ints)
        return "numeric", _num_stats(nums)
    if len(dts) == total:
        return "datetime", {"min": min(dts), "max": max(dts)}
    return "string", {"max_len": max(len(str(v)) for v in non_null)}


def _num_stats(nums):
    n = len(nums)
    mean = sum(nums) / n
    var = sum((x - mean) ** 2 for x in nums) / n
    return {
        "min": min(nums), "max": max(nums), "mean": round(mean, 6),
        "std": round(math.sqrt(var), 6),
    }


def _read_csv(path, max_rows):
    with open(path, "r", encoding="utf-8-sig", errors="replace", newline="") as f:
        sample = f.read(8192)
        f.seek(0)
        try:
            dialect = csv.Sniffer().sniff(sample, delimiters=",;\t|")
        except csv.Error:
            dialect = csv.excel
        reader = csv.DictReader(f, dialect=dialect)
        fields = reader.fieldnames or []
        rows = []
        for i, row in enumerate(reader):
            rows.append(row)
            if max_rows and i + 1 >= max_rows:
                break
        return "csv", fields, rows


def _read_json(path, max_rows):
    with open(path, "r", encoding="utf-8-sig") as f:
        text = f.read().lstrip()
    if text.startswith("["):
        data = json.loads(text)
        rows = data if max_rows is None else data[:max_rows]
        # 键取全量并集：首行可能缺字段（如扁平邻接表首行无 parent/size）
        fields = []
        for r in rows:
            if isinstance(r, dict):
                for k in r:
                    if k not in fields:
                        fields.append(k)
        return "json", fields, rows
    # JSONL：逐行 JSON 对象
    rows, fields = [], []
    for line in text.splitlines():
        line = line.strip()
        if not line:
            continue
        obj = json.loads(line)
        if not isinstance(obj, dict):
            raise ValueError("JSONL 行不是对象")
        rows.append(obj)
        for k in obj:
            if k not in fields:
                fields.append(k)
        if max_rows and len(rows) >= max_rows:
            break
    return "jsonl", fields, rows


def _read_excel(path, max_rows):
    try:
        import pandas as pd  # noqa: F401
    except ImportError:
        raise RuntimeError(
            "Excel 需 pandas/openpyxl。请先导出为 CSV 再运行，或用 lark-drive 转换为 sheet 后取数。"
        )
    df = pd.read_excel(path, nrows=max_rows)
    fields = [str(c) for c in df.columns]
    rows = [dict(zip(fields, map(_norm_cell, r))) for r in df.itertuples(index=False)]
    return "xlsx", fields, rows


def _norm_cell(v):
    if v is None or (isinstance(v, float) and math.isnan(v)):
        return None
    return v


def main(argv):
    if len(argv) < 2:
        print(__doc__)
        return 1
    path = argv[1]
    max_rows, seed = None, None
    i = 2
    while i < len(argv):
        if argv[i] == "--max-rows" and i + 1 < len(argv):
            max_rows = int(argv[i + 1]); i += 2
        elif argv[i] == "--sample-seed" and i + 1 < len(argv):
            seed = int(argv[i + 1]); i += 2
        else:
            print(f"未知参数: {argv[i]}", file=sys.stderr)
            return 1
    try:
        ext = path.rsplit(".", 1)[-1].lower() if "." in path else ""
        if ext == "csv":
            fmt, fields, rows = _read_csv(path, max_rows)
        elif ext == "json":
            fmt, fields, rows = _read_json(path, max_rows)
        elif ext in ("jsonl", "ndjson"):
            fmt, fields, rows = _read_json(path, max_rows)
        elif ext in ("xlsx", "xls"):
            fmt, fields, rows = _read_excel(path, max_rows)
        else:
            print(f"不支持的文件格式: .{ext}（支持 csv/json/jsonl/xlsx）", file=sys.stderr)
            return 2
    except FileNotFoundError:
        print(f"文件不存在: {path}", file=sys.stderr)
        return 1
    except (json.JSONDecodeError, ValueError) as e:
        print(f"解析失败: {e}", file=sys.stderr)
        return 2
    except RuntimeError as e:
        print(str(e), file=sys.stderr)
        return 2

    if not fields or not rows:
        print("空数据：无字段或无行", file=sys.stderr)
        return 2

    columns, dims, measures, time_fields = [], [], [], []
    for f in fields:
        values = [r.get(f) for r in rows]
        typ, extra = _classify(values)
        nulls = sum(1 for v in values if v in (None, ""))
        uniq = len(set(str(v) for v in values if v not in (None, "")))
        col = {
            "name": f, "type": typ, "null_count": nulls,
            "missing_rate": round(nulls / len(values), 4),
            "unique": uniq,
            "cardinality": uniq,
        }
        col.update(extra)
        columns.append(col)
        if typ == "datetime":
            time_fields.append(f)
        elif typ in ("numeric", "integer"):
            if uniq <= 12:
                dims.append(f)   # 低基数数值（如年份/等级）更可能是维度
            else:
                measures.append(f)
        else:
            dims.append(f)

    for name in TIME_HINT_NAMES:
        for c in columns:
            if c["name"] not in time_fields and c["type"] in ("string", "integer"):
                low = c["name"].lower()
                if any(k in low for k in ("duration", "running time", "时长")):
                    continue  # 时长不是时间点
                if name in low:
                    time_fields.append(c["name"])

    seen, dup = set(), 0
    for r in rows:
        key = json.dumps(sorted(r.items()), ensure_ascii=False, default=str)
        if key in seen:
            dup += 1
        else:
            seen.add(key)

    warnings = []
    if len(rows) > 50000:
        warnings.append("行数超过 5 万，建议先聚合或抽样（配 dataZoom + thumbnail）")
    for c in columns:
        if c["type"] in ("string", "integer") and c["cardinality"] > 200:
            warnings.append(f"字段 {c['name']} 基数 {c['cardinality']} 超过 200，建议聚合或抽样")
        if c["missing_rate"] > 0.5:
            warnings.append(f"字段 {c['name']} 缺失率 {c['missing_rate']:.0%} 过高，使用前建议评估")

    out = {
        "file": path, "format": fmt, "rows": len(rows),
        "sampled": max_rows is not None, "sample_seed": seed,
        "columns": columns, "duplicates": dup,
        "possible_time_fields": time_fields,
        "suggested_dimensions": dims, "suggested_measures": measures,
        "warnings": warnings,
    }
    print(json.dumps(out, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv))
