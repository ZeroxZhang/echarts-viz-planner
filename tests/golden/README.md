# Golden Set · 执行协议与验收（v3 方案 §18.1）

## 用途

20 例选型质量回归集。**只在以下时点执行**：能力目录变更后、SKILL.md 规则变更后、改基线版本前（§16.3：只有目录同步更新并跑通 golden set 才允许改基线）。

## 执行协议（Agent 手动执行，无 LLM 在环脚本）

1. 读 `golden_cases.json`，逐例以 `prompt` 为输入、以 `data.path` 为材料，按 SKILL.md 完整工作流选型。
2. 每例完成后，在 `results.json` 对应 `cases.<id>` 记录：
   - `actual_top1_capability` / `actual_top1_family`：主方案
   - `clarifications_asked`：实际提问次数（interactive 必须 ≤ 1）
   - `no_chart_recognized`：expect_no_chart=true 的用例，是否给出纯表格/文字方案
   - `status`：api 用例的实际 status
   - `evidence`：一句话依据或输出文件路径
3. 全部填完后运行 `python3 run_golden.py` 统计命中率。

## 门槛（不达标 = 回归失败，禁止改基线）

| 指标 | 门槛 |
|---|---|
| top-1 族命中率 | ≥ 80% |
| top-3 族命中率 | = 100% |
| 「不该画图」识别率 | = 100% |
| interactive 澄清提问率 | ≤ 30% |

## 覆盖清单（§18.1 要求 20 类，全部覆盖）

趋势 G01 · 排名 G02 · 构成 G03 · 构成随时间 G04 · 分布 G05 · 异常 G06 · 相关 G07 · 漏斗 G08 · 流向 G09 · 关系网络 G10 · 层级 G11 · 地理 G12 · 金融 G13 · 高基数明细 G14 · 多表冲突口径 G15 · 模糊意图 G16 · 指定了错误图表 G17 · 纯表格更优 G18 · 需要组合叙事 G19 · 数据不可访问 G20。

## 数据说明

- `real-data-tests/data/*`：真实公开数据（vega-datasets），用于 G01/G02/G03/G05/G06/G07/G11/G14/G16/G17/G18/G19。
- `tests/golden/data/*`：示意样本（`synthetic: true`，仅用于选型判定，不用于对外报告）。
- `tests/samples/q3_funnel.csv`：漏斗样本（G09）。

## 版本与结果

- 基线：ECharts 6.1.0（`scripts/check_version.py` 核验通过）。
- 首轮结果（2026-09-07）：20/20 全部执行，见 `results.json`；`python3 run_golden.py` 统计通过。
- 后续执行请把 `results.json` 中 `run_at` 与 `skill_version` 更新为当次值，并保留历史结果在 git 提交里。
