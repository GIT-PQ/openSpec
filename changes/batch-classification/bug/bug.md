# bug

## bug1

java后端启动失败

``` bash
[ERROR] COMPILATION ERROR :
[INFO] -------------------------------------------------------------
[ERROR] /D:/WorkSpace/JupyterWorkSpace/pq/app/zl-back-java/src/main/java/com/pq/zlbackjava/service/impl/PatentServiceImpl.java:[95,29] 名称冲突: <匿名com.pq.zlbackjava.service.impl.PatentServiceImpl$1>中的invokeHead(java.util.Map<java.lang.Integer,java.lang.String>,com.alibaba.excel.context.AnalysisContext)和com.alibaba.excel.event.AnalysisEventListener中的invokeHead(java.util.Map<java.lang.Integer,com.alibaba.excel.metadata.data.ReadCellData<?>>,com.alibaba.excel.context.AnalysisContext)具有相同疑符, 但两者均不覆盖对方
[ERROR] /D:/WorkSpace/JupyterWorkSpace/pq/app/zl-back-java/src/main/java/com/pq/zlbackjava/service.impl/PatentServiceImpl.java:[94,17] 方法不会覆盖或实现超类型的方法
[ERROR] /D:/WorkSpace/JupyterWorkSpace/pq/app/zl-back-java/src/main/java/com/pq/zlbackjava/service/impl/PatentServiceImpl.java:[145,29] 名称冲突: <匿名com.pq.zlbackjava.service.impl.PatentServiceImpl$2>中的invokeHead(java.util.Map<java.lang.Integer,java.lang.String>,com.alibaba.excel.context.AnalysisContext)和com.alibaba.excel.event.AnalysisEventListener中的invokeHead(java.util.Map<java.lang.Integer,com.alibaba.excel.metadata.data.ReadCellData<?>>,com.alibaba.excel.context.AnalysisContext)具有相同疑符, 但两者均不覆盖对方
[ERROR] /D:/WorkSpace/JupyterWorkSpace/pq/app/zl-back-java/src/main/java/com/pq/zlbackjava/service/impl/PatentServiceImpl.java:[144,17] 方法不会覆盖或实现超类型的方法
[INFO] 4 errors
[INFO] -------------------------------------------------------------
[INFO] ------------------------------------------------------------------------
[INFO] BUILD FAILURE
[INFO] ------------------------------------------------------------------------
[INFO] Total time:  4.879 s
[INFO] Finished at: 2026-04-28T22:31:34+08:00
[INFO] ------------------------------------------------------------------------
[ERROR] Failed to execute goal org.apache.maven.plugins:maven-compiler-plugin:3.8.1:compile (default-compile) on project zl-back-java: Compilation failure: Compilation failure:
[ERROR] /D:/WorkSpace/JupyterWorkSpace/pq/app/zl-back-java/src/main/java/com/pq/zlbackjava/service/impl/PatentServiceImpl.java:[95,29] 名称冲突: <匿名com.pq.zlbackjava.service.impl.PatentServiceImpl$1>中的invokeHead(java.util.Map<java.lang.Integer,java.lang.String>,com.alibaba.excel.context.AnalysisContext)和com.alibaba.excel.event.AnalysisEventListener中的invokeHead(java.util.Map<java.lang.Integer,com.alibaba.excel.metadata.data.ReadCellData<?>>,com.alibaba.excel.context.AnalysisContext)具有相同疑符, 但两者均不覆盖对方
[ERROR] /D:/WorkSpace/JupyterWorkSpace/pq/app/zl-back-java/src/main/java/com/pq/zlbackjava/service.impl/PatentServiceImpl.java:[94,17] 方法不会覆盖或实现超类型的方法
[ERROR] /D:/WorkSpace/JupyterWorkSpace/pq/app/zl-back-java/src/main/java/com/pq/zlbackjava/service/impl/PatentServiceImpl.java:[145,29] 名称冲突: <匿名com.pq.zlbackjava.service.impl.PatentServiceImpl$2>中的invokeHead(java.util.Map<java.lang.Integer,java.lang.String>,com.alibaba.excel.context.AnalysisContext)和com.alibaba.excel.event.AnalysisEventListener中的invokeHead(java.util.Map<java.lang.Integer,com.alibaba.excel.metadata.data.ReadCellData<?>>,com.alibaba.excel.context.AnalysisContext)具有相同疑符, 但两者均不覆盖对方
[ERROR] /D:/WorkSpace/JupyterWorkSpace/pq/app/zl-back-java/src/main/java/com/pq/zlbackjava/service/impl/PatentServiceImpl.java:[144,17] 方法不会覆盖或实现超类型的方法
[ERROR] -> [Help 1]
[ERROR]
[ERROR] To see the full stack trace of the errors, re-run Maven with the -e switch.
[ERROR] Re-run Maven using the -X switch to enable debug logging.
[ERROR]
[ERROR] For more information about the errors and possible solutions, please read the following articles:
[ERROR] [Help 1] http://cwiki.apache.org/confluence/display/MAVEN/MojoFailureException
```

### 原因分析

EasyExcel 3.x版本API变化：
- 旧版（2.x）：`invokeHead(Map<Integer, String> headMap, AnalysisContext context)`
- 新版（3.x）：`invokeHead(Map<Integer, ReadCellData<?>> headMap, AnalysisContext context)`

使用旧版API的方法签名在新版中无法正确覆盖父类方法，导致编译错误。

### 解决方案

EasyExcel 3.x提供了兼容方法 `invokeHeadMap`，专门用于处理字符串类型的表头：

**修改前**：
```java
@Override
public void invokeHead(Map<Integer, String> headMap, AnalysisContext context) {
    // ...
}
```

**修改后**：
```java
@Override
public void invokeHeadMap(Map<Integer, String> headMap, AnalysisContext context) {
    // ...
}
```

### 修改位置

`PatentServiceImpl.java` 中有两处需要修改：
1. `parseExcel` 方法中的监听器（约第95行）
2. `batchClassify` 方法中的监听器（约第145行）

### 状态

✅ 已修复
