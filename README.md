<div align="center">

# echarts-viz-planner

**数据可视化方案规划师 · ECharts Visualization Planning Skill**

[![ECharts 6.1.0](https://img.shields.io/badge/ECharts-6.1.0-AA344D?style=flat-square&logo=apacheecharts&logoColor=white)](https://echarts.apache.org/)
[![Contract v1.0](https://img.shields.io/badge/contract-v1.0-3b82f6?style=flat-square)](schemas/plan.schema.json)
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
- 能力目录：**61 条**候选，按「族」全量召回，不凭经验直选柱状 / 折线 / 饼图
- 默认只出方案；用户明确要求生成时才产出 HTML / option 等产物

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
| 主输出 | Markdown 方案 | JSON（唯一权威），contract `1.0` |
| 澄清提问 | 最多 1 个阻断性问题 | **禁止提问**，降级为 `assumptions` + `open_questions` |
| option | 默认给规格要点 | 给**可直接运行**的 option |
| 篇幅 | 无硬限 | JSON ≤ 6KB |

> `api` 模式为什么禁止提问：被间接调用时通常没有可应答的人，提问会让上游流程卡死。

### 目录结构

| 路径 | 说明 |
|---|---|
| [SKILL.md](SKILL.md) | Skill 主文件（核心原则、工作流、选型机制、输出契约） |
| [catalog/index.md](catalog/index.md) | 能力目录常驻索引（61 条候选） |
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
- Capability catalog: **61** candidates, recalled per family — never short-circuit to bar / line / pie
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
| Main output | Markdown plan | JSON (single source of truth), contract `1.0` |
| Clarification | ≤ 1 blocking question | **never asks**; falls back to `assumptions` + `open_questions` |
| option | Spec highlights by default | **runnable** option |
| Size | No hard limit | JSON ≤ 6KB |

> Why `api` mode never asks: when called indirectly there is usually nobody to answer, so a question would deadlock the upstream flow.

### Project structure

| Path | Description |
|---|---|
| [SKILL.md](SKILL.md) | Skill entry (principles, workflow, selection mechanism, output contracts) |
| [catalog/index.md](catalog/index.md) | Capability catalog index (61 candidates) |
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
