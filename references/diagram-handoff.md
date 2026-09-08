# 通用图示语义交接

保留材料的时间、主体、节点/边、包含、分支、责任、转移和约束。按 catalog/index.md 召回 diagram 族，并读 diagrams.yaml；未量化关系不先扁平化为指标列表。

`infographic` 旧入口继续有效；`infographic.*` 只是更可检索的子能力，均采用契约 1.1 的 `kind: infographic`。开放的 `structure` 不限制图型或节点数；常用 `nodes_ref`/`edges_ref` 引用原材料，并提供 `node_fields`、`edge_fields`、`lanes`、`stages`、`layout_intent`。不在主 plan 回传数据本体。`relationship_semantics` 解释箭头、包含、并列与虚线；`reading_order` 是实际阅读路径。示例见 templates/diagram.semantic.json。

实施交接：优先载体已有自动布局入口，根据实际宽高与字体测量节点；连接到节点锚点，不能将边末端写成与数据脱离的绝对坐标。空间不足先换方向、扩展空间或有意义分面，再考虑改表达。不能通过缩小所有字号、截断节点或删除边假装容纳。图示不要求 ECharts，静态 SVG 或 HTML 均可。

核对最终成稿：来源节点与边是否完整；lane 是否确为主体；stage 是否确为阶段；标签是否保持端点归属；反馈/条件是否可读；主张与假设是否区分；换尺寸后重新布局。若采用了另一表达，在已有 page_spec 或工作笔记简记变化与理由。

验证加载只说明资源兼容；真正前向调用还须在看到渲染结果前完成目标→候选召回→必要字段淘汰→至多三个可行候选对照→语义规格，并用实际加载源的 validate_plan.py 校验。最终图中看不到所选关系时，建议尚未落实。
