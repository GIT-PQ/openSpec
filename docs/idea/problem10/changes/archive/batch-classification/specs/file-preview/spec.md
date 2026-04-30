## ADDED Requirements

### Requirement: 文件预览接口返回列名和前5行数据
系统SHALL提供 `/api/patent/upload-preview` 接口，解析上传的Excel文件并返回列名列表和前5行预览数据。

#### Scenario: 成功预览
- **WHEN** 用户上传有效Excel文件调用预览接口
- **THEN** 系统返回列名列表、前5行数据、总行数

#### Scenario: 文件解析失败
- **WHEN** 用户上传损坏或格式错误的文件
- **THEN** 系统返回错误提示"文件解析失败"

### Requirement: 预览数据用于摘要列选择
系统SHALL将预览返回的列名列表展示为下拉选项，供用户选择摘要列。

#### Scenario: 展示列名下拉
- **WHEN** 预览接口返回列名列表
- **THEN** 前端下拉框展示所有列名选项

#### Scenario: 默认选择
- **WHEN** 列名列表中包含"摘要"列名
- **THEN** 默认选中"摘要"列（如有）