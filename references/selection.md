# 选型细则 · 任务路由 + 对抗复核 + 淘汰规则

> 选型五步见 SKILL.md §6。本文档细化 Step 1 任务分类、Step 4 对抗复核对、Step 3 淘汰规则。
> Step 2 的依据永远是 `catalog/index.md` 全量索引，不是本文档的记忆捷径。

## 1. 分析任务分类（Step 1，可枚举、可判定）

一个需求可命中多个任务，按「回答主问题的重要性」排序后逐个处理。

| 任务 | 判据 | 命中族 |
|---|---|---|
| trend 趋势 | 存在时间/有序维度，关心变化方向与幅度 | trend |
| ranking 比较排名 | 类目间大小比较，无时间主诉求 | comparison |
| composition 构成 | 数值构成一个整体，关心占比 | composition / comparison(bar.pct) |
| distribution 分布 | 关心个体散落形态、离散度、异常 | distribution |
| correlation 相关 | 两/多维字段之间的关联 | correlation |
| flow_path 流向 | 实体在节点间流动且守恒 | flow |
| hierarchy 层级 | 数据有父子结构 | hierarchy |
| network 关系网络 | 实体间多对多关系 | relation |
| geo_* 地理 | 字段可解析为地区/经纬度 | geo |
| goal_progress 达成度 | 单指标 vs 目标 | kpi |
| exact_lookup 明细查数 | 需要精确读数而非模式 | special(table/text) |
| mechanism_explain 机制流程 | 解释作用、条件、反馈；证据与假设可分 | diagram / special(infographic) |
| process_order / responsibility_flow | 存在有向交接，角色或阶段是判断的一部分 | diagram / flow |
| journey_responsibility | 时间或阶段与触点、责任、前后台关系并存 | diagram |
| capability_hierarchy / conditional_decision | 包含、依赖、决策条件不能被数值排名替代 | diagram / hierarchy |
| paired_change | 同实体、同口径的两个观测需要突出变化 | comparison |

## 2. 任务 → 候选族路由表（召回顺序按优先级）

| 主任务 | 第一族 | 第二族 | 注意 |
|---|---|---|---|
| trend | trend | — | 时间点 ≤ 2 时落回 comparison |
| ranking | comparison | — | 长标签优先横向（bar.rank） |
| composition | composition | comparison(bar.pct) | 先验证「整体」语义成立 |
| distribution | distribution | correlation(scatter) | 先验证样本量与分箱 |
| correlation | correlation | — | 2 字段散点、2 类目热力、多维平行坐标 |
| flow_path | flow | relation | 先验证单向 + 守恒 + 无环 |
| hierarchy | hierarchy | composition | treemap/sunburst 兼表占比 |
| network | relation | flow(chord) | 无权重时 chord/sankey 不成立 |
| geo | geo | comparison(bar.rank) | 地图数据匹配失败 → 排名条形替代 |
| goal_progress | kpi | comparison(bar.diverging) | 单值优先 KPI 卡，别为画图画图 |
| exact_lookup | special | — | 表格/文字就是最优解 |
| mechanism_explain / dependency | diagram | relation | 作用方向与证据状态需可见；不将相关画为已证实因果 |
| process_order / responsibility_flow | diagram | flow | 无真实流量时不得用线宽暗示数量 |
| journey_responsibility | diagram | special(table) | 旅程空间编码阶段，泳道编码主体；责任查找可用矩阵表 |
| capability_hierarchy / conditional_decision | diagram | hierarchy | 区分包含、依赖、必要条件与充分条件 |
| paired_change | comparison | special(table) | 哑铃突出差额，坡度突出方向/排序变化，原值查数用表格 |

## 3. 必测的对抗复核对（Step 4）

至多 3 个可行候选两两对照，不足时不凑数；逐对写出「什么条件下谁胜出」。下列对在候选与任务相关时覆盖：

