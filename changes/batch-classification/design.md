## Context

当前系统仅支持单条专利分类，用户逐条输入摘要文本调用Python推理服务。批量分类需求来自论文评审反馈，实际业务场景中高频需要批量处理专利文本。

现有架构：
- 前端Vue 2 + Element UI
- Java Spring Boot后端处理用户认证，代理转发到Python Flask
- Python Flask提供单条推理接口 `/predict`
- MySQL存储分类记录

约束：
- 复用现有 `/predict` 接口，不新增Python批量推理接口
- 50条以内的规模，逐条调用延迟可接受
- 不引入前端Excel解析库，由后端统一处理

## Goals / Non-Goals

**Goals:**
- 支持上传Excel/CSV文件批量分类
- 用户可选择摘要列名
- 分类结果存库并可在历史页面筛选查看
- 单条失败不影响整体流程

**Non-Goals:**
- 不实现实时进度条（同步等待）
- 不实现Python端批量推理接口
- 不支持并发推理

## Decisions

### D1: 进度反馈机制
**Decision**: 同步等待，前端展示"正在处理中"状态
**Alternatives Considered**:
- 轮询进度：需要新增进度存储，增加复杂度
- WebSocket推送：改动量大，需要建立WebSocket连接
**Rationale**: 50条处理时间预估25-100秒，同步等待用户体验可接受，实现最简单

### D2: 错误处理策略
**Decision**: 继续处理，失败条目不存库，返回failedList
**Alternatives Considered**:
- 立即中断：已成功条目浪费，用户需重新上传
- 存库标记失败：增加表字段，失败记录与成功记录混在一起
**Rationale**: 用户一次上传尽可能产生有效结果，失败信息在响应中返回供用户修正

### D3: 文件预览实现
**Decision**: 后端解析，新增upload-preview接口
**Alternatives Considered**:
- 前端解析：引入xlsx.js依赖，增加包体积
**Rationale**: 后端解析逻辑与batchClassify共用，前端无需引入新依赖

### D4: 来源列显示
**Decision**: 批量记录显示"批量(批次ID)"
**Alternatives Considered**:
- 只显示"批量"，不显示批次ID
- 详情弹窗显示批次ID
**Rationale**: 用户可直接在表格中识别批次，便于区分不同批次

## Risks / Trade-offs

| Risk | Mitigation |
|------|------------|
| 50条同步等待时间较长（CPU环境约100秒） | 提示用户"正在处理中，请稍候"，按钮禁用防止重复提交 |
| 摘要列名不匹配（用户文件列名与预期不同） | 提供列名下拉选择，不做智能匹配，让用户手动选择 |
| 大文件上传内存占用 | 限制文件大小5MB，单次最多50条 |