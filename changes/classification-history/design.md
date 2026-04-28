## Context

步骤1（分类结果持久化）已实现，`classification_record` 表已有数据写入能力（`ClassificationRecordMapper.insert`）。当前系统无法查看历史记录，用户分类后无法回顾结果。本步骤在已有持久化基础上构建"看"的能力。

现有代码现状：
- `ClassificationRecordMapper` 仅有 `insert` 方法，需新增 select 查询
- `PatentClassification.vue` 内联 120+ 行 ECharts 代码，未组件化
- 前端路由、导航栏、首页均无"分类历史"入口
- token 解析逻辑已在 `UserController` 中实现，可复用

## Goals / Non-Goals

**Goals:**
- 提供分类历史列表查询，支持多条件组合筛选
- 仅展示当前用户自己的记录，防止越权
- 摘要全文展示 + 关键字高亮
- 提取公共图表组件，消除代码重复
- 详情弹窗复用图表组件展示概率分布

**Non-Goals:**
- 不实现分页（后续按需加）
- 不实现记录删除/编辑
- 不实现管理员查看所有用户记录

## Decisions

### D1: 在现有 ClassificationRecordMapper 上新增 select 方法

**选择**: 修改现有 Mapper，而非新建 RecordMapper
**理由**: 同一张表两个 Mapper 会导致维护困惑，insert 和 select 本就属于同一实体的不同操作
**替代方案**: 新建独立 RecordMapper — 拒绝，因为命名冲突且职责重叠

### D2: RecordController 独立于 PatentController

**选择**: 新增 `RecordController`，不把查询接口加到 `PatentController`
**理由**: `PatentController` 职责是分类推理，记录查询是独立关注点。路径也不同（`/api/record/*` vs `/api/patent/*`）

### D3: userId 从 token 隐式解析，不作为 API 参数

**选择**: 后端从 `Authorization` 头解析 userId，作为隐式 WHERE 条件
**理由**: 安全性——前端传 userId 可被篡改，token 解析保证用户只能看自己的数据。复用 `UserController` 中已有的解析逻辑。

### D4: 单条记录详情接口校验归属

**选择**: `GET /api/record/{id}` 查询后校验 `record.userId == currentUserId`，不匹配返回 404
**理由**: 防止越权访问。用 404 而非 403，避免泄露记录存在性。

### D5: LIKE 通配符转义

**选择**: MyBatis XML 中使用 `<bind>` 标签对 `%` 和 `_` 转义
**理由**: 用户输入 `%` 或 `_` 不应被当作 SQL 通配符，属于安全性要求
**替代方案**: Java Service 层转义 — 可行但分散逻辑，XML 统一处理更清晰

### D6: 提取 ChartVisualization 公共组件

**选择**: 从 `PatentClassification.vue` 提取 `ChartVisualization.vue`，接收 `categories` prop
**理由**: 历史详情弹窗需要复用同一图表渲染逻辑，内联代码重复不可取
**影响**: `PatentClassification.vue` 改用组件后功能表现不变（验收标准已覆盖）

### D7: 摘要高亮实现方式

**选择**: 前端使用 `v-html` + 正则替换，将匹配关键字包裹在 `<mark>` 标签中
**理由**: 简单直接，`<mark>` 语义正确且 Element UI 默认样式即可
**风险**: XSS — 需对摘要文本做 HTML 转义后再替换关键字，避免注入

## Risks / Trade-offs

- **[XSS via v-html]** → 摘要文本先 `_.escape()` 或手动转义 HTML 实体，再替换关键字为 `<mark>`，确保用户输入的 HTML 不被执行
- **[全文摘要导致表格行高失控]** → 摘要可能 200-500 字，表格行会撑高。可接受——用户明确要求不截断，且详情弹窗有完整查看入口
- **[LIKE '%keyword%' 性能]** → 当前数据量极小（论文项目），无需全文索引。万级以上再考虑
- **[PatentClassification.vue 重构风险]** → 提取图表组件时可能引入回归。通过验收标准"改用公共图表组件后单条分类功能表现不变"覆盖
