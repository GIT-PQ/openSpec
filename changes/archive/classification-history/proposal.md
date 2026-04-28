## Why

系统仅支持单条专利分类，分类结果未持久化，用户无法回顾历史分类记录、按条件筛选或导出结果。论文评审指出系统功能完整性不足，缺少历史记录、筛选、导出等实际业务高频功能。步骤1（分类结果持久化）已实现，本步骤在此基础上提供"看"的能力。

## What Changes

- 新增"分类历史"页面，以表格形式展示当前用户的分类记录
- 支持按预测类别、时间范围、来源、摘要关键字等条件筛选
- 摘要列显示完整文本（不截断），摘要关键字筛选时高亮匹配词
- 点击"详情"弹窗展示完整摘要 + ECharts 概率分布图
- 所有查询接口仅返回当前登录用户的记录（从 token 解析 userId 作为隐式过滤）
- 单条记录详情接口校验记录归属，防止越权访问
- 提取公共图表组件 `ChartVisualization`，供分类页和历史详情弹窗复用
- 改造 `PatentClassification.vue` 使用公共图表组件
- 导航栏和首页新增"分类历史"入口

## Capabilities

### New Capabilities
- `record-query`: 分类记录查询与筛选（后端 API + 数据范围控制 + LIKE 通配符转义）
- `classification-history-ui`: 分类历史前端页面（表格+筛选+详情弹窗+摘要高亮）
- `chart-visualization`: 公共图表组件（从 PatentClassification.vue 提取，供多页面复用）

### Modified Capabilities

## Impact

- **Java 后端**: 新增 `RecordController`、`RecordService`，修改 `ClassificationRecordMapper` 新增 select 查询方法
- **前端**: 新增 `ClassificationHistory.vue`、`ChartVisualization.vue`，修改 `PatentClassification.vue`、`App.vue`、`HomeView.vue`、`router/index.js`、`api/index.js`
- **API**: 新增 `GET /api/record/list`、`GET /api/record/{id}`
- **依赖**: 无新依赖（ECharts 已在项目中）
