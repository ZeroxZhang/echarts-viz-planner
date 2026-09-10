---
name: echarts-viz-planner
description: |
  数据可视化方案规划师（ECharts 可视化决策层，不是图表生成器）。输入任意混合材料——粘贴的表格/CSV/JSON/SQL 结果、本地数据文件、数据集/查询/看板链接、飞书表格或文档、截图——加上意图描述，输出「该用什么图、为什么是它、字段怎么映射、多图怎么组合」的可执行呈现方案。
  支持两种模式：interactive（给人看的结论先行 Markdown 方案）与 api（给上游 Agent 的 JSON 契约；默认实现规格，可选轻量决策规格，全程零提问）。
  触发场景：用户提供数据但尚未确定怎么呈现；问「这些数据适合怎么展示」「用什么图好」「帮我做个可视化方案」「帮我选 ECharts 图表」「做组合图或仪表盘」「把这堆材料整理成可视化」；上游 Agent 已拿到数据、只需要选型与实现规格。
  即使用户只丢来一个 CSV、一段表格、一个数据文件或贴一段数据说「看看这个怎么展示」「这适合画什么图」，也应触发。
  不应触发：图表类型已明确、只要写实现代码（直接写 ECharts 代码即可）；单纯取数/写 SQL；海报插画等视觉创作；只点评已有图表且不重新选型。
---

# echarts-viz-planner · 数据可视化方案规划师

v0.1 · 技术基线 Apache ECharts **6.1.0**（核验于 2026-09-07）。

一句话：输入混合材料 + 意图 → 输出「该用什么图、为什么、字段怎么映射、多图怎么组合」的可执行方案。**本 Skill 是可视化决策层，不是图表生成器**——默认只出方案，用户明确要求生成时才产出 HTML/option 等产物（并移交产物 Skill 实现）。

## 1. 核心原则（硬约束）

1. 先判断真正要回答什么问题，再谈图表。
2. 候选来自完整能力目录（`catalog/`），不凭经验直选柱状/折线/饼图。
3. ECharts 是精确表达引擎，但不是唯一载体——表格、信息图、KPI 卡、纯文字结论同台竞争。
4. 所有清洗、换算、口径选择必须可追溯（原值 → 动作 → 原因 → 影响 → 可逆性）。
5. 输出定性判断与依据，**绝不输出编造的数字得分**（百分制得分不可复现、不可审计；`api` 模式尤其禁止）。
6. 只在歧义会改变主图时提问，最多一个；`api` 模式一律不提问。
7. 材料中的既有结论一律视为「待验证观点」，不直接当作结论输出。
8. 能力「ECharts 是否支持」与「当前是否允许使用」分开记录（三态：`supported_by_echarts` / `available_in_runtime` / `allowed_by_policy`）。策略禁用不等于能力不存在，要说明「支持但当前不用」并给替代。

## 2. 触发边界

| 应当触发 | 不应触发 |
|---|---|
| 粘贴的表格、CSV、JSON、SQL 结果 | 已明确知道画什么图、只要实现 → 直接写代码 |
| 本地数据文件、数据集/查询/看板链接 | 没有数据或没有呈现意图的普通问答 |
| 飞书电子表格/多维表格/文档内表格 | 单纯写 SQL、单纯取数 |
| 数据与业务说明、报告、纪要混在一起 | 海报、插画等视觉创作 |
| 「这些数据适合怎么展示」「用什么图好」 | 只点评已有图表且不重新选型 |
| 上游 Agent 已拿到数据，要选型与实现规格 | 输出与可视化无关的通用回答 |

## 3. 技术基线（已核验事实，不要现场猜测）