| 对 | 判据要点 |
|---|---|
| dumbbell ↔ slope ↔ grouped bar | 同行绝对差距 vs 两期排序迁移 vs 绝对量；不能用斜率比较不同横距 |
| swimlane ↔ process ↔ table | 责任交接可追踪 vs 仅顺序 vs 精确责任查找；主体缺失不能凭空设泳道 |
| mechanism ↔ dependency ↔ graph | 作用假设/反馈 vs 前置依赖 vs 通用关系；必须标明边的含义 |
| journey ↔ timeline ↔ table | 多触点/前后台关系 vs 单一时序 vs 查找责任与时间；缺日期用有序阶段 |
| capability ↔ tree ↔ condition | 包含地图 vs 严格单父层级 vs 判断条件；共用节点不能假装独立子树 |
| sankey ↔ chord | 单向守恒 vs 双向对称 |
| sankey/chord ↔ graph | 有无量化流量/权重 |
| tree ↔ treemap ↔ sunburst | 纯结构 vs 结构+占比；扇区多时 sunburst 退化 |
| boxplot ↔ violin ↔ beeswarm | 统计摘要 vs 形态 vs 个体；样本量与受众决定 |
| radar ↔ parallel | 多指标对比（少量实体）vs 多维相关（大量记录） |
| funnel ↔ stacked bar | 同批对象递减守恒 vs 分组构成 |
| themeRiver ↔ stacked area | 宏观涨落叙事 vs 需要读数；层数 > 4 时禁用面积 |
| pie ↔ rose ↔ 100% stacked bar | 构成对比：类目 ≤ 6 才考虑 pie；rose 仅周期语义 |
| gauge ↔ bullet ↔ KPI card | 单值达成：空间、精度与信息密度 |
| calendar heatmap ↔ matrix heatmap | 时间型双类目 vs 任意双类目交叉 |
| map ↔ ranked bar | 地理是故事的一部分 vs 只是分组标签 |

## 4. 硬淘汰规则（Step 3，逐条留理由）

1. 缺必要字段（对照 details `contract.required`）
2. 字段类型不符（数值/时间/文本语义不匹配）
3. 无法回答目标问题
4. 语义不成立：比例不构成整体、流向有环、层级不成立、阶段非同一批对象
5. 基数或数据量超限（对照 details `contract` 的 ok/warn 区间；warn 不淘汰，但须在 risks 披露）
6. 依赖不可用（扩展包 peer 不兼容、声明禁用）
7. 策略或上游约束禁用（`allow_extensions: false` / `allow_3d: false` → `policy_blocked`）
8. 地图数据无法匹配（地区名对不上 GeoJSON）
9. 视觉编码会造成明显误导（如彩虹色连续值、玫瑰图表达非周期数据）
10. 调用方明确禁止

**三态分离**：`supported_by_echarts`（目录里有）= / `available_in_runtime`（依赖可加载）= / `allowed_by_policy`（当前约束允许）。被策略淘汰 ≠ 能力不存在：说明「支持但当前不用」并给替代。

## 5. 判定输出格式（Step 5）

```
主方案: <capability_id> <中文名>
匹配度: 强 / 中 / 弱
置信度: 高 / 中 / 低
次选:   <capability_id> —— 在 <条件> 下反超主方案
```

**禁止**：数字得分、加权总分、百分比置信度。依据必须是可审计的定性理由（数据契约、语义、任务匹配、受众场景）。

## 6. 允许不画图（硬规则）

以下场景「不画图」参与最终竞争，且经常获胜：
- 明细查数（`table.detail`）、样本量 < 5（`text.conclusion`）、单值对比（`kpi.card` 或一句话）
- 目标问题本身就是「某数值是多少」而非「模式是什么」
- api 模式用 `capability_id: table.detail` / `text.conclusion` / `kpi.card` 表达，不强行返回图表

## 7. 指定图表不当时（硬规则）

用户/上游明确指定了图表但选型判断不合适：
- **先执行要求**，同时指出风险与更优解，不擅自替换。
- interactive：在方案中给「按指定执行」版本 + 「建议替换」版本。
- api：按上游指定输出，把风险写入 `risks`，把更优解写入 `alternatives`。
