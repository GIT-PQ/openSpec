## 1. 数据库

- [x] 1.1 创建 `classification_record` 建表SQL脚本（含 id, user_id, summary, pred_label, pred_index, pred_probability, top_categories, source, batch_id, create_time 字段，user_id 和 batch_id 建索引）
- [x] 1.2 在 MySQL `zl` 库中执行建表SQL，验证表结构正确

## 2. Java后端 - 实体与数据层

- [x] 2.1 创建 `ClassificationRecord` 实体类（com.pq.zlbackjava.entity.ClassificationRecord），使用 @Data 注解，字段与表结构对应，top_categories 映射为 String 类型
- [x] 2.2 创建 `ClassificationRecordMapper` 接口（com.pq.zlbackjava.mapper.ClassificationRecordMapper），定义 insert 方法
- [x] 2.3 创建 `ClassificationRecordMapper.xml` 映射文件（resources/mapper/ClassificationRecordMapper.xml），编写 insert SQL（含 resultMap）

## 3. Java后端 - 服务层

- [x] 3.1 创建 `ClassificationRecordService` 接口（com.pq.zlbackjava.service.ClassificationRecordService），定义 save 方法
- [x] 3.2 创建 `ClassificationRecordServiceImpl` 实现类，注入 ClassificationRecordMapper，实现 save 方法，将 Python 返回的 categories 列表序列化为 JSON 字符串存入 top_categories

## 4. Java后端 - 控制器与服务集成

- [x] 4.1 修改 `PatentController.classify()` 方法，从 `@RequestHeader("Authorization")` 中解析 userId（复用 UserController 中 token 解析逻辑），token 缺失或无效时 userId 设为 0，将 userId 传入 service
- [x] 4.2 修改 `PatentServiceImpl.classify()` 方法签名，接收 userId 参数；在 Python 返回成功（code=200）后，构造 ClassificationRecord 对象并调用 recordService.save()，用 try-catch 包裹存库操作，异常仅 log.error 不向上抛出

## 5. 验证

- [x] 5.1 启动全栈服务，执行单条专利分类，验证 classification_record 表中自动新增记录，字段内容完整（含全部22类概率分布）
- [x] 5.2 验证未登录（无 token）时分类仍正常执行，记录中 user_id 为 0
- [x] 5.3 验证 Python 服务返回错误时不产生记录
- [x] 5.4 模拟数据库不可用（如停 MySQL），验证分类功能仍正常返回结果，后端日志记录存库失败错误