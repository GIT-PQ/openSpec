## ADDED Requirements

### Requirement: User can export filtered classification records

用户 SHALL 可以在分类历史页面将筛选后的记录导出为 Excel 文件。

#### Scenario: Export within limit
- **WHEN** 用户设置筛选条件后点击"导出Excel"按钮
- **AND** 符合条件的记录数量 ≤ 200 条
- **THEN** 系统弹出确认框，用户确认后下载 Excel 文件
- **AND** 文件名格式为 `分类记录_{日期}_{时间}.xlsx`

#### Scenario: Export exceeds limit
- **WHEN** 用户设置筛选条件后点击"导出Excel"按钮
- **AND** 符合条件的记录数量 > 200 条
- **THEN** 系统提示"超过200条，请缩小筛选范围"
- **AND** 不执行导出

#### Scenario: Export with no data
- **WHEN** 用户设置筛选条件后点击"导出Excel"按钮
- **AND** 符合条件的记录数量 = 0
- **THEN** 系统提示"暂无数据，请调整筛选条件"
- **AND** 不导出空文件

### Requirement: Export button requires confirmation and disables during export

导出按钮 SHALL 需要二次确认，导出期间禁用防止重复点击。

#### Scenario: Confirm before export
- **WHEN** 用户点击"导出Excel"按钮
- **THEN** 系统弹出确认框："确定导出当前筛选结果？"
- **AND** 用户可选择"确定"或"取消"

#### Scenario: Button disabled during export
- **WHEN** 用户确认导出
- **THEN** 导出按钮变为禁用状态
- **AND** 显示 loading 状态
- **AND** 导出完成后按钮恢复可用

### Requirement: Export only current user's records

导出 SHALL 仅包含当前登录用户自己的分类记录，从 token 中解析 userId 作为隐式过滤条件。

#### Scenario: User isolation
- **WHEN** 用户 A 导出分类记录
- **THEN** Excel 文件仅包含用户 A 的记录
- **AND** 不包含其他用户的记录

### Requirement: Excel file contains required fields with proper formatting

导出的 Excel 文件 SHALL 包含以下字段，格式正确。

#### Scenario: Excel fields format
- **WHEN** 导出成功
- **THEN** Excel 文件包含列：序号、专利摘要、预测类别、置信度、来源、批次ID、分类时间
- **AND** 置信度显示为百分比格式（如 85.23%）
- **AND** 来源显示为"单条输入"或"批量导入"
- **AND** 单条记录的批次ID显示占位符 "-"
- **AND** 分类时间格式为 yyyy-MM-dd HH:mm:ss

### Requirement: Export uses standard Excel MIME type and triggers download

导出响应 SHALL 使用标准 MIME type 并设置 Content-Disposition 触发浏览器下载。

#### Scenario: Response headers
- **WHEN** 导出成功
- **THEN** 响应 Content-Type 为 `application/vnd.openxmlformats-officedocument.spreadsheetml.sheet`
- **AND** 响应头包含 `Content-Disposition: attachment; filename=分类记录_xxx.xlsx`
- **AND** 浏览器触发文件下载而非直接打开