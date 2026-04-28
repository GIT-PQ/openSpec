## Why

分类历史页面缺少对 batchId 的显式筛选功能。用户目前只能通过 URL query 参数被动接收 batchId（从批量分类页面跳转），无法主动输入 batchId 进行查询。同时，表格中未显示完整的 batchId，用户无法直观识别批量分类的批次归属。

## What Changes

- 筛选区域新增 batchId 输入框，支持等值匹配查询
- 表格新增 batchId 列，完整显示 36 字符 UUID
- 单条分类记录的 batchId 列显示 "-" 表示空值

## Capabilities

### New Capabilities

- `batchid-column-display`: 表格新增批次ID列显示能力

### Modified Capabilities

- `record-query`: 扩展筛选条件支持 batchId 参数

## Impact

- **前端**: `ClassificationHistory.vue` 新增筛选输入框和表格列
- **后端**: 无需改动（MyBatis Mapper 已支持 batchId 等值匹配）
- **API**: 无新增接口，现有 `/api/record/list` 已支持 batchId 参数