## MODIFIED Requirements

### Requirement: 来源列显示分类来源及批次ID
系统SHALL在历史记录表格的来源列显示分类来源，批量记录显示"批量(批次ID)"，单条记录显示"单条输入"。

#### Scenario: 批量记录显示
- **WHEN** 分类记录的source字段为'batch'
- **THEN** 来源列显示"批量(batch_id)"，如"批量(uuid-abc123)"

#### Scenario: 单条记录显示
- **WHEN** 分类记录的source字段为'single'
- **THEN** 来源列显示"单条输入"