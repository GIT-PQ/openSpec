# bug

## bug1
第一次点击详情不展示echart，但第二次及之后点击详情才展示echart
```
Uncaught (in promise) Error: A listener indicated an asynchronous response by returning true, but the message channel closed before a response was received
```

## bug2
摘要关键词查询其实就是作为like查询的，但是后端报错了。其他筛选条件都正常。

## bug3
预测类别 下拉框内容映射错误

```bash
2026-04-28 21:00:54.613 ERROR 28448 --- [nio-8081-exec-8] o.a.c.c.C.[.[.[/].[dispatcherServlet]    : Servlet.service() for servlet [dispatcherServlet] in context with path [] threw exception [Request processing failed; nested exception is org.mybatis.spring.MyBatisSystemException: nested exception is org.apache.ibatis.exceptions.PersistenceException:
### Error querying database.  Cause: java.lang.NumberFormatException: For input string: "\%"
### Cause: java.lang.NumberFormatException: For input string: "\%"] with root cause

java.lang.NumberFormatException: For input string: "\%"
        at java.lang.NumberFormatException.forInputString(NumberFormatException.java:65) ~[na:1.8.0_381]
        at java.lang.Long.parseLong(Long.java:589) ~[na:1.8.0_381]
        at java.lang.Long.parseLong(Long.java:631) ~[na:1.8.0_381]
        at org.apache.ibatis.ognl.OgnlOps.longValue(OgnlOps.java:231) ~[mybatis-3.5.9.jar:3.5.9]
        at org.apache.ibatis.ognl.OgnlOps.convertValue(OgnlOps.java:605) ~[mybatis-3.5.9.jar:3.5.9]
        at org.apache.ibatis.ognl.OgnlOps.convertValue(OgnlOps.java:522) ~[mybatis-3.5.9.jar:3.5.9]
        at org.apache.ibatis.ognl.DefaultTypeConverter.convertValue(DefaultTypeConverter.java:50) ~[mybatis-3.5.9.jar:3.5.9]
        at org.apache.ibatis.ognl.DefaultTypeConverter.convertValue(DefaultTypeConverter.java:55) ~[mybatis-3.5.9.jar:3.5.9]
        at org.apache.ibatis.ognl.OgnlRuntime.getConvertedType(OgnlRuntime.java:1617) ~[mybatis-3.5.9.jar:3.5.9]
        at org.apache.ibatis.ognl.OgnlRuntime.getConvertedTypes(OgnlRuntime.java:1634) ~[mybatis-3.5.9.jar:3.5.9]
        at org.apache.ibatis.ognl.OgnlRuntime.getConvertedMethodAndArgs(OgnlRuntime.java:1733) ~[mybatis-3.5.9.jar:3.5.9]
        at org.apache.ibatis.ognl.OgnlRuntime.getAppropriateMethod(OgnlRuntime.java:1717) ~[mybatis-3.5.9.jar:3.5.9]
        at org.apache.ibatis.ognl.OgnlRuntime.callAppropriateMethod(OgnlRuntime.java:1882) ~[mybatis-3.5.9.jar:3.5.9]
        at org.apache.ibatis.ognl.ObjectMethodAccessor.callMethod(ObjectMethodAccessor.java:68) ~[mybatis-3.5.9.jar:3.5.9]
        at org.apache.ibatis.ognl.OgnlRuntime.callMethod(OgnlRuntime.java:2038) ~[mybatis-3.5.9.jar:3.5.9]
        at org.apache.ibatis.ognl.ASTMethod.getValueBody(ASTMethod.java:97) ~[mybatis-3.5.9.jar:3.5.9]
        at org.apache.ibatis.ognl.SimpleNode.evaluateGetValueBody(SimpleNode.java:212) ~[mybatis-3.5.9.jar:3.5.9]
        at org.apache.ibatis.ognl.SimpleNode.getValue(SimpleNode.java:258) ~[mybatis-3.5.9.jar:3.5.9]
        at org.apache.ibatis.ognl.ASTChain.getValueBody(ASTChain.java:141) ~[mybatis-3.5.9.jar:3.5.9]
        at org.apache.ibatis.ognl.SimpleNode.evaluateGetValueBody(SimpleNode.java:212) ~[mybatis-3.5.9.jar:3.5.9]
        at org.apache.ibatis.ognl.SimpleNode.getValue(SimpleNode.java:258) ~[mybatis-3.5.9.jar:3.5.9]
        at org.apache.ibatis.ognl.Ognl.getValue(Ognl.java:586) ~[mybatis-3.5.9.jar:3.5.9]
        at org.apache.ibatis.ognl.Ognl.getValue(Ognl.java:550) ~[mybatis-3.5.9.jar:3.5.9]
        at org.apache.ibatis.scripting.xmltags.OgnlCache.getValue(OgnlCache.java:46) ~[mybatis-3.5.9.jar:3.5.9]
        at org.apache.ibatis.scripting.xmltags.VarDeclSqlNode.apply(VarDeclSqlNode.java:33) ~[mybatis-3.5.9.jar:3.5.9]
        at org.apache.ibatis.scripting.xmltags.MixedSqlNode.lambda$apply$0(MixedSqlNode.java:32) ~[mybatis-3.5.9.jar:3.5.9]
        at java.util.ArrayList.forEach(ArrayList.java:1259) ~[na:1.8.0_381]
        at org.apache.ibatis.scripting.xmltags.MixedSqlNode.apply(MixedSqlNode.java:32) ~[mybatis-3.5.9.jar:3.5.9]
        at org.apache.ibatis.scripting.xmltags.IfSqlNode.apply(IfSqlNode.java:35) ~[mybatis-3.5.9.jar:3.5.9]
        at org.apache.ibatis.scripting.xmltags.MixedSqlNode.lambda$apply$0(MixedSqlNode.java:32) ~[mybatis-3.5.9.jar:3.5.9]
        at java.util.ArrayList.forEach(ArrayList.java:1259) ~[na:1.8.0_381]
        at org.apache.ibatis.scripting.xmltags.MixedSqlNode.apply(MixedSqlNode.java:32) ~[mybatis-3.5.9.jar:3.5.9]
        at org.apache.ibatis.scripting.xmltags.DynamicSqlSource.getBoundSql(DynamicSqlSource.java:39) ~[mybatis-3.5.9.jar:3.5.9]
        at org.apache.ibatis.mapping.MappedStatement.getBoundSql(MappedStatement.java:305) ~[mybatis-3.5.9.jar:3.5.9]
        at org.apache.ibatis.executor.CachingExecutor.query(CachingExecutor.java:87) ~[mybatis-3.5.9.jar:3.5.9]
        at org.apache.ibatis.session.defaults.DefaultSqlSession.selectList(DefaultSqlSession.java:151) ~[mybatis-3.5.9.jar:3.5.9]
        at org.apache.ibatis.session.defaults.DefaultSqlSession.selectList(DefaultSqlSession.java:145) ~[mybatis-3.5.9.jar:3.5.9]
        at org.apache.ibatis.session.defaults.DefaultSqlSession.selectList(DefaultSqlSession.java:140) ~[mybatis-3.5.9.jar:3.5.9]
        at sun.reflect.NativeMethodAccessorImpl.invoke0(Native Method) ~[na:1.8.0_381]
        at sun.reflect.NativeMethodAccessorImpl.invoke(NativeMethodAccessorImpl.java:62) ~[na:1.8.0_381]
        at sun.reflect.DelegatingMethodAccessorImpl.invoke(DelegatingMethodAccessorImpl.java:43) ~[na:1.8.0_381]
        at java.lang.reflect.Method.invoke(Method.java:498) ~[na:1.8.0_381]
        at org.mybatis.spring.SqlSessionTemplate$SqlSessionInterceptor.invoke(SqlSessionTemplate.java:427) ~[mybatis-spring-2.0.7.jar:2.0.7]
        at com.sun.proxy.$Proxy57.selectList(Unknown Source) ~[na:na]
        at org.mybatis.spring.SqlSessionTemplate.selectList(SqlSessionTemplate.java:224) ~[mybatis-spring-2.0.7.jar:2.0.7]
        at org.apache.ibatis.binding.MapperMethod.executeForMany(MapperMethod.java:147) ~[mybatis-3.5.9.jar:3.5.9]
        at org.apache.ibatis.binding.MapperMethod.execute(MapperMethod.java:80) ~[mybatis-3.5.9.jar:3.5.9]
        at org.apache.ibatis.binding.MapperProxy$PlainMethodInvoker.invoke(MapperProxy.java:145) ~[mybatis-3.5.9.jar:3.5.9]
        at org.apache.ibatis.binding.MapperProxy.invoke(MapperProxy.java:86) ~[mybatis-3.5.9.jar:3.5.9]
        at com.sun.proxy.$Proxy58.selectByCondition(Unknown Source) ~[na:na]
        at com.pq.zlbackjava.service.impl.RecordServiceImpl.listByCondition(RecordServiceImpl.java:19) ~[classes/:na]
        at com.pq.zlbackjava.controller.RecordController.list(RecordController.java:31) ~[classes/:na]
        at sun.reflect.NativeMethodAccessorImpl.invoke0(Native Method) ~[na:1.8.0_381]
        at sun.reflect.NativeMethodAccessorImpl.invoke(NativeMethodAccessorImpl.java:62) ~[na:1.8.0_381]
        at sun.reflect.DelegatingMethodAccessorImpl.invoke(DelegatingMethodAccessorImpl.java:43) ~[na:1.8.0_381]
        at java.lang.reflect.Method.invoke(Method.java:498) ~[na:1.8.0_381]
        at org.springframework.web.method.support.InvocableHandlerMethod.doInvoke(InvocableHandlerMethod.java:205) ~[spring-web-5.3.23.jar:5.3.23]
        at org.springframework.web.method.support.InvocableHandlerMethod.invokeForRequest(InvocableHandlerMethod.java:150) ~[spring-web-5.3.23.jar:5.3.23]
        at org.springframework.web.servlet.mvc.method.annotation.ServletInvocableHandlerMethod.invokeAndHandle(ServletInvocableHandlerMethod.java:117) ~[spring-webmvc-5.3.23.jar:5.3.23]
        at org.springframework.web.servlet.mvc.method.annotation.RequestMappingHandlerAdapter.invokeHandlerMethod(RequestMappingHandlerAdapter.java:895) ~[spring-webmvc-5.3.23.jar:5.3.23]
        at org.springframework.web.servlet.mvc.method.annotation.RequestMappingHandlerAdapter.handleInternal(RequestMappingHandlerAdapter.java:808) ~[spring-webmvc-5.3.23.jar:5.3.23]
        at org.springframework.web.servlet.mvc.method.AbstractHandlerMethodAdapter.handle(AbstractHandlerMethodAdapter.java:87) ~[spring-webmvc-5.3.23.jar:5.3.23]
        at org.springframework.web.servlet.DispatcherServlet.doDispatch(DispatcherServlet.java:1071) ~[spring-webmvc-5.3.23.jar:5.3.23]
        at org.springframework.web.servlet.DispatcherServlet.doService(DispatcherServlet.java:964) ~[spring-webmvc-5.3.23.jar:5.3.23]
        at org.springframework.web.servlet.FrameworkServlet.processRequest(FrameworkServlet.java:1006) ~[spring-webmvc-5.3.23.jar:5.3.23]
        at org.springframework.web.servlet.FrameworkServlet.doGet(FrameworkServlet.java:898) ~[spring-webmvc-5.3.23.jar:5.3.23]
        at javax.servlet.http.HttpServlet.service(HttpServlet.java:670) ~[tomcat-embed-core-9.0.68.jar:4.0.FR]
        at org.springframework.web.servlet.FrameworkServlet.service(FrameworkServlet.java:883) ~[spring-webmvc-5.3.23.jar:5.3.23]
        at javax.servlet.http.HttpServlet.service(HttpServlet.java:779) ~[tomcat-embed-core-9.0.68.jar:4.0.FR]
        at org.apache.catalina.core.ApplicationFilterChain.internalDoFilter(ApplicationFilterChain.java:227) ~[tomcat-embed-core-9.0.68.jar:9.0.68]
        at org.apache.catalina.core.ApplicationFilterChain.doFilter(ApplicationFilterChain.java:162) ~[tomcat-embed-core-9.0.68.jar:9.0.68]
        at org.apache.tomcat.websocket.server.WsFilter.doFilter(WsFilter.java:53) ~[tomcat-embed-websocket-9.0.68.jar:9.0.68]
        at org.apache.catalina.core.ApplicationFilterChain.internalDoFilter(ApplicationFilterChain.java:189) ~[tomcat-embed-core-9.0.68.jar:9.0.68]
        at org.apache.catalina.core.ApplicationFilterChain.doFilter(ApplicationFilterChain.java:162) ~[tomcat-embed-core-9.0.68.jar:9.0.68]
        at org.springframework.web.filter.RequestContextFilter.doFilterInternal(RequestContextFilter.java:100) ~[spring-web-5.3.23.jar:5.3.23]
        at org.springframework.web.filter.OncePerRequestFilter.doFilter(OncePerRequestFilter.java:117) ~[spring-web-5.3.23.jar:5.3.23]
        at org.apache.catalina.core.ApplicationFilterChain.internalDoFilter(ApplicationFilterChain.java:189) ~[tomcat-embed-core-9.0.68.jar:9.0.68]
        at org.apache.catalina.core.ApplicationFilterChain.doFilter(ApplicationFilterChain.java:162) ~[tomcat-embed-core-9.0.68.jar:9.0.68]
        at org.springframework.web.filter.FormContentFilter.doFilterInternal(FormContentFilter.java:93) ~[spring-web-5.3.23.jar:5.3.23]
        at org.springframework.web.filter.OncePerRequestFilter.doFilter(OncePerRequestFilter.java:117) ~[spring-web-5.3.23.jar:5.3.23]
        at org.apache.catalina.core.ApplicationFilterChain.internalDoFilter(ApplicationFilterChain.java:189) ~[tomcat-embed-core-9.0.68.jar:9.0.68]
        at org.apache.catalina.core.ApplicationFilterChain.doFilter(ApplicationFilterChain.java:162) ~[tomcat-embed-core-9.0.68.jar:9.0.68]
        at org.springframework.web.filter.CharacterEncodingFilter.doFilterInternal(CharacterEncodingFilter.java:201) ~[spring-web-5.3.23.jar:5.3.23]
        at org.springframework.web.filter.OncePerRequestFilter.doFilter(OncePerRequestFilter.java:117) ~[spring-web-5.3.23.jar:5.3.23]
        at org.apache.catalina.core.ApplicationFilterChain.internalDoFilter(ApplicationFilterChain.java:189) ~[tomcat-embed-core-9.0.68.jar:9.0.68]
        at org.apache.catalina.core.ApplicationFilterChain.doFilter(ApplicationFilterChain.java:162) ~[tomcat-embed-core-9.0.68.jar:9.0.68]
        at org.apache.catalina.core.StandardWrapperValve.invoke(StandardWrapperValve.java:197) ~[tomcat-embed-core-9.0.68.jar:9.0.68]
        at org.apache.catalina.core.StandardContextValve.invoke(StandardContextValve.java:97) [tomcat-embed-core-9.0.68.jar:9.0.68]
        at org.apache.catalina.authenticator.AuthenticatorBase.invoke(AuthenticatorBase.java:541) [tomcat-embed-core-9.0.68.jar:9.0.68]
        at org.apache.catalina.core.StandardHostValve.invoke(StandardHostValve.java:135) [tomcat-embed-core-9.0.68.jar:9.0.68]
        at org.apache.catalina.valves.ErrorReportValve.invoke(ErrorReportValve.java:92) [tomcat-embed-core-9.0.68.jar:9.0.68]
        at org.apache.catalina.core.StandardEngineValve.invoke(StandardEngineValve.java:78) [tomcat-embed-core-9.0.68.jar:9.0.68]
        at org.apache.catalina.connector.CoyoteAdapter.service(CoyoteAdapter.java:360) [tomcat-embed-core-9.0.68.jar:9.0.68]
        at org.apache.coyote.http11.Http11Processor.service(Http11Processor.java:399) [tomcat-embed-core-9.0.68.jar:9.0.68]
        at org.apache.coyote.AbstractProcessorLight.process(AbstractProcessorLight.java:65) [tomcat-embed-core-9.0.68.jar:9.0.68]
        at org.apache.coyote.AbstractProtocol$ConnectionHandler.process(AbstractProtocol.java:893) [tomcat-embed-core-9.0.68.jar:9.0.68]
        at org.apache.tomcat.util.net.NioEndpoint$SocketProcessor.doRun(NioEndpoint.java:1789) [tomcat-embed-core-9.0.68.jar:9.0.68]
        at org.apache.tomcat.util.net.SocketProcessorBase.run(SocketProcessorBase.java:49) [tomcat-embed-core-9.0.68.jar:9.0.68]
        at org.apache.tomcat.util.threads.ThreadPoolExecutor.runWorker(ThreadPoolExecutor.java:1191) [tomcat-embed-core-9.0.68.jar:9.0.68]
        at org.apache.tomcat.util.threads.ThreadPoolExecutor$Worker.run(ThreadPoolExecutor.java:659) [tomcat-embed-core-9.0.68.jar:9.0.68]
        at org.apache.tomcat.util.threads.TaskThread$WrappingRunnable.run(TaskThread.java:61) [tomcat-embed-core-9.0.68.jar:9.0.68]
        at java.lang.Thread.run(Thread.java:750) [na:1.8.0_381]
```

