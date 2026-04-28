## 1. 后端：记录查询接口

- [ ] 1.1 `ClassificationRecordMapper.xml` 新增 select 查询 SQL：`selectByCondition` 方法，支持 predLabel、startTime、endTime、source、summary 条件筛选，summary 使用 `<bind>` 标签转义 LIKE 通配符，隐式 WHERE user_id 条件
- [ ] 1.2 `ClassificationRecordMapper.java` 新增 `selectByCondition` 方法签名
- [ ] 1.3 `ClassificationRecordMapper.xml` 新增 `selectById` 方法
- [ ] 1.4 `ClassificationRecordMapper.java` 新增 `selectById` 方法签名
- [ ] 1.5 新增 `RecordService` 接口，定义 `listByCondition` 和 `getById` 方法
- [ ] 1.6 新增 `RecordServiceImpl`，实现 `listByCondition`（解析 token 获取 userId，传入查询条件）和 `getById`（查询后校验 userId 归属，不匹配返回 null）
- [ ] 1.7 新增 `RecordController`，提供 `GET /api/record/list`（从 Authorization 头解析 userId，调用 RecordService.listByCondition）和 `GET /api/record/{id}`（调用 RecordService.getById，记录不存在或不属于当前用户返回 404）

## 2. 前端：公共图表组件

- [ ] 2.1 新增 `ChartVisualization.vue` 组件，接收 `categories` prop，内含 ECharts 横向柱状图（Top 10，颜色按概率阈值），支持窗口 resize 自适应
- [ ] 2.2 修改 `PatentClassification.vue`，移除内联的 initChart/updateChart/renderChart 方法和 chart data，改用 `<ChartVisualization :categories="result.categories" />`

## 3. 前端：历史记录页面

- [ ] 3.1 在 `api/index.js` 新增 `recordApi` 对象，包含 `getList`（GET /api/record/list）和 `getDetail`（GET /api/record/{id}）方法
- [ ] 3.2 新增 `ClassificationHistory.vue`，包含筛选区域（预测类别下拉、时间范围日期选择器、来源类型下拉、摘要关键字输入框、查询按钮、重置按钮）和数据表格（序号、摘要全文、预测类别、置信度、来源、分类时间、操作）
- [ ] 3.3 实现摘要关键字高亮：对摘要文本先 HTML 转义，再用正则将匹配关键字包裹 `<mark>` 标签，通过 `v-html` 渲染
- [ ] 3.4 实现来源类型映射：source="single" 显示"单条输入"，source="batch" 显示"批量导入"
- [ ] 3.5 实现详情弹窗：点击"详情"打开 el-dialog，展示完整摘要文本 + `<ChartVisualization :categories="detail.topCategories" />`
- [ ] 3.6 在 `router/index.js` 新增 `/classification-history` 路由，设置 `meta: { requiresAuth: true }`
- [ ] 3.7 在 `App.vue` 导航栏新增"分类历史"菜单项
- [ ] 3.8 在 `HomeView.vue` 首页新增"分类历史"功能卡片

## 4. 验证

- [ ] 4.1 验证单条分类功能：改用 ChartVisualization 后，分类结果图表展示与改造前一致
- [ ] 4.2 验证历史页面：分类后可在历史页看到记录，仅显示当前用户记录
- [ ] 4.3 验证筛选：各筛选条件单独和组合使用结果正确
- [ ] 4.4 验证摘要高亮：输入关键字后摘要中匹配词高亮显示，HTML 转义正常
- [ ] 4.5 验证越权防护：手动修改请求 ID 查看他人记录返回 404
- [ ] 4.6 验证 LIKE 转义：搜索 `50%` 或 `test_1` 时不被当作 SQL 通配符
