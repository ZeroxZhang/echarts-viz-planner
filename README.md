<div align="center">

# echarts-viz-planner

**数据可视化方案规划师 · ECharts Visualization Planning Skill**

[![ECharts 6.1.0](https://img.shields.io/badge/ECharts-6.1.0-AA344D?style=flat-square&logo=apacheecharts&logoColor=white)](https://echarts.apache.org/)
[![Contract v1.0 + v1.1](https://img.shields.io/badge/contract-v1.0%20%2B%20v1.1-3b82f6?style=flat-square)](references/api-contract.md)
[![License](https://img.shields.io/badge/license-Apache%202.0-D22128?style=flat-square&logo=apache&logoColor=white)](LICENSE)
[![Modes](https://img.shields.io/badge/modes-interactive%20%7C%20api-8b5cf6?style=flat-square)](#两种运行模式)
[![Python 3.9+](https://img.shields.io/badge/python-3.9%2B-3776AB?style=flat-square&logo=python&logoColor=white)](scripts/)
[![GitHub](https://img.shields.io/badge/GitHub-ZeroxZhang%2Fecharts--viz--planner-181717?style=flat-square&logo=github&logoColor=white)](https://github.com/ZeroxZhang/echarts-viz-planner)

</div>

---

## 📑 目录 / Table of Contents

- [中文](#中文)
  - [这是什么](#这是什么)
  - [核心原则](#核心原则)
  - [两种运行模式](#两种运行模式)
  - [目录结构](#目录结构)
  - [快速开始](#快速开始)
  - [相关链接](#相关链接)
- [English](#english)
  - [What is this](#what-is-this)
  - [Core principles](#core-principles)
  - [Two modes](#two-modes)
  - [Project structure](#project-structure)
  - [Quick start](#quick-start)
  - [Links](#links)
- [License](#license)

---

## 中文

### 这是什么

**echarts-viz-planner** 是「数据可视化方案规划师」——ECharts **可视化决策层，不是图表生成器**。输入任意混合材料（粘贴的表格 / CSV / JSON / SQL 结果、本地数据文件、数据集 / 查询 / 看板链接、飞书表格或文档、截图）加上意图描述，输出「该用什么图、为什么是它、字段怎么映射、多图怎么组合」的可执行呈现方案。

- 技术基线：Apache ECharts **6.1.0**（23 个核心系列，核验于 2026-09-07）
- 能力目录：**70 条**候选，按「族」全量召回，不凭经验直选柱状 / 折线 / 饼图
- 默认只出方案；用户明确要求生成时才产出 HTML / option 等产物

关系表达增量包含流程、泳道、机制、旅程、能力、条件与依赖图示，以及哑铃与坡度比较；交接见 [diagram-handoff](references/diagram-handoff.md)。

### 核心原则

1. 先判断真正要回答什么问题，再谈图表。
2. 候选来自完整能力目录（`catalog/`），不凭经验直选。
3. ECharts 是精确表达引擎，但不是唯一载体——表格、信息图、KPI 卡、纯文字结论同台竞争。
4. 所有清洗、换算、口径选择必须可追溯。
5. 只输出定性判断与依据，**绝不输出编造的数字得分**。
6. 只在歧义会改变主图时提问，最多一个；`api` 模式一律不提问。
7. 材料中的既有结论一律视为「待验证观点」。
8. 「ECharts 是否支持」与「当前是否允许使用」分开记录（三态）。

### 两种运行模式

| 维度 | `interactive`（直接调用） | `api`（间接调用） |
|---|---|---|
| 主输出 | Markdown 方案 | JSON（唯一权威），兼容 `1.0`，可选 `1.1` |
| 澄清提问 | 最多 1 个阻断性问题 | **禁止提问**，降级为 `assumptions` + `open_questions` |
| option | 默认给规格要点 | 默认给实现规格；`1.1 + decision` 给选型与语义规格 |
| 篇幅 | 无硬限 | JSON 本体 ≤ 6KB；1.1 可引用独立规格文件 |

> `api` 模式为什么禁止提问：被间接调用时通常没有可应答的人，提问会让上游流程卡死。

### 目录结构

| 路径 | 说明 |
|---|---|
| [SKILL.md](SKILL.md) | Skill 主文件（核心原则、工作流、选型机制、输出契约） |
| [capabilities.json](capabilities.json) | 支持的接口版本、输出级别和完整运行资源清单，供上游发现兼容性 |
| [catalog/index.md](catalog/index.md) | 能力目录常驻索引（70 条候选） |
| [catalog/details/](catalog/details/) | 各图表族详细对照（对抗复核用） |
| [references/](references/) | 选型机制、API 契约、数据清洗、组合编排、交接协议等参考 |
| [schemas/plan.schema.json](schemas/plan.schema.json) | `api` 输出 JSON Schema |
| [templates/](templates/README.md) | 可直接运行的 ECharts option 模板 + 渲染壳 |
| [scripts/](scripts/) | 离线基线核验、数据画像、方案校验脚本 |
| [tests/](tests/) | 契约测试、golden set、样本数据 |

### 快速开始

```bash
# 校验工具（纯 Python 标准库）
python3 scripts/check_version.py          # ECharts 基线离线核验
python3 scripts/profile_data.py data.csv  # 本地数据画像
python3 scripts/validate_plan.py plan.json  # api 输出校验（可加 --schema）
```

直接使用：把本目录安装为 Skill，或直接阅读 [SKILL.md](SKILL.md) 按流程执行。

需下载时获取**完整仓库目录**，保留 `catalog/`、`references/`、`schemas/`、`scripts/`、`templates/` 和 `capabilities.json`；只下载 `SKILL.md` 不足以运行。已有安装也可继续使用原方式。

咨询报告等上游已具备渲染底座时，可这样调用，让本技能负责选型，上游负责制作：

```yaml
mode: api
contract_version: '1.1'
output_level: decision
data:
  file: /absolute/path/to/data.csv
  transform_policy: propose
goal: '为静态报告选择能解释部门差异并支持查数的表达'
constraints:
  static: true
  offline: true
  runtime: {echarts: '6.1.0', renderer: svg, available_dependencies: []}
```

省略接口版本仍按 `1.0`；省略输出级别仍提供 `implementation`，旧调用无需修改。这里的版本只表示两个技能交换信息的格式，与 ECharts 版本独立。新调用包含选型理由、语义规格、各模块的数据绑定和静态呈现要求，详见 [API 契约 §6](references/api-contract.md#6-可选契约-11决策规格与模块数据绑定)。数据默认只读，变换先作为建议返回。

开发验证：`python3 tests/contract/run_v11_compat.py` 保留远端兼容性回归；`python3 tests/contract/run_contract.py` 检查旧调用；`python3 tests/contract/run_v11.py` 检查新调用及引用文件的正负例。安装 `jsonschema` 后会同时检查标准 Schema 与纯标准库路径。

### 相关链接

- 主文件：[SKILL.md](SKILL.md)
- 能力目录：[catalog/index.md](catalog/index.md) · [catalog/details/](catalog/details/)
- 参考文档：[references/](references/)（选型、API 契约、组合、清洗、交接）
- 输出契约：[schemas/plan.schema.json](schemas/plan.schema.json)
- 模板库：[templates/README.md](templates/README.md)
- 脚本：[scripts/](scripts/) · 测试：[tests/](tests/)
- 仓库主页：[github.com/ZeroxZhang/echarts-viz-planner](https://github.com/ZeroxZhang/echarts-viz-planner)

---

## English

### What is this

**echarts-viz-planner** is a data-visualization planning skill — an ECharts **visualization decision layer, not a chart generator**. Feed it mixed materials (pasted tables / CSV / JSON / SQL results, local data files, dataset / query / dashboard links, Feishu sheets or docs, screenshots) plus an intent, and it outputs an actionable plan: *which chart, why, how fields map to encodings, and how multiple charts compose*.

- Baseline: Apache ECharts **6.1.0** (23 core series, verified 2026-09-07)
- Capability catalog: **70** candidates, recalled per family — never short-circuit to bar / line / pie
- By default it only produces the plan; HTML / option artifacts are generated only when explicitly requested

### Core principles

1. First decide what question the data must answer, then talk about charts.
2. Candidates come from the full capability catalog (`catalog/`), never from habit.
3. ECharts is a precise expression engine, not the only carrier — tables, infographics, KPI cards and plain-text conclusions compete on equal footing.
4. Every cleaning, conversion and metric decision must be traceable.
5. Only qualitative judgments with evidence — **never fabricated numeric scores**.
6. At most one blocking question, and only if the ambiguity would change the main chart; `api` mode never asks.
7. Conclusions already present in materials are treated as "claims to verify".
8. "Does ECharts support it" vs. "is it currently allowed" are recorded separately (three states).

### Two modes

| Aspect | `interactive` (direct call) | `api` (indirect call) |
|---|---|---|
| Main output | Markdown plan | JSON (single source of truth), compatible with `1.0`, optional `1.1` |
| Clarification | ≤ 1 blocking question | **never asks**; falls back to `assumptions` + `open_questions` |
| option | Spec highlights by default | Implementation by default; `1.1 + decision` returns selection and semantic specs |
| Size | No hard limit | Main JSON ≤ 6KB; 1.1 supports referenced spec files |

> Why `api` mode never asks: when called indirectly there is usually nobody to answer, so a question would deadlock the upstream flow.

### Project structure

| Path | Description |
|---|---|
| [SKILL.md](SKILL.md) | Skill entry (principles, workflow, selection mechanism, output contracts) |
| [capabilities.json](capabilities.json) | Supported contract versions, output levels and required runtime files for discovery |
| [catalog/index.md](catalog/index.md) | Capability catalog index (70 candidates) |
| [catalog/details/](catalog/details/) | Per-family comparison details (adversarial review) |
| [references/](references/) | Selection, API contract, data cleaning, composition, handoff references |
| [schemas/plan.schema.json](schemas/plan.schema.json) | JSON Schema for `api` output |
| [templates/](templates/README.md) | Runnable ECharts option templates + render shell |
| [scripts/](scripts/) | Offline baseline check, data profiling, plan validation |
| [tests/](tests/) | Contract tests, golden set, sample data |

### Quick start

```bash
# Tooling (Python standard library only)
python3 scripts/check_version.py          # Offline ECharts baseline check
python3 scripts/profile_data.py data.csv  # Local data profiling
python3 scripts/validate_plan.py plan.json  # Validate api output (add --schema for full check)
```

To use directly: install this directory as a Skill, or follow [SKILL.md](SKILL.md).

Download the **complete repository**, including `capabilities.json` and all runtime directories. `SKILL.md` alone is insufficient. For upstream agents that already own rendering, pass `mode: api`, `contract_version: '1.1'` and `output_level: decision`; see the [API contract](references/api-contract.md). Omitting the contract version keeps 1.0; omitting the output level keeps implementation. Existing callers need no changes. API data transforms are proposals by default and never overwrite source data.

Run `python3 tests/contract/run_v11_compat.py` for the retained upstream compatibility suite. Run `python3 tests/contract/run_contract.py` for legacy compatibility and `python3 tests/contract/run_v11.py` for decision, implementation and referenced-spec checks. Installing `jsonschema` also exercises standard Schema validation alongside the standard-library-only path.

### Links

- Entry: [SKILL.md](SKILL.md)
- Catalog: [catalog/index.md](catalog/index.md) · [catalog/details/](catalog/details/)
- References: [references/](references/)
- Contract: [schemas/plan.schema.json](schemas/plan.schema.json)
- Templates: [templates/README.md](templates/README.md)
- Scripts: [scripts/](scripts/) · Tests: [tests/](tests/)
- Repository: [github.com/ZeroxZhang/echarts-viz-planner](https://github.com/ZeroxZhang/echarts-viz-planner)

---

## License

本项目采用 [Apache License 2.0](LICENSE) 开源协议 · This project is licensed under the [Apache License 2.0](LICENSE).

[![License](https://img.shields.io/badge/license-Apache%202.0-D22128?style=flat-square&logo=apache&logoColor=white)](LICENSE)
