# Option 模板库 · 索引与占位符约定

> 用途：api 模式产出「可直接运行的 option」时**以本目录模板起底**（见 references/api-contract.md §2.3），
> 替换占位符后返回。interactive 模式给完整 option 时同样使用。
> 基线：ECharts 6.1.0。模板已固化视觉质量规范（references/visual-quality.md）：去边框网格、
> aria 默认开启、无装饰动画、单色相渐变、标签规则；颜色取主题色板，模板中的色值仅作强调色示例。

## 模板 → capability 映射

| 模板文件 | capability_id | 族 |
|---|---|---|
| bar.basic.json | bar.basic | comparison |
| bar.grouped.json | bar.grouped | comparison |
| bar.stacked.json | bar.stacked | comparison |
| bar.pct.json | bar.pct | comparison |
| bar.rank.json | bar.rank | comparison |
| bar.diverging.json | bar.diverging | comparison |
| radar.radar.json | radar.radar | comparison |
| line.basic.json | line.basic | trend |
| line.multi.json | line.multi | trend |
| line.area.json | line.area | trend |
| line.stacked_area.json | line.stacked_area | trend |
| candlestick.k.json | candlestick.k | trend |
| boxplot.box.json | boxplot.box | distribution |
| pie.basic.json | pie.basic | composition |
| pie.donut.json | pie.donut | composition |
| scatter.basic.json | scatter.basic | correlation |
| scatter.bubble.json | scatter.bubble | correlation |
| heatmap.matrix.json | heatmap.matrix | correlation |
| heatmap.calendar.json | heatmap.calendar | correlation |
| parallel.parallel.json | parallel.parallel | correlation |
| sankey.sankey.json | sankey.sankey | flow |
| funnel.funnel.json | funnel.funnel | flow |
| chord.chord.json | chord.chord | flow |
| tree.tree.json | tree.tree | hierarchy |
| treemap.treemap.json | treemap.treemap | hierarchy |
| sunburst.sunburst.json | sunburst.sunburst | hierarchy |
| gauge.basic.json | gauge.basic | kpi |
| gauge.bullet.json | gauge.bullet | kpi |
| map.choropleth.json | map.choropleth | geo |

未提供模板的 capability：ext.* 扩展类（依赖声明见 `catalog/details/extensions.yaml`，骨架由载体按包文档拼装）、
special 族（table.detail / text.conclusion / kpi.card / infographic 非 ECharts，由载体渲染）、
变体类（bar.waterfall / bar.dynamic / scatter.quadrant / ext 等以最近模板起底 + 字段替换，见下表「变体起底」）。

## 占位符约定（替换顺序固定）

| 占位符 | 含义 | 替换来源 |
|---|---|---|
| `__DATA__` | dataset.source | `data.binding`（array<object>），不回传数据时由上游注入 |
| `__X__` `__Y__` | 主维度/指标字段名 | `plan[].encode` |
| `__SERIES_A__` `__SERIES_B__` | 分组/系列字段名；超过 2 个系列按同构复制 series 项 | `plan[].encode` + 画像 |
| `__NAME__` `__VALUE__` `__GROUP__` | 名称/数值/分组字段 | `plan[].encode` |
| `__DATE__` `__OPEN__` `__CLOSE__` `__LOW__` `__HIGH__` | K 线字段 | `plan[].encode` |
| `__SIZE_DIM_INDEX__` | dataset 中尺寸字段的列序号 | 画像列序 |
| `__MIN__` `__MAX__` | visualMap 数值域 | 画像数值范围（取整扩界） |
| `__RANGE__` | calendar 日期范围 | 画像 time_field min/max |
| `__DATA_*__` 类 | series 内数据数组 | 形态见下 |
| `__RADAR_INDICATORS__` | `[{name, max}, ...]` | 画像各指标范围 |
| `__RADAR_DATA__` | `[{value:[...], name}, ...]` | 上游/transform |
| `__PARALLEL_AXES__` | `[{dim, name}, ...]` 各轴 min/max 显式声明 | 画像各指标范围 |
| `__PARALLEL_DATA__` | 数值数组行 | 上游/transform |
| `__SANKEY_NODES__` | `[{name}, ...]` | 去重后的源+目标集合 |
| `__SANKEY_LINKS__` | `[{source, target, value}, ...]` | 聚合后的流量 |
| `__CHORD_NODES__` `__CHORD_LINKS__` | 同 sankey | 同 sankey |
| `__FUNNEL_DATA__` | `[{name, value}, ...]` 按业务顺序 | 聚合 |
| `__TREE_DATA__` | 嵌套 `{name, value?, children:[...]}`；扁平 id/parent 须先转换 | transform/上游 |
| `__CALENDAR_DATA__` | `[["YYYY-MM-DD", value], ...]` | 聚合 |
| `__MAP_NAME__` | 注册地图名（如 "china"） | 载体 registerMap 时约定 |
| `__MAP_DATA__` | `[{name, value}, ...]`，地区名必须与 GeoJSON 匹配 | 聚合 |
| `__VALUE__` `__LABEL__` `__TARGET__` | 单值/标签/目标 | `plan[].encode` |

## 替换规则

1. 先按 `data.binding` 确认数据形态（array<object> / 嵌套树 / 邻接表），选择匹配的模板。
2. 逐个替换占位符；**不留任何 `__X__` 残留**——这是渲染前最后一道人工检查。
3. 系列字段多于模板示例数时按同构复制 series 项（bar.grouped/stacked/pct、line.multi/stacked_area）。
4. 折线模板 Y 轴 `scale: true`：非零起点须在 `yAxis.name` 或 graphic 标注截断（视觉规范）。
5. 颜色：模板不带显式色板（散点/柱默认主题色）；强调色只有一个，需要时在对应 series.itemStyle 指定。

## 变体起底（无独立模板的 capability）

| capability_id | 起底模板 | 增量 |
|---|---|---|
| bar.waterfall | bar.stacked.json | 增加透明占位 series 承载基线，stack 改名 |
| bar.dynamic | bar.rank.json | 外层 timeline 或逐帧 setOption（载体实现），realtimeSort |
| bar.polar | bar.basic.json | 加 polar 坐标系替换 grid |
| pictorial.lollipop | bar.rank.json | series 改 scatter，symbolSize 8，连线 markLine |
| pictorial.pictorial | bar.basic.json | series 改 pictorialBar，symbol 按图标语义 |
| scatter.quadrant | scatter.basic.json | 加 markLine 两条基准线 + graphic 象限标签 |
| effectscatter.ripple | scatter.basic.json | series 改 effectScatter（涟漪仅强调用途） |
| line.step | line.basic.json | series 加 `"step": "end"`（按业务语义） |
| themeriver.themeriver | line.stacked_area.json | series 改 themeRiver |
| bar.hist | bar.basic.json | 分箱参数写入 plan.transforms 并披露 |
| graph.force | chord.chord.json | series 改 graph，layout force，roam true |
| map.scatter | scatter.basic.json | 加 geo 坐标系，encode lng/lat |
| lines.effect | sankey.sankey.json | series 改 lines，data 为坐标对 |
| gl.* | 对应 2D 模板 | 需 echarts-gl@2.1.0，默认禁用（先确认 allow_3d） |