- 稳定版 **6.1.0**；核心系列 **23 个**；ECharts 6 新增 `MatrixComponent`、`ThumbnailComponent`（大数据量导航关键组件）。
- 官方自定义系列 **8 个**（npm scope `@echarts-x/`，peer 均 `echarts@^6.0.0`）→ **允许**，输出中必须声明依赖（精确版本见 `catalog/details/extensions.yaml`）。
- `echarts-gl@2.1.0`（peer `^5.1.2 || ^6.0.0`）→ **默认禁用**：3D 普遍降低读数精度；上游明确要求才启用。
- `echarts-wordcloud` / `echarts-liquidfill` peer 仅 `^5.0.1`，不兼容 6.x → **禁用**，改用 `@echarts-x/custom-word-cloud` / `custom-liquid-fill`。
- 其他社区插件不进候选池。
- 输出一律用精确版本号，不用 `latest`；**运行时不查 npm latest**（联网依赖 + 预发布风险）；离线时标注「能力目录截至 6.1.0」。

## 4. 运行模式判定（第一件事，判定结果必须回显在输出中）

**显式优先**：调用方传入 `mode: api`、明确要「只返回 JSON / spec / option」→ `api`。

**无显式声明时，命中任一即判 `api`**：请求来自子任务描述而非对话且没有可回话的人；请求已附带结构化数据与明确目标、只索要实现规格；请求指定返回格式为 JSON / YAML / option。其余默认 `interactive`。

| 维度 | `interactive`（直接调用） | `api`（间接调用） |
|---|---|---|
| 主输出 | Markdown 方案（§12.1） | JSON（§12.2），唯一权威 |
| 附带摘要 | — | Markdown ≤ 200 字，只讲主方案 + 一句理由 |
| 澄清提问 | 最多 1 个阻断性问题（§7） | **禁止提问**，降级为 `assumptions` + `open_questions` |
| 数据回传 | 可内联少量关键数据 | 不回传数据本体，只回 `data.ref` + `data.binding` |
| option | 默认给规格要点，明确要求才给完整 option | 缺省 `implementation`；`1.1` + `output_level: decision` 返回语义规格，不要求 option |
| 取数 | 主动移交取数 Skill（§11） | 不移交；缺数据时 `status: insufficient_data` + `missing` |
| 产物路由 | 主动建议移交产物 Skill | 不路由；按上游 `target_carrier` 给 `carrier_adaptation` |
| 组合叙事 | 完整故事板 | 由读者任务与可用空间决定，尊重上游 `max_components`，不为凑数增减模块 |
| 篇幅 | 无硬限 | JSON ≤ 6KB，超限裁剪 `rejected` 与 `audit` 明细 |
| 失败处理 | 对话式说明缺什么 | `status` 枚举 + `missing` 清单，**仍返回合法 JSON** |
| 选型审计 | 按需解释 | `audit` 只给计数，不给逐条理由 |

**为什么 `api` 模式禁止提问**：被间接调用时通常没有可应答的人，提问会让上游流程卡死或触发无意义重试。因此原本会触发澄清的歧义必须取默认值继续，并把歧义完整暴露给上游（`open_questions[].blocking` 恒为 `false`），由上游决定是否回头问人。

**契约稳定性**：`contract_version` 语义化管理（兼容 `1.0`，显式选用 `1.1` 才启用新契约）；同一输入必须得到同一 `capability_id`（幂等）；字段只增不删；枚举取封闭列表；任何路径都返回结构合法 JSON。

## 5. 工作流

1. 模式判定（§4）→ 2. 材料盘点与访问状态确认 → 3. 分层提取（数据事实 / 指标口径 / 已有观点 / 目标 / 展示约束）→ 4. 数据画像 + 安全清洗 + 跨材料冲突检测 → 5. 意图识别（四层：显式目标 → 数据可回答的问题 → 隐含业务目标 → 使用场景）→ 6. 歧义处理（interactive 单选项提问 / api 取默认值写假设）→ 7. 分析任务分类 → 按族召回候选 → 硬淘汰 → 对抗复核 → 定性判定（§6）→ 8. 单图 / 组合 / 非图表方案共同竞争，编排叙事（§8）→ 9. 输出（interactive Markdown / api JSON）。

## 6. 选型机制（五步，核心）

