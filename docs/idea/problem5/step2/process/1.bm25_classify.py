"""
BM25 关键词匹配标注方案（Baseline ①）

文档粒度：三级条目，按一级类别聚合得分
文档内容：完整结构列
分词：jieba + 自定义医疗器械词典
聚合策略：max / sum（可配）
"""
import os
import jieba
import pandas as pd
from pathlib import Path
from rank_bm25 import BM25Okapi
from collections import defaultdict

# ── 路径 ──────────────────────────────────────────────
base = Path(__file__).resolve().parent.parent
JIEBA_DICT = base / "output" / "jieba_dict" / "医疗器械术语_合并.txt"
CATALOG_PARQUET = base / "output" / "医疗器械分类目录_eb_with_full_structure_normalized.parquet"
PATENT_PARQUET = base / "output" / "D2_eb.parquet"
OUTPUT_XLSX = base / "output" / "bm25_results.xlsx"

# ── 22 类标签 ─────────────────────────────────────────
LABELS = [
    "有源手术器械", "无源手术器械", "神经和心血管手术器械", "骨科手术器械",
    "放射治疗器械", "医用成像器械", "医用诊察和监护器械", "呼吸、麻醉和急救器械",
    "物理治疗器械", "输血、透析和体外循环器械", "医疗器械消毒灭菌器械",
    "有源植入器械", "无源植入器械", "注输、护理和防护器械",
    "患者承载器械", "眼科器械", "口腔科器械", "妇产科、辅助生殖和避孕器械",
    "医用康复器械", "中医器械", "医用软件", "临床检验器械"
]


def load_jieba_dict(dict_path: str):
    if not os.path.exists(dict_path):
        raise FileNotFoundError(f"jieba 词典不存在: {dict_path}")
    jieba.load_userdict(dict_path)


def tokenize(text: str) -> list[str]:
    return [w for w in jieba.cut(text) if w.strip() and len(w) > 1]


def build_bm25_index(catalog_df: pd.DataFrame, k1: float = 1.5, b: float = 0.75):
    docs = catalog_df["完整结构"].fillna("").tolist()
    labels = catalog_df["一级序号/产品类别"].tolist()
    tokenized_docs = [tokenize(doc) for doc in docs]
    bm25 = BM25Okapi(tokenized_docs, k1=k1, b=b)
    return bm25, labels


def classify_query(bm25: BM25Okapi, doc_labels: list[str], query: str,
                   agg: str = "max") -> str:
    tokenized_query = tokenize(query)
    if not tokenized_query:
        return LABELS[0]

    scores = bm25.get_scores(tokenized_query)

    category_scores = defaultdict(list)
    for score, label in zip(scores, doc_labels):
        category_scores[label].append(score)

    if agg == "max":
        agg_scores = {cat: max(sc) for cat, sc in category_scores.items()}
    else:
        agg_scores = {cat: sum(sc) for cat, sc in category_scores.items()}

    return max(agg_scores, key=agg_scores.get)


def run_bm25(catalog_df: pd.DataFrame, patent_df: pd.DataFrame,
             k1: float = 1.5, b: float = 0.75, agg: str = "max") -> list[str]:
    """执行一次 BM25 分类，返回预测标签列表"""
    bm25, doc_labels = build_bm25_index(catalog_df, k1=k1, b=b)
    results = []
    for _, row in patent_df.iterrows():
        query = f"{row['标题']} {row['摘要']}"
        results.append(classify_query(bm25, doc_labels, query, agg=agg))
    return results


def main():
    k1 = 1.5
    b = 0.75
    agg = "max"

    load_jieba_dict(str(JIEBA_DICT))
    catalog_df = pd.read_parquet(CATALOG_PARQUET)
    patent_df = pd.read_parquet(PATENT_PARQUET, columns=["申请号", "标题", "摘要"])

    print(f"[BM25] k1={k1}, b={b}, agg={agg}, 专利数={len(patent_df)}")
    results = run_bm25(catalog_df, patent_df, k1=k1, b=b, agg=agg)

    # 输出到 xlsx（参考 llm_zeroshot_results.xlsx 格式）
    # 读取真实标签
    xlsx_df = pd.read_excel(base / "input" / "D2.xlsx",
                            columns=["申请号", "一级产品类别（校对）"])
    # 从 parquet 获取申请号保序
    ids = patent_df["申请号"].tolist()
    true_map = dict(zip(xlsx_df["申请号"], xlsx_df["一级产品类别（校对）"]))

    out_df = pd.DataFrame({"申请号": ids})
    out_df["true_label"] = out_df["申请号"].map(true_map)
    col_name = f"pred_k1{k1}_b{b}_{agg}"
    out_df[col_name] = results
    out_df.to_excel(OUTPUT_XLSX, index=False)
    print(f"[输出] {OUTPUT_XLSX}")


if __name__ == "__main__":
    main()
