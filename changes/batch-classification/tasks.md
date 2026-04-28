## 1. Java后端 - 依赖与基础

- [x] 1.1 pom.xml新增EasyExcel依赖（与步骤3导出共用）
- [x] 1.2 PatentService新增parseExcel方法，解析Excel返回列名列表和数据行

## 2. Java后端 - 文件预览接口

- [x] 2.1 PatentController新增uploadPreview方法，接收multipart/form-data
- [x] 2.2 uploadPreview调用parseExcel，返回columns、previewRows、totalRows
- [x] 2.3 处理文件格式错误、解析失败的异常响应

## 3. Java后端 - 批量分类接口

- [x] 3.1 PatentController新增batchClassify方法，接收file和summaryColumn参数
- [x] 3.2 batchClassify调用parseExcel提取指定摘要列数据
- [x] 3.3 生成batch_id（UUID）
- [x] 3.4 逐条调用Python /predict接口，收集结果
- [x] 3.5 失败条目记录到failedList，继续处理下一条
- [x] 3.6 成功结果调用RecordService.batchInsert批量存库
- [x] 3.7 返回batchId、total、success、failed、results、failedList

## 4. Java后端 - 批量插入服务

- [x] 4.1 RecordService新增batchInsert方法
- [x] 4.2 ClassificationRecordMapper新增批量插入SQL

## 5. 前端 - API接口

- [x] 5.1 api/index.js新增uploadPreview接口调用
- [x] 5.2 api/index.js新增batchClassify接口调用

## 6. 前端 - 批量分类页面

- [x] 6.1 新增BatchClassification.vue组件
- [x] 6.2 实现文件上传组件（支持拖拽和点击上传）
- [x] 6.3 上传后调用uploadPreview展示列名下拉和前5行预览
- [x] 6.4 实现摘要列下拉选择（默认"摘要"）
- [x] 6.5 点击"开始分类"调用batchClassify，展示"正在处理中"状态
- [x] 6.6 分类完成后展示结果摘要（成功数、失败数）
- [x] 6.7 实现"查看结果"按钮跳转历史页面（带batch_id参数）

## 7. 前端 - 路由与导航

- [x] 7.1 router/index.js新增/batch-classification路由
- [x] 7.2 App.vue导航栏新增"批量分类"菜单项
- [x] 7.3 HomeView.vue首页新增"批量分类"功能卡片

## 8. 前端 - 历史页面来源列修改

- [x] 8.1 ClassificationHistory.vue来源列显示逻辑修改
- [x] 8.2 批量记录显示"批量(batch_id)"
- [x] 8.3 详情弹窗显示批次ID字段

## 9. 测试验证

- [ ] 9.1 测试上传xlsx文件预览功能
- [ ] 9.2 测试上传csv文件预览功能
- [ ] 9.3 测试批量分类流程（全成功）
- [ ] 9.4 测试批量分类流程（部分失败）
- [ ] 9.5 测试历史页面批次ID筛选
- [ ] 9.6 测试来源列显示批次ID