```
Step 1  分析任务分类（可枚举、可判定）：趋势 / 比较排名 / 构成 / 分布 / 相关
        / 流向 / 层级 / 关系网络 / 地理 / 达成度 / 明细查数 / 机制流程。
        一个需求可命中多个任务，按重要性排序。
Step 2  查 catalog/index.md，取命中任务所属族的全部候选。
        族内即全量——保证冷门图不被跳过。
Step 3  硬淘汰，逐条留理由。
Step 4  对抗复核：对至多 3 个真正可行候选读 catalog/details/<族>.yaml，两两对照
        （必测对见 references/selection.md）。
Step 5  定性判定：匹配度（强/中/弱）+ 置信度（高/中/低），
        必须写明「次选在什么条件下会反超」。
```

**硬淘汰条件**：缺必要字段；字段类型不符；无法回答目标问题；语义不成立（比例不构成整体 / 流向有环 / 层级不成立）；基数或数据量超限；依赖不可用；策略或上游约束禁用；地图数据无法匹配；视觉编码会造成明显误导；调用方明确禁止。

**为什么不打分**：数字得分不可复现、不可审计、无校准依据，本质是编造——`api` 模式下上游若拿到分数会误当作可比较的置信度做二次决策。一律用定性等级 + 判定依据。

**允许不画图**：明细查数、样本量 < 5、单值对比等场景，表格或一句话结论就是最优解。纯表格与纯文字方案必须参与最终竞争（`capability_id: table.detail` 或 `text.conclusion`），不强行返回图表。

## 7. 澄清机制（仅 interactive）

> **最多一个阻断性问题；其余歧义取默认值并显式披露假设。** 不问：颜色、标题、美化偏好；材料中已能推断的信息；不影响主推荐的歧义。

阻断性判定——不同答案会导致主图完全不同，实践中只有两类：① 用途是「探索/诊断」还是「汇报/传播」；② 存在两套冲突口径且都可能成立。

格式：选项式、标出推荐项、含「其他」、允许回字母。

> 这批数据主要用于哪种场景？
> A. 业务复盘，解释结果与原因（推荐）　B. 管理层汇报，突出结论
> C. 探索分析，先看有没有问题　D. 其他（请补充）

`api` 模式跳过本章：取保守默认（保留原值、不删不补），写进 `assumptions` / `open_questions`。

## 8. 组合叙事

**叙事骨架**：结论 → 发生了什么 → 谁贡献最大 → 为什么 → 证据明细 → 下一步。
**模块类型**：结论句、KPI 卡（≤ 5）、ECharts 图、信息图、数据表格、原始证据、注释。
**分工**：模式识别用图表；精确查数用表格；流程与机制用信息图；三者不互相替代、不重复表达同一信息。
**约束**：按读者任务、证据关系和正文空间确定模块；一个模块回答一个明确问题，单图讲得清就不组合。尊重上游 `max_components` 上限；没有上限时不设固定模块数量，说明必要的主辅关系与阅读顺序。
常用范式见 `references/composition.md`。

## 9. 视觉质量红线（细则见 references/visual-quality.md）

- 连续量用单色相渐变；分类色板通常不超过 8 色，更多类目优先使用位置、分面、直接标签或表格；合并“其他”属于数据变换，须有语义依据和上游接受；强调色只用一个；禁止彩虹色映射连续值。
- 坐标轴标签超 6 字改横向条形或旋转 ≤ 30°；数值标签仅在类目 ≤ 12 时全量显示，否则只标首尾与极值。
- 去掉竖向网格线与图表边框；Y 轴从 0 起，折线可例外但必须标注截断。
- 飞书文档载体：宽 100%、高 360–420px；交互网页可按空间调整图例；静态交付核心信息必须直接可见。
- 禁用：3D 饼图；双 Y 轴不同量纲且不标注；面积图叠加超 4 层；无意义动画；玫瑰图表达非周期数据。
- `api` 模式：implementation 将规范落实进 option；decision 给出与载体相符的表达约束，由上游实现。主题遵循上游 `theme`，缺省 `light`。

## 10. 数据处理要点（细则见 references/api-contract.md §数据）

