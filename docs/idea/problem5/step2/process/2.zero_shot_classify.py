"""
LLM Zero-Shot 标注方案 — 并发批量标注

实验对照组②：验证"裸LLM"（无领域知识注入）在医疗器械专利分类上的表现。
仅提供22个类别名称和简短描述，测试LLM自身语义理解能力。

支持多轮标注（n_run），每轮预测列命名为 pred_label_{n}。
评估逻辑请在外部通用函数中完成，本脚本只负责预测和保存。
"""

import asyncio
import os
import re
import sys
import time
from pathlib import Path

import pandas as pd
from dotenv import load_dotenv
from openai import AsyncOpenAI
from tqdm import tqdm

# ── 加载环境变量 ──────────────────────────────────────────────
env_path = Path(__file__).parent / ".env"
load_dotenv(env_path)

API_KEY = os.getenv("DASHSCOPE_API_KEY")
MODEL = os.getenv("model")
BASE_URL = os.getenv("base_url")

if not API_KEY or not MODEL or not BASE_URL:
    sys.exit("错误：请在 .env 中配置 DASHSCOPE_API_KEY、model、base_url")

# ── 22 个类别标签 ─────────────────────────────────────────────
LABELS = [ "有源手术器械", "无源手术器械", "神经和心血管手术器械", "骨科手术器械",
           "放射治疗器械", "医用成像器械", "医用诊察和监护器械", "呼吸、麻醉和急救器械",
           "物理治疗器械", "输血、透析和体外循环器械", "医疗器械消毒灭菌器械",
           "有源植入器械", "无源植入器械", "注输、护理和防护器械",
           "患者承载器械", "眼科器械", "口腔科器械", "妇产科、辅助生殖和避孕器械",
           "医用康复器械", "中医器械", "医用软件", "临床检验器械"
           ]

# ── 限流参数 ─────────────────────────────────────────────────
# rpm=600，留余量按 450 计算，确保请求匀速发送
SAFE_RPM = 450
MIN_INTERVAL = 60.0 / SAFE_RPM  # ≈0.133s，两次请求之间的最小间隔
MAX_CONCURRENCY = 30  # 最大并发数（SAFE_RPM/60 × 平均耗时4s ≈ 30）

# ── LLM 生成参数 ─────────────────────────────────────────────
TEMPERATURE = 0.6
TOP_P = 0.6

# ── 重试参数 ─────────────────────────────────────────────────
MAX_RETRIES = 3
RETRY_COOLDOWN = 60  # 请求失败后兜底重试的等待秒数

# ── System Prompt（编号与 LABELS 数组顺序一致）───────────────────────────
SYSTEM_PROMPT = """你是一位专利分类专家，负责将医疗器械发明专利归类到22个一级产品类别之一。

22个医疗器械类别（请输出对应编号1-22）：
1. 有源手术器械 - 依赖电源的手术器械（如电刀、超声刀、激光手术设备等）
2. 无源手术器械 - 不依赖电源的手术器械（如手术刀、钳、剪等）
3. 神经和心血管手术器械 - 神经外科和心血管手术专用器械
4. 骨科手术器械 - 骨科手术专用器械
5. 放射治疗器械 - 用于放射治疗的设备及配套器械
6. 医用成像器械 - 用于医学影像的器械（如X光、CT、MRI、超声成像等）
7. 医用诊察和监护器械 - 用于生理参数监测、诊察的器械
8. 呼吸、麻醉和急救器械 - 呼吸支持、麻醉、急救用器械
9. 物理治疗器械 - 利用物理因子（光、电、热、磁等）进行治疗的器械
10. 输血、透析和体外循环器械 - 血液处理和体外循环相关器械
11. 医疗器械消毒灭菌器械 - 用于医疗器械消毒灭菌的设备
12. 有源植入器械 - 植入体内且有源动的器械（如心脏起搏器等）
13. 无源植入器械 - 植入体内且无源动的器械（如人工关节、骨板等）
14. 注输、护理和防护器械 - 注射、输液、护理防护用品
15. 患者承载器械 - 手术床、轮椅、担架等承载患者的器械
16. 眼科器械 - 眼科专用诊断、手术器械
17. 口腔科器械 - 牙科、口腔科专用器械
18. 妇产科、辅助生殖和避孕器械 - 妇产科及生殖健康相关器械
19. 医用康复器械 - 用于患者康复训练的器械
20. 中医器械 - 基于中医理论的诊断、治疗器械
21. 医用软件 - 医疗用途的独立软件
22. 临床检验器械 - 用于实验室检验、体外诊断的器械

分类规则：
- 每条专利必须且只能归入一个类别
- 请根据专利的摘要内容判断其主要功能和用途
- 当专利涉及多个类别时，选择其主要功能或核心用途对应的类别
- 请仅输出类别编号（1-22），不要输出其他内容"""


