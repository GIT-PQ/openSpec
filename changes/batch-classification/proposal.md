## Why

论文评审指出系统功能完整性不足，缺少批量分类功能。实际业务中高频需要批量处理专利文本，当前系统仅支持单条分类，工程性较弱。

## What Changes

- 新增批量分类功能：支持上传Excel/CSV文件，批量提取专利摘要并执行分类推理
- 新增文件预览功能：上传后展示列名列表和前5行数据，用户选择摘要列
- 新增批次管理：批量分类结果关联同一batch_id，可在历史页面精确筛选
- 修改历史页面：来源列显示批次ID（如"批量(uuid-abc123)"）

## Capabilities

### New Capabilities
- `batch-classification`: 批量专利分类功能，包括文件上传、预览、分类处理、结果展示
- `file-preview`: Excel文件预览功能，返回列名和前N行数据

### Modified Capabilities
- `classification-history`: 来源列显示方式变更，批量记录需显示批次ID

## Impact

**Java后端**:
- 新增 `uploadPreview` 和 `batchClassify` 接口
- 新增 Excel解析逻辑（使用EasyExcel）
- 新增批量插入分类记录方法

**前端**:
- 新增 `BatchClassification.vue` 页面
- 修改 `ClassificationHistory.vue` 来源列显示逻辑
- 新增路由、导航菜单项、首页功能卡片

**数据库**:
- 无新表，使用现有 `classification_record` 表（source='batch', batch_id字段）

**Python服务**:
- 无改动，复用现有 `/predict` 单条推理接口