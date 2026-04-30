## Why

论文评审指出系统功能完整性不足，未支持结果导出等实际业务高频需求。用户在查看分类历史后，无法将筛选结果导出为 Excel 文件，限制了数据的二次分析和汇报用途。步骤1、2已完成持久化和历史展示，现在需要补齐导出能力，形成完整的数据闭环。

## What Changes

- 新增条件导出功能：用户可在历史页面按筛选条件导出 Excel 文件
- 导出上限限制：单次最多导出 200 条，超出提示用户缩小范围
- 二次确认交互：点击导出按钮需确认，导出期间按钮禁用
- 标准文件格式：使用 EasyExcel 生成 `.xlsx` 文件，正确 MIME type + Content-Disposition
- 空值处理：单条记录的 batch_id 显示占位符 "-"

## Capabilities

### New Capabilities

- `record-export`: 分类记录条件导出功能，支持按预测类别、时间范围、来源、摘要关键字筛选后导出 Excel 文件

### Modified Capabilities

- 无（导出是新功能，不修改现有能力的需求）

## Impact

| 层 | 改动点 | 说明 |
|----|--------|------|
| Java后端 | pom.xml | 新增 EasyExcel 依赖 |
| Java后端 | RecordController | 新增 export 方法，处理导出请求 |
| Java后端 | RecordService | 新增 countByCondition 和 queryAll 方法 |
| Java后端 | ClassificationRecordMapper | 新增 count 和全量查询 SQL |
| 前端 | ClassificationHistory.vue | 新增导出按钮、确认弹窗、下载逻辑 |
| 前端 | api/index.js | 新增导出相关接口 |