# 能力目录 · 常驻索引

> 技术基线：Apache ECharts **6.1.0** · `verified_at: 2026-09-07` · 核验方式：npm view + 直读 apache/echarts@6.1.0 `src/export/charts.ts` 与 `components.ts`。
> 改基线版本前必须同步更新本目录并跑通 golden set；运行时不查 npm latest。

## 使用协议

1. 选型 Step 2 必须按「族」在本表召回**全部**候选，不得只凭记忆挑常见图。
2. 需要对抗复核时读 `details/<族>.yaml`；本表一行即一个候选的最小编码。
3. 状态列三态：`native`（核心可用）/ `ext:<包>@<版本>`（允许，须声明依赖）/ `ext:<包> / 默认禁用`。
4. details 尚未覆盖的族（correlation / composition / hierarchy / geo / kpi / relation / special），以本表为召回依据并结合 ECharts 6.1.0 知识复核，`audit` 中标注 `catalog_coverage: partial`。

## 全量索引（61 条）

| id | 中文名 | 族 | 最小数据契约 | 主分析任务 | 状态 |
|---|---|---|---|---|---|
| bar.basic | 柱状图 | comparison | 1类目+1数值 | ranking | native |
| bar.grouped | 分组柱状图 | comparison | 2类目+1数值 | grouped_compare | native |
| bar.stacked | 堆叠柱状图 | comparison | 2类目+1数值 | stacked_compare | native |
| bar.pct | 百分比堆叠柱状图 | comparison | 2类目+1数值 | composition | native |
| bar.rank | 横向排名条形图 | comparison | 1类目+1数值 | ranking | native |
| bar.diverging | 正负发散条形图 | comparison | 1类目+1数值(可负) | deviation | native |
| bar.waterfall | 瀑布图 | comparison | 1类目+2数值 | cumulative_change | native |
| bar.dynamic | 动态排序条形图 | comparison | 1类目+1数值+时间 | ranking_over_time | native |
| bar.polar | 极坐标柱状图 | comparison | 1类目+1数值(周期) | cyclic_compare | native |
| pictorial.lollipop | 棒棒糖图 | comparison | 1类目+1数值 | ranking | native |
| pictorial.pictorial | 象形柱状图 | comparison | 1类目+1数值 | ranking | native |
| radar.radar | 雷达图 | comparison | ≥3指标+1实体 | multi_dim_compare | native |
| ext.bar-range | 区间柱状图 | comparison | 1类目+2数值(区间) | range_compare | ext:@echarts-x/custom-bar-range@1.2.1 |
| line.basic | 折线图 | trend | 时间+1数值 | trend | native |
| line.multi | 多序列折线 | trend | 时间+多数值 | multi_trend | native |
| line.area | 面积图 | trend | 时间+1数值 | volume_trend | native |
| line.stacked_area | 堆叠面积图 | trend | 时间+类目+1数值 | composition_over_time | native |
| line.step | 阶梯折线图 | trend | 时间+1数值 | discrete_trend | native |
| candlestick.k | 蜡烛图 | trend | 时间+4数值(OHLC) | financial_trend | native |
| themeriver.themeriver | 主题河流图 | trend | 时间+类目+1数值 | composition_over_time | native |
| ext.line-range | 区间折线图 | trend | 时间+2数值 | band_trend | ext:@echarts-x/custom-line-range@1.1.1 |
| bar.hist | 直方图 | distribution | 1数值 | distribution_shape | native |
| boxplot.box | 箱线图 | distribution | 1类目+1数值数组 | distribution_compare | native |
| ext.violin | 小提琴图 | distribution | 1类目+1数值数组 | distribution_shape | ext:@echarts-x/custom-violin@1.1.1 |
| ext.contour | 等高线密度图 | distribution | 2数值 | density_2d | ext:@echarts-x/custom-contour@1.2.1 |
| scatter.beeswarm | 蜂群图 | distribution | 1类目+1数值 | distribution_points | native(custom) |
| pie.basic | 饼图 | composition | 1类目+1数值 | part_whole | native |
| pie.donut | 环形图 | composition | 1类目+1数值 | part_whole | native |
| pie.rose | 南丁格尔玫瑰图 | composition | 1类目+1数值(周期) | part_whole_cyclic | native |
| ext.segmented-donut | 分段环形图 | composition | 1类目+1数值 | part_whole | ext:@echarts-x/custom-segmented-doughnut@1.1.1 |
| ext.wordcloud | 词云 | composition | 文本+频次 | keyword_highlight | ext:@echarts-x/custom-word-cloud@1.0.1 |
| scatter.basic | 散点图 | correlation | 2数值 | correlation | native |
| scatter.bubble | 气泡图 | correlation | 3数值 | correlation_3d | native |
| scatter.quadrant | 四象限散点图 | correlation | 2数值+基准 | quadrant_analysis | native |
| effectscatter.ripple | 涟漪散点图 | correlation | 2数值(+权重) | highlight | native |
| heatmap.matrix | 矩阵热力图 | correlation | 2类目+1数值 | cross_tabulation | native |
| heatmap.calendar | 日历热力图 | correlation | 日期+1数值 | temporal_pattern | native |
| parallel.parallel | 平行坐标图 | correlation | ≥3数值 | multi_dim_correlation | native |
| sankey.sankey | 桑基图 | flow | 源+目标+流量 | flow_path | native |
| chord.chord | 和弦图 | flow | 源+目标+流量(双向) | flow_relation | native |
| funnel.funnel | 漏斗图 | flow | 阶段+数值 | stage_loss | native |
| ext.stage | 阶段图 | flow | 阶段+多指标 | stage_compare | ext:@echarts-x/custom-stage@1.1.1 |
| tree.tree | 树图 | hierarchy | 节点+父节点 | hierarchy | native |
| treemap.treemap | 矩形树图 | hierarchy | 节点+父节点+数值 | hierarchy_part_whole | native |
| sunburst.sunburst | 旭日图 | hierarchy | 节点+父节点+数值 | hierarchy_part_whole | native |
| graph.force | 关系图 | relation | 节点+边(+权重) | network | native |
| map.choropleth | 分级设色地图 | geo | 地区名+1数值 | geo_compare | native |
| map.scatter | 地图散点 | geo | 经纬度+1数值 | geo_distribution | native |
| lines.effect | 飞线图 | geo | 源/目标坐标+1数值 | geo_flow | native |
| gauge.basic | 仪表盘 | kpi | 1数值+目标 | goal_progress | native |
| gauge.bullet | 子弹图 | kpi | 1数值+目标区间 | goal_progress | native |
| ext.liquidfill | 水球图 | kpi | 1数值(0~1) | goal_progress | ext:@echarts-x/custom-liquid-fill@1.0.2 |
| kpi.card | KPI 卡（HTML） | kpi | 1~5 数值 | headline_metric | 非ECharts |
| table.detail | 明细表 | special | 多字段 | exact_lookup | 非ECharts |
| table.pivot | 透视表 | special | 2类目+1数值 | cross_tabulation | 非ECharts |
| text.conclusion | 纯文字结论 | special | 无 | headline | 非ECharts |
| infographic | 信息图 | special | 无固定 | mechanism_explain | 非ECharts |
| custom.custom | 自定义系列 | special | 任意 | bespoke | native |
| gl.bar3d | 3D 柱状图 | geo | 2类目+1数值 | 3d_compare | ext:echarts-gl@2.1.0 / 默认禁用 |
| gl.scatter3d | 3D 散点图 | correlation | 3数值 | 3d_correlation | ext:echarts-gl@2.1.0 / 默认禁用 |
| gl.surface | 3D 曲面图 | distribution | 网格数值 | 3d_surface | ext:echarts-gl@2.1.0 / 默认禁用 |

