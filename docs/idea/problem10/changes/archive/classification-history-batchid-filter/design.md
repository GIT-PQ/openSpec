## Context

分类历史页面 (`ClassificationHistory.vue`) 已支持按预测类别、时间范围、来源类型、摘要关键字筛选。batchId 筛选功能仅通过 URL query 参数被动传递（批量分类跳转场景），前端无显式输入控件。

后端 MyBatis Mapper (`ClassificationRecordMapper.xml`) 已支持 batchId 等值匹配查询，无需后端改动。

## Goals / Non-Goals

**Goals:**
- 前端筛选区域新增 batchId 输入框
- 表格新增 batchId 列，完整显示 36 字符 UUID
- 空值显示 "-" 或空白

**Non-Goals:**
- 不改动后端代码
- 不新增 API 接口
- 不支持 batchId 模糊匹配

## Decisions

### D1: 筛选输入框位置

**Decision**: 放在"摘要关键字"输入框右侧，保持单行布局。

**Alternatives considered**:
- 独立一行: 筛选区域过长，视觉冗余
- 放在"来源类型"下方: 打破现有布局节奏

### D2: 表格列位置

**Decision**: 放在"来源"列之后，"分类时间"列之前。

**Alternatives considered**:
- 放在"摘要"列之后: 批次ID与摘要内容无直接关联
- 放在表格末尾: 位置偏后，用户不易发现

### D3: 空值显示策略

**Decision**: 显示 "-" 表示无批次ID。

**Alternatives considered**:
- 空白: 可能让用户困惑"是否有数据"
- "N/A": 英文表达，与中文界面不一致

## Risks / Trade-offs

- 表格新增列后宽度增加，小屏幕可能需要横向滚动 → 列宽度设为固定 280px，可容纳完整 UUID