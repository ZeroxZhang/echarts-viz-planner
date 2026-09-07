# api 模式完整契约

> `api` 模式 = 被其他 Agent / Skill 间接调用。本文档是唯一权威的完整契约；
> SKILL.md §12.2 的最小速查用于第一层兜底。上游未必加载本文件，核心字段必须与 SKILL.md 一致。

## 1. 输入契约（上游怎么调）

上游声明「使用 echarts-viz-planner skill，为这批数据给出可视化方案与 option」，并传入：

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

结构见 `schemas/plan.schema.json`，完整示例见 SKILL.md §12.2 与 v3 方案 §14.2。要点：

### 2.1 status 枚举（封闭）

| 值 | 含义 | 上游应做什么 |
|---|---|---|
| `ok` | 方案完整可用 | 直接渲染 |
| `ok_with_assumptions` | 可用，但含影响结论的假设 | 渲染，同时向用户披露 `assumptions` |
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

### 2.3 option 约定

- **以 `templates/` 起底**：按 `capability_id` 选模板（映射表见 `templates/README.md`），逐项替换占位符，
  输出前确认无 `__X__` 残留；无独立模板的变体按 README「变体起底」表组合。
- 数据用 `dataset` 占位：`"option": { "dataset": { "source": "<由上游注入 data.binding 指定数据>" }, ... }`；
  树/图/桑基/漏斗/日历等系列数据形态按模板内 `__*_DATA__` 占位符说明注入。
- series 类型必须与 `capability_id` 的 runtime 一致；扩展候选的 `echarts.deps` 必须含对应包名+版本。
- 视觉质量规范（references/visual-quality.md）已固化进模板（aria/网格/标签/单色相渐变），替换时不要回退。
- 主题遵循上游 `theme`，缺省 `light`。
- 网页载体可给 `templates/render-shell.html` 外壳（option 替换 `__OPTION__`）；交接细节见 `references/handoff.md`。

## 3. 契约稳定性

- `contract_version` 语义化管理（当前 `1.0`）：破坏性变更升主版本。
- **幂等**：同一输入必须得到同一 `capability_id` 与 `encode`，不允许结果漂移。
- 字段**只增不删**；上游可忽略未知字段。
- 所有枚举取封闭列表，不返回自由文本枚举值。
- 任何情况（包括失败）都返回结构合法的 JSON，不抛裸文本报错。
- JSON ≤ 6KB；超限先裁剪 `rejected` 明细，再裁剪 `audit`，最后裁剪 `alternatives`，核心字段（status/plan/assumptions/missing）不可裁。

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
