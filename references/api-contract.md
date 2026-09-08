# api 模式完整契约

> `api` 模式 = 被其他 Agent / Skill 间接调用。本文档是唯一权威的完整契约；
> SKILL.md §12.2 的最小速查用于第一层兜底。上游未必加载本文件，核心字段必须与 SKILL.md 一致。

## 1. 输入契约（上游怎么调）

以下为兼容 1.0 的调用模板；模块化上游选择 1.1 + decision 时见 §6。上游声明使用本 skill 并传入：

```yaml
mode: api                      # 可选；缺省按 SKILL.md §4 判定
data:                          # 三者择一，必填
  inline: []                   # 小数据直接给（数组）
  file: "data/q3_funnel.csv"   # 本地文件路径
  ref: { type: aeolus | lark_sheet | bitable | hive | lark_doc, id: "", note: "" }
goal: "解释 Q3 转化下降来自哪些渠道"      # 建议必填
questions: []                  # 或直接给要回答的原子问题
scenario: review | executive | exploration | broadcast | monitoring
target_carrier: lark_doc | web | none
constraints:
  allow_extensions: false      # false 时扩展类候选一律 policy_blocked
  allow_3d: false
  max_components: 2
  size: { width: "100%", height: 380 }
theme: light | dark
composition: false             # true 时才输出多模块故事板
```

**缺项处理**：
- `goal` 缺失 → 从数据画像推断并写入 `assumptions`（`inferred: true`），不阻塞。
- `data.ref` 指向的资源本 Skill 无法访问 → 不自行取数，`status: insufficient_data` + `missing` 说明「需上游用哪个 Skill 取到什么形态的数据」。
- 无 `theme` → `light`；无 `scenario` → 从 goal 推断，`confidence` 相应降级。

## 2. 输出契约（唯一权威 JSON）

结构见 `schemas/plan.schema.json`，兼容示例见 SKILL.md §12.2，1.1 增量契约见本文 §6。要点：

### 2.1 status 枚举（封闭）

| 值 | 含义 | 上游应做什么 |
|---|---|---|
| `ok` | 方案完整可用 | 按 output_level 继续制作与验证 |
| `ok_with_assumptions` | 可用，但含影响结论的假设 | 继续制作并披露 `assumptions` |
| `insufficient_data` | 无法选型 | 按 `missing` 补数据后重试（此时 `plan` 可为空数组） |
| `unsupported` | 需求超出可视化决策范围 | 改走其他能力（`plan` 可为空数组） |
| `policy_blocked` | 唯一合适方案被约束禁用 | 放宽 `constraints` 或采用 `alternatives` |

`insufficient_data` 时必须给：

```json
"missing": [
  { "what": "阶段字段", "why_needed": "漏斗/流向类图的必要维度",
    "how_to_get": "使用 bytedance-aeolus 从原查询补出 stage 列" }
]
```

### 2.2 transforms 算子语法（可复现的清洗表达）

清洗动作必须表达为算子序列，不用自然语言。常见算子：

```json
{ "op": "filter", "where": "channel != '汇总'" }
{ "op": "aggregate", "by": ["channel", "stage"], "agg": "sum(users)" }
{ "op": "sort", "by": "date", "order": "asc" }
{ "op": "normalize", "field": "users", "method": "divide_by" }
{ "op": "derive", "field": "loss_rate", "expr": "1 - users/prev_users" }
{ "op": "sample", "method": "random", "n": 5000, "seed": 42 }
{ "op": "unnest", "field": "tags" }
{ "op": "convert", "field": "date", "to": "datetime" }
```

### 2.3 option 约定（implementation；decision 见 §6）

- **以 `templates/` 起底**：按 `capability_id` 选模板（映射表见 `templates/README.md`），逐项替换占位符，
  输出前确认无 `__X__` 残留；无独立模板的变体按 README「变体起底」表组合。
- 数据用 `dataset` 占位：`"option": { "dataset": { "source": "<由上游注入 data.binding 指定数据>" }, ... }`；
  树/图/桑基/漏斗/日历等系列数据形态按模板内 `__*_DATA__` 占位符说明注入。
