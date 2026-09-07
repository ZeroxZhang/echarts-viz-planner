#!/usr/bin/env python3
"""check_version.py — ECharts 技术基线离线核验（echarts-viz-planner 版本机制 §16.2）。

职责：比对 npm 最新版与锁定基线 6.1.0，diff 核心系列与组件导出，复查扩展包 peer 范围。
设计：仅只读网络（registry.npmjs.org + raw.githubusercontent.com），不改任何文件；
      运行时不查 npm latest 是运行时规则，本脚本是**定期离线核验**，两者不冲突。
网络不可用时输出快照态说明，不报错。

用法：
    python3 check_version.py            # 人类可读报告
    python3 check_version.py --json     # JSON 报告
退出码：0 无差异；1 存在差异（目录需同步更新后才允许改基线）；2 网络不可用。
"""

import json
import re
import ssl
import sys
import urllib.request
from datetime import datetime, timezone

BASELINE = "6.1.0"
UA = {"User-Agent": "echarts-viz-planner/check_version 0.2"}
CTX = ssl.create_default_context()

# 锁定基线的核心系列（23，核验于 apache/echarts@6.1.0 src/export/charts.ts）
CORE_SERIES = [
    "line", "bar", "pie", "scatter", "effectScatter", "radar", "map", "tree",
    "treemap", "sunburst", "graph", "chord", "sankey", "funnel", "gauge",
    "parallel", "boxplot", "candlestick", "heatmap", "lines", "pictorialBar",
    "themeRiver", "custom",
]
# 锁定基线的关键组件（含 ECharts 6 新增 Matrix / Thumbnail）
CORE_COMPONENTS = [
    "MatrixComponent", "ThumbnailComponent", "DatasetComponent", "TransformComponent",
    "VisualMapComponent", "DataZoomComponent", "TimelineComponent", "BrushComponent",
    "ToolboxComponent", "GraphicComponent", "LegendComponent", "TooltipComponent",
    "AxisPointerComponent", "TitleComponent", "AriaComponent", "MarkPointComponent",
    "MarkLineComponent", "MarkAreaComponent", "CalendarComponent", "GeoComponent",
]
EXTENSIONS = [
    "@echarts-x/custom-violin", "@echarts-x/custom-contour",
    "@echarts-x/custom-stage", "@echarts-x/custom-segmented-doughnut",
    "@echarts-x/custom-bar-range", "@echarts-x/custom-line-range",
    "@echarts-x/custom-liquid-fill", "@echarts-x/custom-word-cloud",
]
BANNED = ["echarts-wordcloud", "echarts-liquidfill"]


def _get(url):
    req = urllib.request.Request(url, headers=UA)
    with urllib.request.urlopen(req, timeout=30, context=CTX) as r:
        return r.read().decode("utf-8")


def _npm(pkg):
    url = "https://registry.npmjs.org/" + pkg.replace("/", "%2F")
    return json.loads(_get(url))


def _npm_peer(pkg, version=None):
    data = _npm(pkg)
    ver = version or data["dist-tags"]["latest"]
    return ver, data["versions"][ver].get("peerDependencies", {})


def _diff_export_file(repo_tag, path, expected):
    """取 raw 文件，检查 expected 每个名字是否出现（大小写不敏感，只要求前导词边界——
    导出名形如 PictorialBarChart，名字与 Chart 之间无词边界）。"""
    url = f"https://raw.githubusercontent.com/apache/echarts/{repo_tag}/{path}"
    text = _get(url)
    found = {name for name in expected
             if re.search(r"\b" + re.escape(name), text, re.IGNORECASE)}
    return found, expected - found


