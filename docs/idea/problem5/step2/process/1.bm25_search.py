"""
BM25 超参数搜索

搜索维度：k1, b, agg
输出：bm25_results.xlsx，每列对应一组超参数组合的预测结果
"""
import os
import jieba
import pandas as pd
from pathlib import Path
from rank_bm25 import BM25Okapi
from collections import defaultdict

# ── 22 类标签 ─────────────────────────────────────────
LABELS = [
    "有源手术器械", "无源手术器械", "神经和心血管手术器械", "骨科手术器械",
    "放射治疗器械", "医用成像器械", "医用诊察和监护器械", "呼吸、麻醉和急救器械",
    "物理治疗器械", "输血、透析和体外循环器械", "医疗器械消毒灭菌器械",
    "有源植入器械", "无源植入器械", "注输、护理和防护器械",
    "患者承载器械", "眼科器械", "口腔科器械", "妇产科、辅助生殖和避孕器械",
    "医用康复器械", "中医器械", "医用软件", "临床检验器械"
]

# ── 路径 ──────────────────────────────────────────────
base = Path(__file__).resolve().parent.parent
JIEBA_DICT = base / "output" / "jieba_dict" / "医疗器械术语_合并.txt"
CATALOG_PARQUET = base / "output" / "医疗器械分类目录_eb_with_full_structure_normalized.parquet"
PATENT_PARQUET = base / "output" / "D2_eb.parquet"
OUTPUT_XLSX = base / "output" / "bm25_results.xlsx"

# ── 搜索空间 ──────────────────────────────────────────
K1_VALUES = [0.5, 1.0, 1.5, 2.0, 2.5]
B_VALUES = [0.3, 0.5, 0.75, 0.9, 1.0]
# "max", "sum"已经跑过了
# AGG_VALUES = ["max", "sum", "avg_nonzero", "top3_avg"]
AGG_VALUES = ["avg_nonzero", "top3_avg", "top5_avg"]


def tokenize(text: str) -> list[str]:
    return [w for w in jieba.cut(text) if w.strip() and len(w) > 1]


def agg_scores(sc: list[float], strategy: str) -> float:
    if strategy == "max":
        return max(sc)
    if strategy == "sum":
        return sum(sc)
    if strategy == "avg_nonzero":
        nonzero = [s for s in sc if s > 0]
        return sum(nonzero) / len(nonzero) if nonzero else 0.0
    if strategy == "top3_avg":
        top3 = sorted(sc, reverse=True)[:3]
        return sum(top3) / len(top3)
    if strategy == "top5_avg":
        top5 = sorted(sc, reverse=True)[:5]
        return sum(top5) / len(top5)
    raise ValueError(f"未知聚合策略: {strategy}")


def classify_with_scores(bm25, doc_labels, tokenized_queries, agg):
    results = []
    for tok_q in tokenized_queries:
        if not tok_q:
            results.append(LABELS[0])
            continue
        scores = bm25.get_scores(tok_q)
        category_scores = defaultdict(list)
        for score, label in zip(scores, doc_labels):
            category_scores[label].append(score)
        agg_map = {cat: agg_scores(sc, agg) for cat, sc in category_scores.items()}
        results.append(max(agg_map, key=agg_map.get))
    return results


def main():
    # 1. 加载 jieba 词典
    if not os.path.exists(JIEBA_DICT):
        raise FileNotFoundError(f"jieba 词典不存在: {JIEBA_DICT}")
    jieba.load_userdict(str(JIEBA_DICT))

    # 2. 预分词：文档和查询各只做一次
    catalog_df = pd.read_parquet(CATALOG_PARQUET)
    doc_labels = catalog_df["一级序号/产品类别"].tolist()
    tokenized_docs = [tokenize(doc) for doc in catalog_df["完整结构"].fillna("")]
    print(f"[分词] 文档分词完成: {len(tokenized_docs)} 篇")

    patent_df = pd.read_parquet(PATENT_PARQUET, columns=["申请号", "标题", "摘要"])
    queries = [f"{row['标题']} {row['摘要']}" for _, row in patent_df.iterrows()]
    tokenized_queries = [tokenize(q) for q in queries]
    print(f"[分词] 查询分词完成: {len(tokenized_queries)} 条")

    # 3. 真实标签
    xlsx_df = pd.read_excel(base / "input" / "D2.xlsx",
                            usecols=["申请号", "一级产品类别（校对）"])
    true_map = dict(zip(xlsx_df["申请号"], xlsx_df["一级产品类别（校对）"]))

    out_df = pd.DataFrame({"申请号": patent_df["申请号"].tolist()})
    out_df["true_label"] = out_df["申请号"].map(true_map)

    # 追加模式：读取已有结果
    if os.path.exists(OUTPUT_XLSX):
        existing = pd.read_excel(OUTPUT_XLSX)
        for col in existing.columns:
            if col not in out_df.columns:
                out_df[col] = existing[col]
        print(f"[追加] 已有 {len(existing.columns) - 2} 列预测结果")

    # 4. 搜索
    total = len(K1_VALUES) * len(B_VALUES) * len(AGG_VALUES)
    done = 0

    for k1 in K1_VALUES:
        for b in B_VALUES:
            bm25 = BM25Okapi(tokenized_docs, k1=k1, b=b)
            for agg in AGG_VALUES:
                done += 1
                col = f"pred_k1{k1}_b{b}_{agg}"
                print(f"[{done}/{total}] k1={k1}, b={b}, agg={agg}", end="", flush=True)
                results = classify_with_scores(bm25, doc_labels, tokenized_queries, agg)
                out_df[col] = results
                acc = (out_df["true_label"] == out_df[col]).mean()
                print(f"  acc={acc:.4f}")

    out_df.to_excel(OUTPUT_XLSX, index=False)
    print(f"\n[完成] {total} 组超参数组合 → {OUTPUT_XLSX}")


if __name__ == "__main__":
    main()