**上游数据所有权**：api 调用默认 `data.transform_policy: propose`。下列清洗档位用于判断和提出 `transforms`，不直接修改上游数据；仅明确传入 `apply` 时可生成派生版本，原始材料仍只读。避免重复清洗已核定数据，发现单位、分母或证据冲突返回上游。

- **清洗三档**：自动执行（删空白行列、字段名去空格、识别合计行、标准化日期/数字/百分比/货币、统一空值、标记重复、时间排序）；执行但必须记录（类名归一、单位换算、宽转长、多表关联、聚合抽样、派生指标）；必须询问或保留原值（删异常值、填补缺失、冲突口径二选一、显著改变结论的裁剪）。
- **冲突检测**：同名指标口径不同、同区间数据不一致、多份文件都自称最新、Join 关系不明、`0` 语义不明 → 不得自行选择，标记并按影响决定是否提问。
- **访问异常强制动作**：无权限 → 告知并请对方导出或授权，**不根据标题猜测内容**；超时 → 重试一次仍失败标 `unavailable` 并列出受影响分析点；超阈值（> 5 万行或类目 > 200）→ 提出有依据的聚合、抽样或拆页方案；交互场景可用 `dataZoom` + `thumbnail`，静态输出保留必要细节与覆盖范围；截图/OCR → 标来源与置信度，关键数字请对方复核。
- **溯源**：每项处理记录「原值 → 动作 → 原因 → 影响行数 → 是否可逆 → 是否经确认」；图、表、正文引用同一份清洗后数据版本；`api` 模式清洗动作表达为可复现的 `transforms` 算子序列。

## 11. 路由与移交（只做决策，不穿透调用其他 Skill 的工具）

移交一律用「使用 X Skill 完成 Y」的声明式表达。交接信息包（capability_id + 当前 output_level 的规格 + 数据注入说明 + 依赖清单 + verify_hints）与载体适配要点见 `references/handoff.md`——**兼容优先，不绑定任何载体的接口**；已有渲染底座优先复用；没有底座的网页实现可用 `templates/render-shell.html` 参考。环境内实际存在的 Skill 名：

| 环节 | 场景 | 移交对象（interactive） | api 模式 |
|---|---|---|---|
| 取数 | 风神/Aeolus 数据集或查询链接 | `bytedance-aeolus` | 不移交，写入 `missing` |
| 取数 | Hive 表名、指标口径 | `bytedance-hive` | 同上 |
| 取数 | 飞书电子表格 / 多维表格 | `lark-sheets` / `lark-base` | 同上 |
| 取数 | 飞书文档内表格 | `lark-doc` | 同上 |
| 取数 | 本地 CSV / Excel / JSON | 本 Skill `scripts/profile_data.py` | 直接处理 |
| 产物 | 独立网页 / Dashboard | `huashu-design`（HTML 原型）或 `lark-apps`（可分享部署） | 给 `carrier_adaptation.web` |
| 产物 | 图放进飞书文档 | `lark-doc`（如环境有 htmlbox 类 Skill 则优先） | 给 `carrier_adaptation.lark_doc` |
| 产物 | 只要一段 option | 本 Skill 直接输出 | 直接输出 |

`api` 模式一律不发起移交——上游已掌握全局，由它决定下一跳，避免调用链层层嵌套失控。

## 12. 输出契约

### 12.1 interactive 模板（结论先行，固定结构）

```
## 结论：建议怎么画
主方案 + 一句话理由 + 匹配度（强/中/弱）+ 置信度（高/中/低）

## 判断依据
真实目标 / 使用场景 / 关键分析问题 / 依据来源

## 呈现方案
叙事顺序 → 各模块（类型 / 回答的问题 / 字段映射 / 关键配置）

## 备选与淘汰
次选 + 何种条件下反超；关键淘汰候选 + 一句话理由

## 数据处理与风险
自动清洗记录 / 待确认口径 / 抽样与限制 / 【待补充：xxx】
```

### 12.2 api 最小输出字段速查（完整契约见 references/api-contract.md）

