## Why

论文评审指出系统"仅实现单条专利文本分类，功能完整性不足"。当前分类结果仅返回前端展示，未做任何持久化，导致后续的历史记录查询、结果导出、批量分类汇总等功能无法实现。分类结果持久化是所有后续功能（历史展示、导出、批量分类）的数据基础，必须首先落地。

## What Changes

- 新增 `classification_record` 数据库表，存储每次分类的完整结果（输入摘要、预测类别、类别索引、置信度、全量22类概率分布、来源、批次ID、操作用户、时间）
- Java后端新增 `ClassificationRecord` 实体、Mapper、Service，实现分类结果的自动存库
- 修改 `PatentController.classify()` 从请求头 `Authorization` 中解析 userId，传入 service 层
- 修改 `PatentServiceImpl.classify()` 在分类成功后尝试存库，存库失败仅记日志不影响用户获取分类结果
- Python服务和前端无改动（前端请求拦截器已自动带 token）

## Capabilities

### New Capabilities
- `classification-record-persistence`: 分类结果自动持久化能力，包括数据库表设计、实体映射、存库逻辑、用户身份关联、存库失败容错

### Modified Capabilities
<!-- 无现有 spec 需要修改 -->

## Impact

- **数据库**: 新增 `classification_record` 表（MySQL，zl 库）
- **Java后端**: 新增3个文件（Entity、Mapper接口、Mapper XML、Service），修改2个文件（PatentController、PatentServiceImpl）
- **API行为**: `/api/patent/classify` 接口行为不变（响应格式不变），新增副作用（分类成功后自动存库）
- **依赖**: 无新增外部依赖，使用现有 MyBatis + MySQL 基础设施