## Context

当前系统已完成分类结果持久化（步骤1）和历史记录展示与筛选（步骤2），用户可以在历史页面查看自己的分类记录并按条件筛选。但缺少导出能力，用户无法将筛选结果导出为 Excel 文件进行二次分析或汇报。

**现有架构**：
- Java 后端：Spring Boot + MyBatis，已有 `RecordController`、`RecordService`
- 前端：Vue 2 + Element UI，已有 `ClassificationHistory.vue` 筛选页面
- 数据库：MySQL，`classification_record` 表存储分类历史

**约束**：
- 用户数据隔离：导出仅限当前用户自己的记录（从 token 解析 userId）
- 单次导出上限 200 条，避免大数据量导出

## Goals / Non-Goals

**Goals:**
- 用户可按筛选条件导出 Excel 文件
- 导出流程安全可控（上限限制、二次确认）
- 生成标准格式 Excel 文件，方便后续使用

**Non-Goals:**
- 不支持自定义导出字段（固定导出全部字段）
- 不支持其他格式（如 CSV、PDF）
- 不支持异步导出（200 条以内同步处理）

## Decisions

### D1: Excel 库选型 → EasyExcel

| 方案 | 优点 | 缺点 |
|------|------|------|
| EasyExcel | 内存占用低、API简洁、阿里维护、中文文档 | 功能相对 POI 少 |
| Apache POI | 功能全面 | 大数据量易 OOM、API 繁琐 |

**结论**：选择 EasyExcel。数据量上限 200 条，两种库都能处理，但 EasyExcel API 更简洁、兼容性更好。

### D2: 导出上限 → 200 条

**理由**：
- 论文 PRD 预期规模约 1000 条，日常使用筛选后通常在 200 条以内
- 200 条以内同步导出，用户体验流畅
- 超出时提示用户缩小范围，避免长时间等待

**备选考虑**：不设上限，用户自行控制 → 但可能导致意外的大导出请求，影响服务稳定性。

### D3: 导出流程 → 先 count 再导出

```
用户点击导出 → 确认弹窗 → 禁用按钮
     ↓
调用 /api/record/export，后端先 count
     ↓
count > 200 → 返回错误提示，前端显示
count ≤ 200 → 查询数据、生成 Excel、返回文件流
```

**备选方案**：
- 单独 `/export-check` 接口 → 增加一次请求，但逻辑分离
- 在响应头返回 `X-Total-Count` → 需前端特殊处理

**结论**：采用单一接口方案，count > 200 时返回 JSON 错误响应，≤ 200 时返回 Excel 文件流。前端通过响应 Content-Type 判断处理方式。

### D4: 空值处理 → 占位符 "-"

| 字段 | 空值情况 | 处理方式 |
|------|----------|----------|
| batch_id | 单条输入时为 NULL | 显示 "-" |
| 其他字段 | 无空值 | 正常显示 |

### D5: 文件命名 → `分类记录_{日期}_{时间}.xlsx`

示例：`分类记录_2026-04-28_143052.xlsx`

**理由**：带时间戳便于区分多次导出的文件。

### D6: 前端下载 → axios + blob

```javascript
axios.get('/api/record/export', {
  params,
  responseType: 'blob'
}).then(res => {
  if (res.data.type === 'application/json') {
    // count > 200，返回 JSON 错误
    // 解析并显示提示
  } else {
    // 正常 Excel 流
    const blob = new Blob([res.data])
    const url = window.URL.createObjectURL(blob)
    // 创建 a 标签触发下载
  }
})
```

### D7: 按钮交互 → 二次确认 + 禁用

- 点击导出按钮 → 弹出 `el-confirm` 确认框
- 确认后 → 禁用按钮，显示 loading
- 完成/失败 → 恢复按钮状态

## Risks / Trade-offs

| 风险 | 影响 | 缓解措施 |
|------|------|----------|
| 用户不理解上限限制 | 困惑为什么不能导出 | 提示文案清晰："超过200条，请缩小筛选范围" |
| blob 响应类型判断 | JSON 和 Excel 混合响应需特殊处理 | 前端通过 `res.data.type` 判断处理逻辑 |
| 大量并发导出请求 | 服务压力 | 200 条上限限制单次开销；必要时可加接口限流 |

## Open Questions

- 无（决策已明确）