---

## Bug1 分析与修复

### 原因

弹窗首次打开时，执行顺序如下：
1. `showDetail()` 先设置 `detailCategories` 数据
2. 再设置 `detailVisible = true` 打开弹窗
3. `ChartVisualization` 的 watch 立即触发 `renderChart()`
4. 但此时 el-dialog 的 DOM 还在动画渲染中，`$refs.chart` 不存在
5. ECharts 无法初始化，图表不显示

第二次点击时，弹窗 DOM 已存在于页面（只是隐藏状态），`$refs.chart` 已存在，所以图表正常显示。

### 修复方案

使用 el-dialog 的 `@opened` 事件，在弹窗完全打开后再触发图表渲染。

**修改 `ClassificationHistory.vue`**：

1. 弹窗添加 `@opened` 事件：
```vue
<el-dialog title="分类详情" :visible.sync="detailVisible" width="60%" @opened="onDialogOpened">
```

2. 给 ChartVisualization 添加 ref：
```vue
<ChartVisualization
  ref="detailChart"
  v-if="detailCategories.length > 0"
  :categories="detailCategories"
  height="400px"
/>
```

3. 修改 `showDetail` 方法（先打开弹窗）：
```javascript
showDetail (row) {
  this.detailRecord = row
  this.detailVisible = true  // 先打开弹窗，数据在 opened 事件中处理
}
```