- series 类型必须与 `capability_id` 的 runtime 一致；扩展候选的 `echarts.deps` 必须含对应包名+版本。
- 视觉质量规范（references/visual-quality.md）已固化进模板（aria/网格/标签/单色相渐变），替换时不要回退。
- 主题遵循上游 `theme`，缺省 `light`。
- 网页载体可给 `templates/render-shell.html` 外壳（option 替换 `__OPTION__`）；交接细节见 `references/handoff.md`。

## 3. 契约稳定性

- `contract_version` 语义化管理（兼容 `1.0`，新增可选 `1.1`）：破坏性变更升主版本。
- **幂等**：同一输入必须得到同一 `capability_id` 与 `encode`，不允许结果漂移。
- 字段**只增不删**；上游可忽略未知字段。
- 所有枚举取封闭列表，不返回自由文本枚举值。
- 任何情况（包括失败）都返回结构合法的 JSON，不抛裸文本报错。
- JSON ≤ 6KB；超限先裁剪 `rejected` 明细，再裁剪 `audit`，最后裁剪 `alternatives`；1.1 详细规格可引用真实 JSON 文件，核心字段（status/plan/assumptions/missing）不可裁。

## 4. 数据回传禁令

- 不回传数据本体。`data.profile` 只回画像（规模/维度/指标/时间字段/基数），不回行级数据。
- 需要精确读数时用 `plan[].role: support` 指向 `table.detail`，由上游渲染数据表。
- `data.binding` 描述上游注入数据的形态（`mode: dataset.source`，`expects: array<object>`，`required_fields`），不携带数值。

## 5. 审计与幂等自检清单（输出前逐项过）

- [ ] `mode: api` 已回显；全程零提问；`open_questions[].blocking` 恒 false
- [ ] 所有 `capability_id` 存在于 `catalog/index.md`，且 series 类型匹配
- [ ] 每个 `rejected` 条目有一句话理由；扩展被禁时理由为 `policy_blocked` 且给原生替代
- [ ] `ok_with_assumptions` 时 `assumptions` 非空；`insufficient_data` 时 `missing` 非空
- [ ] `audit` 计数与实际一致（候选数/淘汰数/复核对数）
- [ ] 通过 `scripts/validate_plan.py <plan.json> --schema`
- [ ] 无编造数字得分；无未核实来源（缺来源写 `【待补充：xxx】`）

## 6. 可选契约 1.1：决策规格与模块数据绑定

只有显式传入 `contract_version: "1.1"` 才启用本节；省略版本仍使用 1.0。`output_level` 缺省为 `implementation`，`decision` 只在 1.1 中有效。1.0 字段和默认输出保持兼容。

### 输入与数据所有权

```yaml
mode: api
contract_version: '1.1'
output_level: decision
context:
  reader_task: '读者需要看清的关系或作出的判断'
  findings: []                   # 已核验发现及证据定位，不强迫接受原结论
  evidence_refs: []              # 文件、页码、单元格或片段定位
  boundaries: []                 # 口径、反证、因果解释与不可推断范围
data:
  file: /absolute/path/to/materials.json  # 或 inline/ref；允许混合文本材料
  transform_policy: propose      # 缺省 propose；apply 也仅生成派生版本
goal: '当前视觉问题'
scenario: executive
target_carrier: web
constraints:
  static: true
  offline: true
  size: {width: 1100, height: 550} # 正文实际空间，单位由调用方说明
  runtime: {echarts: '6.1.0', renderer: svg, available_dependencies: []}
  theme: {ref: '/absolute/path/to/theme.css'}
```

`context`、`constraints` 与 `data.transform_policy` 在输出回显已收到的约束。顶层旧 `theme` 仍可用；与 `constraints.theme` 冲突时以上游明确优先级为准，未给时披露假设。`runtime` 是上游能力描述，不能将目录支持等同于已经安装。1.1 校验器从 catalog/index.md 的状态列读取精确依赖包和版本；若提供 runtime.available_dependencies，还检查实际可用清单。allow_extensions=false 禁用所有扩展；3D 需显式 allow_3d=true。引用原始资料不足以确认事实时返回疑点或 `insufficient_data`。