def build_user_prompt(row: pd.Series) -> str:
    return f"""请对以下专利进行分类：

摘要：{row['摘要']}

请输出该专利所属的类别编号（1-22）。"""


def parse_output(raw: str) -> str:
    """解析 LLM 输出，返回类别名称或 '解析错误'"""
    raw = raw.strip()
    numbers = re.findall(r"\b(\d+)\b", raw)
    for n in reversed(numbers):
        idx = int(n) - 1
        if 0 <= idx < 22:
            return LABELS[idx]
    return "解析错误"


class RateLimiter:
    """令牌桶式匀速限速器：确保请求间隔不低于 MIN_INTERVAL"""

    def __init__(self, min_interval: float):
        self._min_interval = min_interval
        self._last_sent = 0.0
        self._lock = asyncio.Lock()

    async def acquire(self):
        async with self._lock:
            now = time.monotonic()
            wait = self._min_interval - (now - self._last_sent)
            if wait > 0:
                await asyncio.sleep(wait)
            self._last_sent = time.monotonic()


async def classify_one(
    client: AsyncOpenAI,
    semaphore: asyncio.Semaphore,
    limiter: RateLimiter,
    row: pd.Series,
) -> dict:
    """对单条专利进行分类，带重试"""
    user_prompt = build_user_prompt(row)

    for attempt in range(MAX_RETRIES):
        async with semaphore:
            await limiter.acquire()
            try:
                resp = await client.chat.completions.create(
                    model=MODEL,
                    messages=[
                        {"role": "system", "content": SYSTEM_PROMPT},
                        {"role": "user", "content": user_prompt},
                    ],
                    temperature=TEMPERATURE,
                    top_p=TOP_P,
                    max_tokens=10,
                    extra_body={"enable_thinking": False},
                )
                raw_output = resp.choices[0].message.content.strip()
                pred_label = parse_output(raw_output)
                return {
                    "申请号": row["申请号"],
                    "true_label": row["一级产品类别（校对）"],
                    "pred_label": pred_label,
                    "raw_output": raw_output,
                }
            except Exception as e:
                if attempt < MAX_RETRIES - 1:
                    await asyncio.sleep(2 ** attempt)
                else:
                    return {
                        "申请号": row["申请号"],
                        "true_label": row["一级产品类别（校对）"],
                        "pred_label": "请求失败",
                        "raw_output": str(e),
                    }


async def batch_classify_once(
    df: pd.DataFrame,
    semaphore: asyncio.Semaphore,
    limiter: RateLimiter,
    desc: str = "标注",
) -> list[dict]:
    """单轮并发批量分类"""
    client = AsyncOpenAI(api_key=API_KEY, base_url=BASE_URL)
    tasks = [classify_one(client, semaphore, limiter, row) for _, row in df.iterrows()]

    results = []
    pbar = tqdm(asyncio.as_completed(tasks), total=len(tasks), desc=desc)

    for coro in pbar:
        result = await coro
        results.append(result)

    await client.close()
    return results


async def retry_failed(
    df: pd.DataFrame,
    failed_indices: list[int],
    results: list[dict],
    semaphore: asyncio.Semaphore,
    limiter: RateLimiter,
    desc: str = "兜底重试",
) -> None:
    """对请求失败的行进行兜底重试，原地更新 results"""
    client = AsyncOpenAI(api_key=API_KEY, base_url=BASE_URL)
    # 用失败结果中的申请号定位正确的行，而非用 results 列表索引取 df.iloc
    pid_to_row = {row["申请号"]: row for _, row in df.iterrows()}
    rows = [pid_to_row[results[i]["申请号"]] for i in failed_indices]
    tasks = [classify_one(client, semaphore, limiter, row) for row in rows]

    pbar = tqdm(asyncio.as_completed(tasks), total=len(tasks), desc=desc)
    new_results = []
    for coro in pbar:
        new_results.append(await coro)

    await client.close()

    # 原地更新：按申请号匹配，而非按列表位置
    new_by_pid = {r["申请号"]: r for r in new_results}
    for i in failed_indices:
        pid = results[i]["申请号"]
        if pid in new_by_pid:
            results[i] = new_by_pid[pid]


