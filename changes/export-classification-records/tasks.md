## 1. 后端依赖与基础设施

- [ ] 1.1 在 pom.xml 中添加 EasyExcel 依赖
- [ ] 1.2 创建 Excel 导出实体类 `ClassificationRecordExcelVO`（字段映射、置信度格式化、空值处理）

## 2. 后端 Mapper 层

- [ ] 2.1 在 `ClassificationRecordMapper.java` 中新增 `countByCondition` 方法
- [ ] 2.2 在 `ClassificationRecordMapper.xml` 中新增 count 查询 SQL（复用现有筛选条件）

## 3. 后端 Service 层

- [ ] 3.1 在 `RecordService.java` 接口中新增 `countByCondition` 和 `queryAll` 方法声明
- [ ] 3.2 在 `RecordServiceImpl.java` 中实现 `countByCondition` 方法
- [ ] 3.3 在 `RecordServiceImpl.java` 中实现 `queryAll` 方法（全量查询，带筛选条件）

## 4. 后端 Controller 层

- [ ] 4.1 在 `RecordController.java` 中新增 `export` 方法
- [ ] 4.2 实现导出逻辑：先 count 判断，> 200 返回 JSON 错误，≤ 200 生成 Excel 返回文件流
- [ ] 4.3 设置正确的响应头（Content-Type、Content-Disposition）

## 5. 前端 API 层

- [ ] 5.1 在 `api/index.js` 中新增 `recordApi.export` 方法（responseType: 'blob'）

## 6. 前端页面改造

- [ ] 6.1 在 `ClassificationHistory.vue` 筛选区域新增"导出Excel"按钮
- [ ] 6.2 实现点击导出按钮弹出确认框（使用 `this.$confirm`）
- [ ] 6.3 实现导出期间按钮禁用和 loading 状态
- [ ] 6.4 实现导出逻辑：调用 export 接口，判断响应类型处理
- [ ] 6.5 实现 Excel 文件下载（createObjectURL + a 标签触发）
- [ ] 6.6 实现超过 200 条提示逻辑（解析 JSON 响应并显示提示）
- [ ] 6.7 实现无数据提示逻辑

## 7. 测试验证

- [ ] 7.1 测试正常导出（筛选条件有效，记录 ≤ 200）
- [ ] 7.2 测试超过 200 条导出（显示提示，不下载）
- [ ] 7.3 测试无数据导出（显示提示，不下载）
- [ ] 7.4 测试二次确认交互
- [ ] 7.5 测试导出期间按钮禁用
- [ ] 7.6 测试 Excel 文件字段格式正确（置信度百分比、来源中文、批次ID空值显示 "-"）
- [ ] 7.7 测试文件名格式正确（分类记录_日期_时间.xlsx）
- [ ] 7.8 测试用户数据隔离（仅导出当前用户记录）