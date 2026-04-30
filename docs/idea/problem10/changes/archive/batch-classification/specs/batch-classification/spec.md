## ADDED Requirements

### Requirement: 用户可上传Excel/CSV文件进行批量分类
系统SHALL支持上传 `.xlsx`、`.xls`、`.csv` 格式文件，批量提取专利摘要并执行分类推理。

#### Scenario: 上传有效Excel文件
- **WHEN** 用户上传包含专利摘要的Excel文件
- **THEN** 系统解析文件并返回列名列表和预览数据

#### Scenario: 上传无效格式文件
- **WHEN** 用户上传非Excel/CSV格式文件
- **THEN** 系统返回错误提示"文件格式不支持，仅支持.xlsx/.xls/.csv"

#### Scenario: 上传超过50条记录
- **WHEN** 用户上传包含超过50条记录的文件
- **THEN** 系统返回错误提示"单次最多处理50条，请拆分文件"

### Requirement: 用户可选择摘要列名
系统SHALL在文件预览后提供列名下拉列表，让用户选择摘要列。

#### Scenario: 选择摘要列
- **WHEN** 用户从下拉列表选择某一列作为摘要列
- **THEN** 系统记录选择的列名，用于后续分类

#### Scenario: 摘要列数据为空
- **WHEN** 用户选择的摘要列中某些行数据为空
- **THEN** 系统跳过空行，不产生分类记录，返回在failedList中

### Requirement: 批量分类结果存入数据库
系统SHALL将成功的分类结果存入 `classification_record` 表，source字段值为'batch'，关联同一batch_id。

#### Scenario: 成功分类存库
- **WHEN** Python推理返回有效结果
- **THEN** 系统将结果存入数据库，包含batch_id、摘要、预测类别、置信度等字段

#### Scenario: 失败分类不存库
- **WHEN** Python推理失败（超时、异常）
- **THEN** 系统不存入数据库，将失败信息记录在响应的failedList中

### Requirement: 分类完成后可跳转历史页面
系统SHALL在分类完成后提供跳转链接，按batch_id精确筛选当前批次记录。

#### Scenario: 查看当前批次结果
- **WHEN** 用户点击"查看结果"按钮
- **THEN** 系统跳转到历史页面，自动筛选batch_id参数

### Requirement: 前端展示处理状态
系统SHALL在分类处理期间展示"正在处理中"状态，按钮禁用防止重复提交。

#### Scenario: 处理中状态
- **WHEN** 用户点击"开始分类"后端开始处理
- **THEN** 前端展示"正在处理中，请稍候..."，按钮禁用

#### Scenario: 处理完成
- **WHEN** 后端返回分类结果
- **THEN** 前端展示结果摘要（成功数、失败数），恢复按钮状态