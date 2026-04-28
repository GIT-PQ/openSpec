## Context

当前系统分类流程为纯透传代理：前端 → Java后端 → Python服务 → 返回结果，无任何持久化。每次分类结果仅在前端展示，刷新即丢失。现有技术栈为 Spring Boot 2.6.13 + MyBatis（XML映射）+ MySQL，实体/映射器/服务已有成熟模式（参见 User 模块）。前端请求拦截器已自动在所有请求头中附加 `Authorization: Bearer token_{userId}_{timestamp}`，后端 UserController 中已有从 token 解析 userId 的逻辑可复用。

## Goals / Non-Goals

**Goals:**
- 分类成功后自动将完整结果（摘要、预测类别、索引、置信度、22类概率分布、用户、时间、来源）写入数据库
- 从请求头 token 中提取 userId 关联到记录
- 存库失败不影响分类核心功能，仅记录日志
- 为后续步骤（历史展示、导出、批量分类）提供数据基础

**Non-Goals:**
- 不实现历史记录查询/展示/导出（步骤2、3的范围）
- 不实现批量分类（步骤4的范围）
- 不实现 ip_address 存储（无业务需求）
- 不修改 Python 服务和前端代码
- 不引入新的外部依赖

## Decisions

### 1. user_id 获取方式：复用 token 解析

**选择**：从 `Authorization: Bearer token_{userId}_{timestamp}` 中解析 userId

**备选方案**：
- A) 新增 JWT 鉴权：安全但改动大，超出步骤一范围
- B) 前端主动传 userId 参数：不安全，可伪造
- C) 复用现有 token 解析：零前端改动，与现有 getUserInfo 接口一致

**理由**：现有 token 格式虽简单，但系统当前无更高安全要求，复用可保持步骤一改动最小化。token 格式 `token_{userId}_{timestamp}`，解析 `parts[1]` 即得 userId。

### 2. 存库失败策略：静默失败 + 日志

**选择**：try-catch 包裹存库操作，异常仅 log.error，不向上抛出

**备选方案**：
- A) 存库失败返回 500：用户看到分类成功却报错，体验差
- B) 存库失败返回 500 并回滚：Python 已推理却告知失败，浪费计算
- C) 静默失败：分类是核心功能，持久化是附加能力

**理由**：用户首要需求是获取分类结果，历史记录是锦上添花。存库失败不应阻断主流程。

### 3. top_categories 存全部22类而非Top10

**选择**：存储 Python 返回的完整22个类别概率分布

**理由**：22条 JSON 约 1KB，存储成本可忽略；步骤二详情弹窗需展示完整概率分布图，存 Top10 会导致数据不完整。JSON 格式保留 `name`、`probability`、`index` 三个字段，与 Python 返回一致。

### 4. pred_probability 类型选择 double

**选择**：使用 MySQL `double` 类型

**备选方案**：
- A) `decimal(5,4)`：精度固定但范围受限（0.0000~0.9999），无法表示 1.0
- B) `decimal(6,5)`：范围略大但仍有限制
- C) `double`：浮点精度对概率值足够，无范围限制

**理由**：概率值为 0~1 的浮点数，`double` 精度完全满足，且避免 decimal 范围截断问题。

### 5. 存库时机：同步调用，在返回响应前

**选择**：在 PatentServiceImpl.classify() 中，Python 返回成功后、返回前端前，同步调用存库

**备选方案**：
- A) 异步存库（@Async / 消息队列）：解耦更好但增加复杂度，步骤一不需要
- B) 同步存库：简单直接，50ms 以内的数据库写入对总体响应时间（主要在模型推理 500ms+）影响可忽略

**理由**：步骤一追求最小改动，同步存库足够。后续如遇性能问题可优化为异步。

## Risks / Trade-offs

- **[Token 安全性]** → 当前 token 格式（`token_userId_timestamp`）可被伪造，无签名验证。这是系统现有问题，不在步骤一解决范围内。后续如需加固，应引入 JWT。
- **[数据库不可用导致记录丢失]** → 存库失败仅记日志，记录不可恢复。可接受：分类结果可重新生成，非唯一数据源。
- **[top_categories JSON 字段查询效率]** → MySQL JSON 类型在 5.7+ 支持良好，22条数据量极小，步骤二筛选基于 pred_label 等普通字段，不涉及 JSON 内部查询，无性能风险。