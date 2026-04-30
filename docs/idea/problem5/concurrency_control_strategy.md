# LLM API 并发控制策略

## 目标

在给定 API 限流参数的条件下，通过控制**发送速率**和**并发窗口**，使请求既不被限流，又能最大化吞吐。

## 输入参数

| 参数 | 符号 | 含义 |
|------|------|------|
| RPM_limit | $R_{lim}$ | API 每分钟最大请求数 |
| TPM_limit | $T_{lim}$ | API 每分钟最大 token 数 |
| avg_response_time | $t_{resp}$ | 单次调用平均响应时间（秒） |
| avg_tokens_per_call | $tok_{avg}$ | 单次调用平均消耗 token 数 |

## 核心推导

### 1. 确定 RPM 有效上限

API 同时受 RPM 和 TPM 两个维度约束，取较小者：

```
RPM_from_TPM = TPM_limit / avg_tokens_per_call
RPM_ceiling  = min(RPM_limit, RPM_from_TPM)
```

> 例：RPM=600, TPM=1000000, avg_tokens=800
> → RPM_from_TPM = 1250
> → RPM_ceiling = min(600, 1250) = **600**（RPM 是瓶颈）
>
> 例：RPM=600, TPM=100000, avg_tokens=800
> → RPM_from_TPM = 125
> → RPM_ceiling = min(600, 125) = **125**（TPM 是瓶颈）

### 2. 施加安全裕度

```
safety_factor = 0.85   # 留 15% 余量，应对波动
safe_RPM = RPM_ceiling × safety_factor
```

> 15% 余量的依据：网络抖动、响应时间波动、token 消耗波动。
> 如果你的请求模式非常稳定，可提高到 0.90；反之降到 0.80。

### 3. 计算最小请求间隔

```
min_interval = 60 / safe_RPM   # 秒
```

这是两个相邻请求发送时刻之间的最小距离。用**令牌桶限速器**在发送前强制等待。

### 4. 计算最大并发数（Little's Law）

稳定状态下，并发数 = 到达率 × 平均响应时间：

```
arrival_rate     = safe_RPM / 60              # 请求/秒
avg_concurrency  = arrival_rate × avg_response_time
max_concurrency  = ceil(avg_concurrency × 1.2)  # 20% 缓冲
```

用 **Semaphore** 限制同时在途的请求数不超过此值。

> 例：safe_RPM=510, avg_response_time=4s
> → arrival_rate = 8.5 req/s
> → avg_concurrency = 8.5 × 4 = 34
> → max_concurrency = ceil(34 × 1.2) = **41**

## 双重控制架构

```
         ┌──────────────┐
  请求 ──→│  Semaphore   │──→ 同时在途 ≤ max_concurrency
         │ (并发窗口)    │
         └──────┬───────┘
                │
         ┌──────▼───────┐
         │ RateLimiter  │──→ 发送间隔 ≥ min_interval
         │ (令牌桶匀速)  │
         └──────┬───────┘
                │
           发送请求 ──→ API
```

**Semaphore** 和 **RateLimiter** 各管一件事：

| 控制器 | 防止什么 | 怎么防 |
|--------|---------|--------|
| Semaphore | 瞬间并发过高，在途请求堆积 | 限制同时在途数量 |
| RateLimiter | 单位时间请求过多，触发 RPM/TPM 限流 | 强制相邻请求最小间隔 |

两者缺一不可：
- 只有 Semaphore：可能在短时间内释放→获取→释放→获取，瞬间发送速率远超 RPM
- 只有 RateLimiter：虽然发送速率受控，但若响应变慢，在途请求会无限堆积

## 完整参数速查

以当前项目参数为例（RPM=600, TPM=1000000, avg_response_time=4s, avg_tokens=800）：

```
RPM_from_TPM    = 1000000 / 800 = 1250
RPM_ceiling     = min(600, 1250) = 600
safe_RPM        = 600 × 0.85 = 510
min_interval    = 60 / 510 ≈ 0.118s
arrival_rate    = 510 / 60 = 8.5 req/s
avg_concurrency = 8.5 × 4 = 34
max_concurrency = ceil(34 × 1.2) = 41
```