下例为兼容 `1.0` 的默认 implementation。上游要自行设计制作时，显式传 `contract_version: "1.1", output_level: "decision"`。1.1 的每个模块必须给 `rationale` 及 `spec` 或可读 JSON `spec_ref: {path}`；ECharts、表格和 KPI 还需模块级 `bindings`（target/ref/expects/required_fields）。规格表达图表映射、表格行列、文本证据、信息图结构与关系含义，不限定图示形态或节点数；详见完整契约 §6。`capabilities.json` 供调用方动态发现兼容性。只加载 SKILL.md 不等于完成调用：api 必须继续读完整契约，实际选型必须读 catalog/index.md。

可传 `context`（reader_task/findings/evidence_refs/boundaries）与 `constraints`（static/offline/size/runtime/theme）。保留上游主题、字体及既有渲染底座；静态核心信息不能依赖 tooltip/悬停/缩放，离线不能依赖外网 CDN。

```json
{
  "contract_version": "1.0",
  "mode": "api",
  "status": "ok | ok_with_assumptions | insufficient_data | unsupported | policy_blocked",
  "summary": "建议 X + 理由（一句话）",
  "echarts": { "version": "6.1.0", "deps": [], "renderer": "canvas" },
  "intent": { "goal": "", "scenario": "review|executive|exploration|broadcast|monitoring", "inferred": false, "confidence": "high|medium|low" },
  "data": {
    "ref": { "type": "inline|file|lark_sheet|bitable|aeolus|hive", "id": "" },
    "profile": { "rows": 0, "dimensions": [], "measures": [], "time_field": null, "cardinality": {} },
    "binding": { "mode": "dataset.source", "expects": "array<object>", "required_fields": [] }
  },
  "plan": [
    { "role": "primary|support", "capability_id": "sankey.sankey", "question": "",
      "match": "strong|medium|weak",
      "encode": {}, "transforms": [], "option": { "series": [ { "type": "sankey" } ] },
      "carrier_adaptation": { "lark_doc": { "width": "100%", "height": 400 }, "web": { "responsive": true } } }
  ],
  "alternatives": [ { "capability_id": "", "when_better": "" } ],
  "rejected": [ { "capability_id": "", "reason": "" } ],
  "assumptions": [ { "item": "", "impact": "high|medium|low", "reversible": true } ],
  "open_questions": [ { "q": "", "default_used": "", "impact": "", "blocking": false } ],
  "risks": [], "verify_hints": [],
  "audit": { "candidates": 0, "rejected": 0, "reviewed_pairs": 0 }
}
```

**status 语义**：`ok` 表示当前输出级别的选型规格可供上游继续制作，不代表渲染、静态可读或交付 QA 通过；`ok_with_assumptions` 继续制作时披露 assumptions；`insufficient_data` 必须附 `missing: [{what, why_needed, how_to_get}]` 且仍是合法 JSON（此时 `plan` 可为空数组）；`unsupported` 超出可视化决策范围（`plan` 可为空）；`policy_blocked` 唯一合适方案被约束禁用（最优解进 `rejected` 且理由 `policy_blocked`，`plan` 给原生替代）。

**上游调用方式**：声明「使用 echarts-viz-planner skill，为这批数据给出可视化方案与 option」，传入 `mode / data（inline|file|ref 三者择一）/ goal / questions / scenario / target_carrier / constraints（allow_extensions / allow_3d / max_components / size）/ theme / composition`。`goal` 缺失时从数据画像推断并写入 `assumptions`，不阻塞。

## 13. 硬性红线

- 不出现未核实的数字、得分、行业基准；缺来源一律 `【待补充：xxx】`。
- 每个淘汰候选都能给出一句话理由；`api` 模式 `audit` 保留计数（候选数/淘汰数/复核对数）。
- 依赖包名与版本与 §3 核验结果一致。
- `api` 模式全程零提问、任何路径返回合法 JSON、≤ 6KB、不回传数据本体。
- 指定图表不合适时：**先执行要求，同时指出风险与更优解**，不擅自替换（api 模式写入 `risks`）。
- 输出前跑 `scripts/validate_plan.py`（`api` 模式必须通过 `--schema`）。

