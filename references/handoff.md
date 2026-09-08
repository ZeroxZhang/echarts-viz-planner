# 交接指南（兼容优先，不固化）

> v1.0 交接契约采取**兼容优先**设计：本 Skill 只产出「载体无关的最小信息包」，
> 不绑定任何产物 Skill 的接口；载体可任意替换、随时演进。上游/载体拿到信息包后自行适配，
> 本文件只给适配要点与降级链。

## 1. 交接信息包（载体无关）

上游指定 1.1 + decision 时用完整契约 §6 的 rationale、spec/spec_ref、模块 bindings 与约束适配交接，不要求完整 option。下列五件适用于 implementation。已有渲染底座优先复用，外壳仅为没有底座的网页参考。

对每个模块（plan[].capability_id），交接以下五件，缺一即标注：

1. **capability_id** + `plan[].question`：渲染方知道这是什么、回答什么问题（用于标注/无障碍/图注）。
2. **完整 option**：以 `templates/` 起底、**占位符已全部替换**的 ECharts 6.1.0 option（含 `aria`）。
   api 不内联行级数据；用 data.binding 或 1.1 模块 bindings 说明注入形态。
3. **数据注入说明**：`data.binding`（mode/expects/required_fields）。不回传数据本体时，
   上游把数据按 binding 注入 option.dataset 或 series.data。
4. **依赖清单**：`echarts@6.1.0` + `echarts.deps` 中的扩展包（精确版本）。
5. **渲染校验提示**：`plan[].verify_hints`（如「节点标签是否溢出」「散点样本量与 392 一致」）。

## 2. 载体适配矩阵（要点，非固化接口）

| 载体 | 常见实现 | 适配要点 |
|---|---|---|
| 独立网页/Dashboard | `lark-apps`（可分享部署）/ `huashu-design`（HTML 原型） | 直接用 `templates/render-shell.html` 外壳；多图=多 chart 实例共享一个 echarts import |
| 飞书文档内嵌 | `lark-doc` 或环境内 htmlbox 类能力 | 宽 100%、高 360–420px；若载体禁外部脚本 → 走降级链（§5） |
| PPT/汇报 | `huashu-slides` | ECharts 需浏览器渲染后截图/导出 SVG 再插入；每屏一个结论 |
| 白板/信息图 | `beautiful-feishu-whiteboard` | 静态 SVG 路线：选型结论不变，视觉由白板风格重绘（机制型内容优先） |
| 移动端 | 任意网页载体 | 交互网页可调整图例与 tooltip；静态核心信息必须直接可见 |

## 3. 渲染外壳（最大兼容的最小实现）

`templates/render-shell.html` 是**载体无关的规范化外壳**：ESM 引入 `echarts@6.1.0`（jsdelivr CDN），
`__OPTION__` 替换为最终 option，并完成数据注入与依赖适配后验证运行；CDN 模板本身不支持离线。
载体侧只需要做两件事：注入 option（替换 `__OPTION__`）、处理多图（复制 div + 复用 import）。
外壳不含任何载体专属 API——这是兼容性的来源。

## 4. 依赖解析三档（载体按能力选择，从高到低）

1. **npm 环境**（lark-apps 全栈、前端工程）：`npm i echarts@6.1.0` + `echarts.deps` 中的 `@echarts-x/*`。
2. **CDN ESM**：`https://cdn.jsdelivr.net/npm/echarts@6.1.0/dist/echarts.esm.min.js`（外壳默认档）。
3. **离线内联快照**：载体禁外网时内联 echarts.min.js 快照，并标注「能力目录截至 6.1.0」。
扩展包优先级同此（violin@1.1.1 / contour@1.2.1 / stage@1.1.1 / segmented-doughnut@1.1.1 /
bar-range@1.2.1 / line-range@1.1.1 / liquid-fill@1.0.2 / word-cloud@1.0.1）。

## 5. 降级链（载体能力不足时的顺序）

```
交互 ECharts（首选）
  → 静态 SVG/PNG（载体无法执行脚本：白板、邮件、部分文档）
  → 表格 + 文字（连图片都不支持：纯文本终端、飞书表格）
```
降级不改变**选型结论**与字段映射，只改变表达媒介；每一级都保留 conclusion + capability_id +
字段映射，确保下游可读、可追溯。

## 6. 交接自检清单（interactive 移交前 / api 输出 carrier_adaptation 前）

- [ ] option 中无 `__X__` 类占位符残留
- [ ] `echarts.deps` 与 option 实际使用的扩展一致，版本精确
- [ ] 数据注入说明与 option.dataset/series.data 形态一致
- [ ] verify_hints 可执行（每条都是可验证的渲染检查）
- [ ] 尺寸适配（lark_doc 400px 高 / web responsive / 移动断点）已写入 carrier_adaptation
- [ ] 降级链的下一级已备好（表格版本字段映射）