4. 新增 `onDialogOpened` 方法：
```javascript
onDialogOpened () {
  // 弹窗完全打开后，解析数据并刷新图表
  try {
    this.detailCategories = JSON.parse(this.detailRecord.topCategories || '[]')
  } catch (e) {
    this.detailCategories = []
  }
  this.$nextTick(() => {
    if (this.$refs.detailChart) {
      this.$refs.detailChart.renderChart()
    }
  })
}
```

---

## Bug2 分析与修复

### 原因

`<bind>` 标签中的 OGNL 表达式：
```xml
<bind name="escapedSummary" value="summary.replace('%', '\%').replace('_', '\_')" />
```

OGNL 解析器将 `'\%'` 中的反斜杠误解为类型转换操作，尝试将 `\%` 解析为数值，导致 `NumberFormatException: For input string: "\%"`。

### 修复方案

在 Java Service 层处理 LIKE 通配符转义，不依赖 MyBatis `<bind>` 的 OGNL 表达式。

**修改 `RecordServiceImpl.java`**：

```java
@Override
public List<ClassificationRecord> listByCondition(Integer userId, String predLabel, String startTime, String endTime, String source, String summary) {
    // 在 Service 层转义 LIKE 通配符
    String escapedSummary = null;
    if (summary != null && !summary.isEmpty()) {
        escapedSummary = summary.replace("%", "\\%").replace("_", "\\_");
    }
    return classificationRecordMapper.selectByCondition(userId, predLabel, startTime, endTime, source, escapedSummary);
}
```

**修改 `ClassificationRecordMapper.xml`**：

移除 `<bind>` 标签，直接使用参数：

```xml
<if test="summary != null and summary != ''">
    AND summary LIKE CONCAT('%', #{summary}, '%') ESCAPE '\\'
</if>
```

注意：Service 层传入的 `summary` 已经是转义后的值，SQL 中指定 `ESCAPE '\\'` 告知数据库 `\` 是转义字符。

## bug3 分析与修复
参考以下映射关系解决即可
```python
# === index → 标签名称映射 ===
LABELS = [
    '中医器械', '临床检验器械', '医用康复器械', '医用成像器械', '医用诊察和监护器械', '医用软件',
    '医疗器械消毒灭菌器械', '口腔科器械', '呼吸、麻醉和急救器械', '妇产科、辅助生殖和避孕器械',
    '患者承载器械', '放射治疗器械', '无源手术器械', '无源植入器械', '有源手术器械', '有源植入器械',
    '注输、护理和防护器械', '物理治疗器械', '眼科器械', '神经和心血管手术器械', '输血、透析和体外循环器械', '骨科手术器械'
]
```