def main(argv):
    as_json = "--json" in argv
    report = {"time": datetime.now(timezone.utc).isoformat(), "baseline": BASELINE}
    try:
        # 1. npm dist-tags
        ech = _npm("echarts")
        latest = ech["dist-tags"]["latest"]
        report["npm_latest"] = latest
        report["dist_tags"] = {k: v for k, v in ech["dist-tags"].items()}
        report["baseline_matches"] = (latest == BASELINE)

        # 2/3. 源码导出 diff（latest 与基线 6.1.0 都查）
        for tag, key in ((BASELINE, "baseline"), (latest, "latest")):
            series_found, series_missing = _diff_export_file(
                tag, "src/export/charts.ts", set(CORE_SERIES))
            comp_found, comp_missing = _diff_export_file(
                tag, "src/export/components.ts", set(CORE_COMPONENTS))
            report[key] = {
                "tag": tag,
                "series_missing": sorted(series_missing),
                "series_all": len(series_missing) == 0,
                "components_missing": sorted(comp_missing),
                "components_all": len(comp_missing) == 0,
            }
        # 新增系列（latest 的 charts.ts 里出现、基线清单里没有的系列名）
        latest_text = _get(
            f"https://raw.githubusercontent.com/apache/echarts/{latest}/src/export/charts.ts")
        exported = {m + "Chart" for m in
                    re.findall(r"export\s*\{\s*([A-Za-z0-9]+)Chart", latest_text)}
        expected_export = {s[0].upper() + s[1:] + "Chart" for s in CORE_SERIES}
        report["new_series_in_latest"] = sorted(exported - expected_export)

        # 4. @echarts-x peer 复核
        ext_report = {}
        for pkg in EXTENSIONS:
            ver, peer = _npm_peer(pkg)
            ext_report[pkg] = {"latest": ver, "peer_echarts": peer.get("echarts", "无声明"),
                               "compat_6": any("6" in str(v) for v in peer.values())}
        report["extensions"] = ext_report

        # 5. echarts-gl peer
        gl_ver, gl_peer = _npm_peer("echarts-gl")
        report["echarts_gl"] = {"latest": gl_ver, "peer": gl_peer.get("echarts", "无")}

        # 6. 禁用包复查（peer 是否仍不兼容 6.x）
        banned_report = {}
        for pkg in BANNED:
            ver, peer = _npm_peer(pkg)
            banned_report[pkg] = {"latest": ver, "peer": peer.get("echarts", "无"),
                                  "still_incompat": not any(
                                      "6" in str(v) for v in peer.values())}
        report["banned"] = banned_report

        changed = (
            report["baseline_matches"] is False
            or any(not report[t]["series_all"] or not report[t]["components_all"]
                   for t in ("baseline", "latest"))
            or any(not e["compat_6"] for e in ext_report.values())
            or any(not b["still_incompat"] for b in banned_report.values())
        )
        report["conclusion"] = (
            "需要更新能力目录" if changed else "基线仍有效，目录无需更新")
        report["exit"] = 1 if changed else 0
    except Exception as e:  # 网络/解析失败 → 快照态
        report["offline"] = True
        report["error"] = str(e)
        report["conclusion"] = "网络不可用：能力目录截至 6.1.0，未核验更新版本"
        report["exit"] = 2

    if as_json:
        print(json.dumps(report, ensure_ascii=False, indent=2))
    else:
        print(f"ECharts 基线核验报告（锁定 {BASELINE}）")
        print(f"核验时间: {report['time']}")
        if report.get("offline"):
            print(f"网络不可用: {report['error']}")
            print(report["conclusion"])
        else:
            print(f"npm latest: {report['npm_latest']}  "
                  f"({'与基线一致' if report['baseline_matches'] else '⚠️ 有更新'})")
            print(f"dist-tags: {report['dist_tags']}")
            for tag in ("baseline", "latest"):
                s = report[tag]
                print(f"[{tag}] 核心系列 23/{'23' if s['series_all'] else '23⚠️'} "
                      f"（缺失: {s['series_missing'] or '无'}） | "
                      f"组件 {len(CORE_COMPONENTS) - len(s['components_missing'])}/{len(CORE_COMPONENTS)} "
                      f"（缺失: {s['components_missing'] or '无'}）")
            if report["new_series_in_latest"]:
                print(f"⚠️ latest 出现基线外系列: {report['new_series_in_latest']}")
            print("扩展复核:")
            for pkg, e in report["extensions"].items():
                print(f"  {pkg}@{e['latest']} peer={e['peer_echarts']} "
                      f"{'✅' if e['compat_6'] else '❌ 不兼容'}")
            print(f"echarts-gl@{report['echarts_gl']['latest']} "
                  f"peer={report['echarts_gl']['peer']}")
            print("禁用包复查:")
            for pkg, b in report["banned"].items():
                print(f"  {pkg}@{b['latest']} peer={b['peer']} "
                      f"{'仍不兼容 6.x ✅ 维持禁用' if b['still_incompat'] else '⚠️ 已兼容，需复审'}")
            print(f"结论: {report['conclusion']}")
    return report["exit"]


if __name__ == "__main__":
    sys.exit(main(sys.argv))