默认只提出 `transforms`，不二次清洗已核定数据，不写回原文或原数据，不为图形效果删除异常、换分母或合并其他。只有上游明确 `apply` 才执行可复现变换，记录派生版本；原始材料仍只读。这个数据所有权规则也适用于 api 1.0 调用；已存在的 transforms 字段仍保留，但缺省表示建议。

### 每个模块的语义规格

1.1 的 `plan[]` 在原有 role/capability_id/question/match 外增加非空 `rationale`，并在 `spec` 与 `spec_ref` 中恰选一个。所有 spec 都有：

- `kind`: `echarts | table | text | infographic | kpi`，与 capability_id 对应。
- `message`: 该模块要呈现的发现或读者可完成的判断。
- `evidence_refs`: 证据位置字符串数组；来源不足时不得用空数组掩盖问题，应同时披露缺口。
- `boundaries`: 口径与推断边界字符串数组，没有额外边界可为空。

各 kind 的额外最小字段如下。这是信息要求，不是版式或固定图示模板。

| kind | 最小语义字段 |
|---|---|
| echarts | `mapping` 非空对象，视觉角色映射到字段名或字段数组；`comparison_basis` 说明比较对象、单位、分母或无量化比较的含义 |
| table | `columns: [{field,label}]` 非空；`row_organization` 说明排序、分组与粒度；`lookup_task` 说明精确查数任务。pivot 另说明行列维度和汇总口径 |
| text | `text` 是实际结论文字，证据与推断边界放共同字段 |
| infographic | `structure` 非空开放对象，内容足以制作；`relationship_semantics` 说明箭头、并列、包含或其他关系含义；`reading_order` 非空字符串数组。不固定节点/边模型、节点数量或层次形式，不把推测关系画成已证实因果 |
| kpi | `metric` 指标字段；`comparison_basis` 比较基准；`format` 单位与显示精度 |

ECharts、表格与 KPI 每模块必须给非空 `bindings`，用于表达自己的数据结构：

```json
{"target":"series[0].links","ref":{"type":"file","id":"data/flows.json"},"expects":"array<object>","required_fields":["source","target","value"]}
```

一个模块可绑定树、节点、边、多个 dataset 或非图表内容；`target` 指定实际注入位置，`expects` 说明结构，复杂嵌套进一步说明字段路径与关系。保留顶层 `data.binding` 作为兼容摘要，1.1 的模块级绑定优先，不能把所有复杂数据都假设为 dataset.source。绑定仅引用数据，不回传行级数值。

### 引用、实现与载体

`spec_ref: {"path":"specs/mechanism.json"}` 指向只包含 spec 对象的真实 JSON 文件。相对路径以 plan.json 所在目录解析；跨机器交接优先相对路径并一起携带文件，也允许本机绝对路径。输出前校验器必须实际读取，文件不存在、无权读取、非 JSON 或语义不完整均失败。6KB 限 plan.json 本体（UTF-8、标准 JSON 序列化），引用文件可更大，但不能借引用回传原始数据。引用是结构化规格，不是未完成任务的占位。

`decision` 不要求 option。`implementation` 的 ECharts 模块必须提供 option 或 `implementation_ref: {path}`（JSON 文件包含 option 对象），这仍是需要上游数据注入及运行时适配的实现规格。`custom` 的 renderItem 等函数不能靠 JSON 字符串直接运行：给出需要上游实现/注册的 renderer 与接口，或交付可检查的代码引用，不承诺 option JSON 自带可执行函数。

`constraints.static: true` 时每模块需 `carrier_adaptation.static.essential_information`，写明核心标签、单位、读数或关系如何无需交互可见。tooltip、缩放和图例选择可以作为附加功能，不能承载唯一证据。`offline: true` 时依赖需使用本地/内联资源；遵守上游已有引擎、主题、字体和渲染路线，不复制网页外壳取代它们。

`ok` 表示选型规格在所请求 output_level 下完成；上游仍需数据计算复核、制作、渲染和静态可读性 QA。不得将 schema 通过或 option 存在解释为交付已完成。