## 14. 脚本与版本

- `scripts/profile_data.py <文件>`：本地 CSV/JSON/JSONL 数据画像（字段类型、基数、缺失率、数值范围、时间字段检测），stdout 输出 JSON 画像。
- `scripts/validate_plan.py <plan.json> [--schema]`：校验 `api` 输出——结构合法性（内置校验器，jsonschema 可用时自动升级）、`capability_id` 是否存在于 `catalog/index.md`、option 的 series 与依赖是否匹配、encode 字段是否在数据画像内、status 与 assumptions 一致性、零提问、无伪得分、JSON 本体 ≤ 6KB；1.1 引用规格可更大但必须可读且通过同等语义验证。`--builtin-only` 验证纯标准库路径。零参数跑自检。
- `scripts/check_version.py`：定期离线核验基线——比对 npm latest、diff `charts.ts`/`components.ts`、复查 `@echarts-x/*` 与 `echarts-gl` 的 peer 范围（exit 0 = 基线有效，无需更新目录）。
- `templates/`：option 模板库（29 个模板 + 索引与占位符约定见 `templates/README.md`）；api implementation 给待数据注入与适配的 option 时**以模板起底、替换占位符**。`templates/render-shell.html` 是载体无关的渲染外壳。
- 回归（无 LLM 在环）：`tests/contract/run_contract.py`（兼容 api 契约 6 用例），`tests/contract/run_v11.py`（1.1 语义与引用正负例）、`tests/golden/run_golden.py`（选型质量 20 例，协议见 `tests/golden/README.md`）。
- 版本机制：目录锁定 6.1.0（`catalog/index.md` 头部 `verified_at`）；**只有能力目录同步更新并跑通 golden set 才允许改基线版本**（只改版本号不重验目录没有意义）；运行时不查 npm latest（联网依赖 + 预发布风险）；`contract_version` 与 ECharts 版本解耦。

## 15. 文件地图（何时读什么）

| 文件 | 何时读 |
|---|---|
| `catalog/index.md` | **每次选型必读**。Step 2 族内全量召回的依据 |
| `catalog/details/<族>.yaml` | Step 4 对至多 3 个可行候选做对抗复核时读对应族（共 9 族：comparison/trend/distribution/flow/correlation/hierarchy/composition/geo/kpi） |
| `catalog/details/extensions.yaml` | 任何 `ext.*` / `gl.*` 候选进入复核时**必读**（三态分离 + 精确版本） |
| `references/api-contract.md` | `api` 模式输出完整契约、上游输入模板、transforms 算子语法 |
| `references/selection.md` | 任务→族路由表、10 组必测对抗复核对、淘汰规则细节 |
| `references/business-expression-boundaries.md` | 候选涉及 Mekko、指数/敏感性/小倍数、预测/经济曲线、业务评分、责任或计划时，按对应表达核对数据前提与误用边界 |
| `references/composition.md` | 需要多图组合 / 看板 / 汇报叙事时 |
| `references/visual-quality.md` | 给完整 option 或固化视觉规范时 |
| `references/data-cleaning.md` | 涉及清洗三档、冲突检测、访问异常、溯源台账时 |
| `references/antipatterns.md` | 输出前自检（视觉/选型/流程三类反模式） |
| `references/handoff.md` | 移交产物 Skill 前（信息包五件、载体适配、降级链） |
| `templates/` | api 模式给 option 时（`templates/README.md` 选模板 + 替换占位符；`render-shell.html` 做网页渲染） |
| `schemas/plan.schema.json` | 校验器自动引用；手工核对契约时读 |

说明：`special` 族（table.detail / table.pivot / text.conclusion / infographic / custom.custom）无 details 文件——非图表载体同样比较任务匹配与表达边界，不需要读取不存在的 details 文件；`relation` 族单条目 `graph.force` 的详情在 `catalog/details/hierarchy.yaml` 末尾。