async def run_with_retry(
    df: pd.DataFrame,
    semaphore: asyncio.Semaphore,
    limiter: RateLimiter,
    desc: str = "标注",
) -> list[dict]:
    """批量标注 + 兜底重试循环"""
    results = await batch_classify_once(df, semaphore, limiter, desc=desc)

    fail_count = sum(1 for r in results if r["pred_label"] == "请求失败")
    retry_round = 0
    while fail_count > 0:
        retry_round += 1
        print(f"\n检测到 {fail_count} 条请求失败，等待 {RETRY_COOLDOWN}s 后进行第 {retry_round} 轮重试...")
        await asyncio.sleep(RETRY_COOLDOWN)

        failed_indices = [i for i, r in enumerate(results) if r["pred_label"] == "请求失败"]
        await retry_failed(df, failed_indices, results, semaphore, limiter, desc=f"兜底重试 R{retry_round}")

        fail_count = sum(1 for r in results if r["pred_label"] == "请求失败")

    return results


async def run_all_rounds(df: pd.DataFrame, n_run: int, output_path: Path):
    """在同一 event loop 内运行多轮标注，避免 Semaphore 跨 loop 问题"""
    semaphore = asyncio.Semaphore(MAX_CONCURRENCY)
    limiter = RateLimiter(MIN_INTERVAL)
    print(f"SAFE_RPM={SAFE_RPM}, 请求间隔≈{MIN_INTERVAL:.3f}s, 并发窗口={MAX_CONCURRENCY}")

    start_total = time.time()
    all_results = {}  # key: 申请号, value: dict

    # 断点续跑：加载已有结果
    existing_cols = []
    if output_path.exists():
        existing_df = pd.read_excel(output_path)
        for _, row in existing_df.iterrows():
            pid = row["申请号"]
            all_results[pid] = row.to_dict()
        existing_cols = [c for c in existing_df.columns if c.startswith("pred_label_")]
        print(f"已有结果: {len(existing_df)} 条, 已完成轮次: {len(existing_cols)}")

    for n in range(1, n_run + 1):
        col_name = f"pred_label_{n}"
        if col_name in existing_cols:
            print(f"\n第 {n}/{n_run} 轮已存在 ({col_name})，跳过")
            continue

        print(f"\n{'='*50}")
        print(f"第 {n}/{n_run} 轮标注 (temperature={TEMPERATURE}, top_p={TOP_P})")
        print(f"{'='*50}")

        start = time.time()
        results = await run_with_retry(df, semaphore, limiter, desc=f"R{n}")
        elapsed = time.time() - start

        fail_count = sum(1 for r in results if r["pred_label"] == "请求失败")
        parse_fail = sum(1 for r in results if r["pred_label"] == "解析错误")
        valid_count = len(results) - fail_count - parse_fail

        print(f"R{n} 耗时: {elapsed:.1f}s, 有效: {valid_count}, 解析错误: {parse_fail}, 请求失败: {fail_count}")

        # 汇聚到 all_results
        raw_name = f"raw_output_{n}"
        for r in results:
            pid = r["申请号"]
            if pid not in all_results:
                all_results[pid] = {"申请号": pid, "true_label": r["true_label"]}
            all_results[pid][col_name] = r["pred_label"]
            all_results[pid][raw_name] = r["raw_output"]

        # 每轮标注后立即保存结果
        result_df = pd.DataFrame(list(all_results.values()))
        pred_cols = [f"pred_label_{i}" for i in range(1, n + 1) if f"pred_label_{i}" in result_df.columns]
        raw_cols = [f"raw_output_{i}" for i in range(1, n + 1) if f"raw_output_{i}" in result_df.columns]
        result_df = result_df[["申请号", "true_label"] + pred_cols + raw_cols]
        result_df.to_excel(output_path, index=False)
        print(f"第 {n} 轮结果已保存到: {output_path}")

    elapsed_total = time.time() - start_total

    print(f"\n{'='*50}")
    print(f"总耗时: {elapsed_total:.1f}s ({n_run} 轮)")
    print(f"最终结果已保存: {output_path}")


def main():
    # ── 超参数 ─────────────────────────────────────────────
    n_run = 10  # 标注轮次

    # ── 路径 ───────────────────────────────────────────────
    base = Path(__file__).resolve().parent.parent
    input_path = base / "input" / "D2.xlsx"
    output_path = base / "output" / "llm_zeroshot_results.xlsx"

    # ── 加载数据 ───────────────────────────────────────────
    sys.stdout.reconfigure(encoding="utf-8")
    df = pd.read_excel(input_path)
    print(f"数据量: {len(df)}, 类别数: {df['一级产品类别（校对）'].nunique()}")

    # ── 整个流程在同一个 event loop 中运行 ─────────────────
    asyncio.run(run_all_rounds(df, n_run, output_path))


if __name__ == "__main__":
    main()
