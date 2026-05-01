import asyncio
import time
import pandas as pd
import requests
from tqdm import tqdm

# ==================== 配置 ====================
API_KEY = "app-eAalqcHLyQrAs45tXXxq0lGG"
API_URL = "http://localhost/v1/workflows/run"
RPM_LIMIT = 600
TPM_LIMIT = 1000000
AVG_RESPONSE_TIME = 3.0
AVG_TOKENS_PER_CALL = 2500
SAFETY_FACTOR = 0.85
MAX_RETRIES = 3
RETRY_DELAY = 5

INPUT_PATH = "../input/D2.xlsx"
OUTPUT_COL = "v12_error_relabel_5"
REAL_COL = "一级产品类别（校对）"

# ==================== 并发参数 ====================
rpm_from_tpm = TPM_LIMIT / AVG_TOKENS_PER_CALL
rpm_ceiling = min(RPM_LIMIT, rpm_from_tpm)
safe_rpm = rpm_ceiling * SAFETY_FACTOR
MIN_INTERVAL = 60.0 / safe_rpm
MAX_CONCURRENCY = int((safe_rpm / 60.0) * AVG_RESPONSE_TIME * 1.2) + 1

# ==================== 限速器 ====================
class RateLimiter:
    def __init__(self, min_interval):
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
def call_dify(abstract):
    headers = {"Authorization": f"Bearer {API_KEY}", "Content-Type": "application/json"}
    data = {"inputs": {"abstract": abstract}, "response_mode": "blocking", "user": "pq"}
    resp = requests.post(API_URL, headers=headers, json=data, timeout=120)
    if resp.status_code == 200:
        result = resp.json()
        if result.get("data", {}).get("status") == "succeeded":
            text = result["data"]["outputs"].get("text", {})
            category = text.get("类别", "")
            if category:
                return category
        error = result.get("data", {}).get("error", "")
        raise Exception(f"status={result.get('data',{}).get('status')}, error={error}")
    raise Exception(f"HTTP {resp.status_code}: {resp.text[:200]}")

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
async def main():
    df = pd.read_excel(INPUT_PATH)
    todo = df[df["v12预测错误"] == True].index.tolist()
    print(f"v12预测错误总数: {len(todo)}")

    if not todo:
        print("无待处理数据")
        return

    if OUTPUT_COL not in df.columns:
        df[OUTPUT_COL] = pd.NA

    # 跳过已填充
    todo = [i for i in todo if pd.isna(df.at[i, OUTPUT_COL])]
    print(f"待预测: {len(todo)}")

    semaphore = asyncio.Semaphore(MAX_CONCURRENCY)
    rate_limiter = RateLimiter(MIN_INTERVAL)

    with tqdm(total=len(todo), desc="标注进度", ncols=80) as pbar:
        tasks = [process_one(i, df.at[i, "摘要"], semaphore, rate_limiter, pbar) for i in todo]
        results = await asyncio.gather(*tasks)

    for idx, category in results:
        df.at[idx, OUTPUT_COL] = category

    df.to_excel(INPUT_PATH, index=False)
    print(f"已保存到: {INPUT_PATH}")

    # 准确率计算
    valid = df[df[OUTPUT_COL].notna() & (df[OUTPUT_COL] != "失败")]
    total = len(valid)
    correct = (valid[OUTPUT_COL] == valid[REAL_COL]).sum()
    print(f"\nv12错误样本重新标注准确率: {correct}/{total} = {correct/total:.2%}")

if __name__ == "__main__":
    asyncio.run(main())
