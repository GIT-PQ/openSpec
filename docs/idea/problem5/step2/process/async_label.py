import asyncio
import time
import pandas as pd
import requests
from tqdm import tqdm

# ==================== 配置区 ====================

# Dify 应用配置
API_KEY = "app-eAalqcHLyQrAs45tXXxq0lGG"
API_URL = "http://localhost/v1/workflows/run"

# API 限流参数
RPM_LIMIT = 600
TPM_LIMIT = 1000000
AVG_RESPONSE_TIME = 3.0    # 秒
AVG_TOKENS_PER_CALL = 2500 # token

# 并发控制参数（由下方自动计算，也可手动覆盖）
SAFETY_FACTOR = 0.85
CONCURRENCY_BUFFER = 1.2

# 任务配置
ROUND = 1                  # 当前轮数，输出列名为 last_label_{ROUND}
SKIP_FILLED = True         # 是否跳过已填充的行
SAVE_EVERY = 500           # 每多少条保存一次
MAX_RETRIES = 3            # 单条请求最大重试次数
RETRY_DELAY = 5            # 重试间隔（秒）

# ==================== 并发参数计算 ====================

def compute_concurrency_params():
    rpm_from_tpm = TPM_LIMIT / AVG_TOKENS_PER_CALL
    rpm_ceiling = min(RPM_LIMIT, rpm_from_tpm)
    safe_rpm = rpm_ceiling * SAFETY_FACTOR
    min_interval = 60.0 / safe_rpm
    arrival_rate = safe_rpm / 60.0
    avg_concurrency = arrival_rate * AVG_RESPONSE_TIME
    max_concurrency = int(avg_concurrency * CONCURRENCY_BUFFER) + 1
    bottleneck = "RPM" if RPM_LIMIT <= rpm_from_tpm else "TPM"
    return {
        "safe_rpm": safe_rpm,
        "min_interval": min_interval,
        "max_concurrency": max_concurrency,
        "bottleneck": bottleneck,
    }

# ==================== 限速器 ====================

class RateLimiter:
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

# ==================== 调用 Dify ====================

def call_dify(abstract: str) -> str:
    headers = {
        "Authorization": f"Bearer {API_KEY}",
        "Content-Type": "application/json",
    }
    data = {
        "inputs": {"abstract": abstract},
        "response_mode": "blocking",
        "user": "pq",
    }
    response = requests.post(API_URL, headers=headers, json=data, timeout=120)
    if response.status_code == 200:
        result = response.json()
        status = result.get("data", {}).get("status")
        if status == "succeeded":
            outputs = result.get("data", {}).get("outputs", {})
            text = outputs.get("text", {})
            category = text.get("类别", "")
            if category:
                return category
        error = result.get("data", {}).get("error", "")
        raise Exception(f"工作流未成功: status={status}, error={error}")
    else:
        raise Exception(f"HTTP {response.status_code}: {response.text[:200]}")

# ==================== 单条处理 ====================

async def process_one(idx, abstract, semaphore, rate_limiter, pbar):
    async with semaphore:
        await rate_limiter.acquire()

    loop = asyncio.get_event_loop()
    for attempt in range(1, MAX_RETRIES + 1):
        try:
            category = await loop.run_in_executor(None, call_dify, abstract)
            pbar.update(1)
            return idx, category
        except Exception as e:
            if attempt < MAX_RETRIES:
                await asyncio.sleep(RETRY_DELAY)
            else:
                print(f"\n[行{idx}] 重试{MAX_RETRIES}次仍失败: {e}")
                pbar.update(1)
                return idx, "失败"

# ==================== 主流程 ====================

async def run(input_path: str, output_path: str = None):
    params = compute_concurrency_params()
    print(f"并发参数: safe_RPM={params['safe_rpm']:.0f}, "
          f"min_interval={params['min_interval']:.3f}s, "
          f"max_concurrency={params['max_concurrency']}, "
          f"瓶颈={params['bottleneck']}")

    output_col = f"last_label_{ROUND}"
    if output_path is None:
        output_path = input_path

    df = pd.read_excel(input_path)
    print(f"总行数: {len(df)}")

    # 确定待处理行
    if output_col not in df.columns:
        df[output_col] = pd.NA

    if SKIP_FILLED:
        mask = df[output_col].isna() & df["摘要"].notna()
    else:
        mask = df["摘要"].notna()

    todo = df[mask].index.tolist()
    print(f"待处理: {len(todo)} 条 (列={output_col}, 跳过已填充={SKIP_FILLED})")

    if not todo:
        print("无待处理数据，退出")
        return

    semaphore = asyncio.Semaphore(params["max_concurrency"])
    rate_limiter = RateLimiter(params["min_interval"])

    with tqdm(total=len(todo), desc="标注进度", ncols=80) as pbar:
        tasks = []
        for idx in todo:
            abstract = df.at[idx, "摘要"]
            tasks.append(process_one(idx, abstract, semaphore, rate_limiter, pbar))

        results = await asyncio.gather(*tasks)

    # 写回结果
    for idx, category in results:
        df.at[idx, output_col] = category

    # 保存
    df.to_excel(output_path, index=False)
    print(f"已保存到: {output_path}")

    # 统计
    valid = df[df[output_col].notna() & (df[output_col] != "失败")]
    failed = df[df[output_col] == "失败"]
    print(f"成功: {len(valid)}, 失败: {len(failed)}, 未处理: {len(df) - len(valid) - len(failed)}")

# ==================== 入口 ====================

if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser(description="并发调用 Dify 工作流标注数据")
    parser.add_argument("input", help="输入 xlsx 文件路径")
    parser.add_argument("-o", "--output", help="输出 xlsx 文件路径（默认覆盖输入）")
    parser.add_argument("-r", "--round", type=int, default=1, help="轮数（默认1）")
    parser.add_argument("--no-skip", action="store_true", help="不跳过已填充行")
    args = parser.parse_args()

    ROUND = args.round
    SKIP_FILLED = not args.no_skip

    asyncio.run(run(args.input, args.output))