## 坐标系与布局（组合能力，不是独立图种）

Cartesian/Grid · Polar · Radar · Parallel · SingleAxis · Calendar · Geo · Matrix（6.0 新增）· Graph layout · Tree layout · 多 Grid 组合

## 组件（常常比换图更能改善表达）

`dataset`（数据统一入口）· `transform`（filter/sort/aggregate 等数据变换）· `encode` · `visualMap`（增加一个视觉维度）· `dataZoom` + `thumbnail`（6.0 新增，大数据量导航关键组件）· `timeline` · `brush` · `toolbox` · `graphic` · `markPoint/markLine/markArea` · `legend` · `tooltip` · `axisPointer` · `title` · `aria`

## 扩展准入备忘（details/extensions.yaml 属 v0.2，先固化于此）

| 扩展 | 版本/peer | 政策 |
|---|---|---|
| @echarts-x/custom-{violin@1.1.1, contour@1.2.1, stage@1.1.1, segmented-doughnut@1.1.1, bar-range@1.2.1, line-range@1.1.1} | peer 均 `^6.0.0` | 允许，输出须声明依赖 |
| @echarts-x/custom-word-cloud | 1.0.1 | 允许（替代禁用的 echarts-wordcloud） |
| @echarts-x/custom-liquid-fill | 1.0.2 | 允许（替代禁用的 echarts-liquidfill） |
| echarts-gl | 2.1.0，peer `^5.1.2 \|\| ^6.0.0` | 默认禁用（3D 降低读数精度），明确要求才启用 |
| echarts-wordcloud / echarts-liquidfill | peer 仅 `^5.0.1` | **禁用**，改用 @echarts-x 对应包 |
| 其他社区插件 | — | 不进候选池 |

api 模式若上游 `constraints.allow_extensions: false`：扩展类候选一律硬淘汰，`rejected` 理由 `policy_blocked`，同时给出原生替代。

新扩展准入须同时满足：Apache 官方维护、来源与许可可核验、与锁定版本兼容、有可运行示例、未废弃、通过依赖与渲染检查。
