# Bug Log

## Bug #1: asyncio.as_completed 导致索引错位

**日期**: 2026-05-01
**文件**: `2.zero_shot_classify.py`

### 现象

输入数据 1104 条（无重复申请号），标注后输出 xlsx 只有 939 条，丢失 165 条。

### 根因

`asyncio.as_completed()` 返回的协程是**完成顺序**，不是提交顺序。当 `retry_failed` 中用 results 列表索引去 `df.iloc[i]` 取行时，两者不对应：

```python
# BUG: failed_indices 是 results 列表索引（完成顺序），不是 DataFrame 行号
failed_indices = [i for i, r in enumerate(results) if r["pred_label"] == "请求失败"]
rows = [df.iloc[i] for i in failed_indices]  # 取了错误的行！
```

重试时取了错误的行，导致部分申请号被错误覆盖或丢失。

### 修复

用结果中的业务主键（申请号）定位正确的行，而非依赖列表索引：

```python
# 正确：用申请号从 DataFrame 中查找对应行
pid_to_row = {row["申请号"]: row for _, row in df.iterrows()}
rows = [pid_to_row[results[i]["申请号"]] for i in failed_indices]

# 原地更新也按申请号匹配，而非按列表位置 zip
new_by_pid = {r["申请号"]: r for r in new_results}
for i in failed_indices:
    pid = results[i]["申请号"]
    if pid in new_by_pid:
        results[i] = new_by_pid[pid]
```

### 通用原则

> **使用 `asyncio.as_completed` / `asyncio.gather` 时，不要用列表索引去映射回原始输入。** 因为结果顺序可能与输入顺序不一致，必须用业务主键（如 ID）来关联输入和输出。
