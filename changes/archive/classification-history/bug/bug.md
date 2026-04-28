# bug

## bug1
第一次点击详情不展示echart，但第二次及之后点击详情才展示echart
### 问题定位：
- http://localhost:8080/#/patent-classification
- http://localhost:8080/#/classification-history
```
Uncaught (in promise) Error: A listener indicated an asynchronous response by returning true, but the message channel closed before a response was received
```

后续发现：第一次打开确实显示了，但宽高不对，没有铺满，默认是 100 * 400。

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
        ...
```

---

## Bug1 分析与修复（最终方案）

### 原因分析（两个阶段）

**阶段1：第一次点击不显示图表**

执行顺序：
1. 弹窗打开 → `onDialogOpened` 执行 → `detailCategories` 赋值
2. `v-if` 条件满足 → `ChartVisualization` 开始创建
3. `mounted` → `initChart()`（用了 `$nextTick`，chart 还没初始化）
4. `watch immediate: true` → `renderChart()`（此时 `this.chart = null`）
5. 第 71 行 `if (!this.chart) return` ← 直接退出，图表不渲染

**根本原因**：`v-if` 导致组件动态创建，而 `initChart()` 用 `$nextTick` 延迟初始化，watch 的 `renderChart()` 在 chart 初始化完成之前就执行了。

**阶段2：第一次显示后宽高不对**

- 组件使用 `:style="{ display: detailCategories.length > 0 ? 'block' : 'none' }"` 控制显示
- 弹窗打开前 `display: none`，容器尺寸为 0
- ECharts 用错误尺寸初始化后，没有重新计算

### 修复方案

**修改 `ClassificationHistory.vue`**：

1. 去掉 `v-if`，改用 `:style` 控制显示隐藏，组件始终存在：
```vue
<ChartVisualization
  ref="detailChart"
  :categories="detailCategories"
  height="400px"
  :style="{ display: detailCategories.length > 0 ? 'block' : 'none' }"
/>
```

2. `onDialogOpened` 中调用 `resize()` 重算尺寸：
```javascript
onDialogOpened () {
  try {
    this.detailCategories = JSON.parse(this.detailRecord.topCategories || '[]')
  } catch (e) {
    this.detailCategories = []
  }
  this.$nextTick(() => {
    if (this.$refs.detailChart) {
      this.$refs.detailChart.renderChart()
      // 弹窗打开后容器尺寸变化，需要 resize
      setTimeout(() => {
        if (this.$refs.detailChart) {
          this.$refs.detailChart.resize()
        }
      }, 100)
    }
  })
}
```

**修改 `ChartVisualization.vue`**：

1. `renderChart` 方法增加 chart 未初始化时的处理：
```javascript
renderChart () {
  if (!this.categories || this.categories.length === 0) return

  // 如果 chart 未初始化，先初始化
  if (!this.chart) {
    this.$nextTick(() => {
      if (this.$refs.chart) {
        this.chart = echarts.init(this.$refs.chart)
        window.addEventListener('resize', this.handleResize)
        this.doRenderChart()
      }
    })
    return
  }

  this.doRenderChart()
}
```

2. 新增 `resize()` 方法：
```javascript
resize () {
  if (this.chart) {
    this.chart.resize()
  }
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

---

## Bug3 分析与修复

### 原因

前端下拉框的预测类别选项与后端模型的 LABELS 映射不一致。

### 修复方案

参考以下正确的映射关系更新 `ClassificationHistory.vue` 下拉框选项：

```python
# === index → 标签名称映射 ===
LABELS = [
    '中医器械', '临床检验器械', '医用康复器械', '医用成像器械', '医用诊察和监护器械', '医用软件',
    '医疗器械消毒灭菌器械', '口腔科器械', '呼吸、麻醉和急救器械', '妇产科、辅助生殖和避孕器械',
    '患者承载器械', '放射治疗器械', '无源手术器械', '无源植入器械', '有源手术器械', '有源植入器械',
    '注输、护理和防护器械', '物理治疗器械', '眼科器械', '神经和心血管手术器械', '输血、透析和体外循环器械', '骨科手术器械'
]
```

---

## 修复总结

| Bug | 修复文件 | 修复要点 |
|-----|---------|---------|
| Bug1 | `ClassificationHistory.vue` + `ChartVisualization.vue` | 去掉 `v-if` 改用 `display`；`renderChart` 兜底初始化；弹窗打开后 `resize()` |
| Bug2 | `RecordServiceImpl.java` + `ClassificationRecordMapper.xml` | Service 层转义 LIKE 通配符，移除 `<bind>` OGNL |
| Bug3 | `ClassificationHistory.vue` | 下拉框选项替换为正确的 22 类映射 |