**对比当前代码的参数**：`SAFE_RPM=450, MIN_INTERVAL≈0.133s, MAX_CONCURRENCY=30`

当前代码偏保守（安全裕度 75%），并发窗口偏小（30 vs 理论值 41），吞吐有约 12% 的提升空间。

## 实现模板

```python
import asyncio
import time

class RateLimiter:
    """令牌桶式匀速限速器"""
    def __init__(self, min_interval: float):
        self._min_interval = min_interval
        self._last_sent = 0.0
        self._lock = asyncio.Lock()

    async def acquire(self):
        async with self._lock:
            wait = self._min_interval - (time.monotonic() - self._last_sent)
            if wait > 0:
                await asyncio.sleep(wait)
            self._last_sent = time.monotonic()


def compute_concurrency_params(
    rpm_limit: int,
    tpm_limit: int,
    avg_response_time: float,
    avg_tokens: int,
    safety_factor: float = 0.85,
    concurrency_buffer: float = 1.2,
) -> dict:
    """根据 API 限流参数计算最优并发控制参数"""
    rpm_from_tpm = tpm_limit / avg_tokens
    rpm_ceiling = min(rpm_limit, rpm_from_tpm)
    safe_rpm = rpm_ceiling * safety_factor
    min_interval = 60.0 / safe_rpm
    arrival_rate = safe_rpm / 60.0
    avg_concurrency = arrival_rate * avg_response_time
    max_concurrency = int(avg_concurrency * concurrency_buffer) + 1

    return {
        "safe_rpm": safe_rpm,
        "min_interval": min_interval,
        "max_concurrency": max_concurrency,
        "rpm_bottleneck": "RPM" if rpm_limit <= rpm_from_tpm else "TPM",
    }
```

## 边界情况

### 响应时间波动大

如果 P95 响应时间是均值的 2-3 倍，Semaphore 会被长期占满，导致吞吐下降。

对策：将 `max_concurrency` 的缓冲系数从 1.2 提高到 1.5，或在运行时动态调整（见下文）。

### Token 消耗波动大

若部分请求消耗远超 avg_tokens，可能触发 TPM 限流。

对策：
1. 降低 safety_factor（如 0.75）留更多余量
2. 按 token 消耗分桶：大 token 请求单独降速
3. 在 RateLimiter 中加入 token 维度的流量控制（复杂度较高）

### 响应时间极短（<0.5s）

此时并发数很低（如 safe_RPM=510, t=0.3s → concurrency ≈ 3），瓶颈完全在发送速率。
Semaphore 退化为几乎不生效，吞吐完全由 RateLimiter 决定。

### 响应时间极长（>10s）

并发数可能很高，但实际受 API 侧连接数限制。
需确认 API 是否有最大连接数/并发连接数限制，并将 `max_concurrency` 设为两者较小值。

## 进阶：运行时自适应

固定参数在稳态下工作良好，但实际场景中响应时间会波动。可加入自适应逻辑：

```python
class AdaptiveRateLimiter:
    """基于滑动窗口统计的自适应限速器"""
    def __init__(self, safe_rpm: float, max_concurrency: int):
        self.min_interval = 60.0 / safe_rpm
        self.semaphore = asyncio.Semaphore(max_concurrency)
        self._lock = asyncio.Lock()
        self._last_sent = 0.0
        self._recent_tokens = []  # 最近1分钟的token消耗
        self._tpm_limit = None    # 如需TPM控制

    async def acquire(self, estimated_tokens: int = 0):
        async with self._lock:
            # RPM 维度
            wait = self.min_interval - (time.monotonic() - self._last_sent)
            if wait > 0:
                await asyncio.sleep(wait)
            # TPM 维度（可选）
            if self._tpm_limit and estimated_tokens > 0:
                tpm_wait = self._check_tpm(estimated_tokens)
                if tpm_wait > 0:
                    await asyncio.sleep(tpm_wait)
            self._last_sent = time.monotonic()
```

> 自适应方案复杂度显著增加，建议仅在固定参数方案频繁触发限流时再考虑。
