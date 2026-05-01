"""
KNN + BGE 语义匹配标注 - 方法③
基于BGE嵌入的KNN分类，超参数搜索 + acc/macro-f1评估
"""

import numpy as np
import pandas as pd
from sklearn.metrics import accuracy_score, f1_score
from sklearn.metrics.pairwise import cosine_similarity
from collections import Counter
import os

# ========== 路径 ==========
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
INPUT_DIR = os.path.join(BASE_DIR, "input")
OUTPUT_DIR = os.path.join(BASE_DIR, "output")

# ========== 标签 ==========
LABELS = [
    "有源手术器械", "无源手术器械", "神经和心血管手术器械", "骨科手术器械",
    "放射治疗器械", "医用成像器械", "医用诊察和监护器械", "呼吸、麻醉和急救器械",
    "物理治疗器械", "输血、透析和体外循环器械", "医疗器械消毒灭菌器械",
    "有源植入器械", "无源植入器械", "注输、护理和防护器械",
    "患者承载器械", "眼科器械", "口腔科器械", "妇产科、辅助生殖和避孕器械",
    "医用康复器械", "中医器械", "医用软件", "临床检验器械",
]

# ========== 加载数据 ==========
print("加载数据...")
patent_df = pd.read_parquet(os.path.join(OUTPUT_DIR, "D2_eb.parquet"))
catalog_df = pd.read_parquet(
    os.path.join(OUTPUT_DIR, "医疗器械分类目录_eb_with_full_structure_normalized.parquet")
)
d2_xlsx = pd.read_excel(os.path.join(INPUT_DIR, "D2.xlsx"))

# 真实标签来自 D2.xlsx
gt = d2_xlsx[["申请号", "一级产品类别（校对）"]].dropna(subset=["一级产品类别（校对）"])
patent_df = patent_df.merge(gt, on="申请号", how="inner")

print(f"有效专利: {len(patent_df)}, 分类目录条目: {len(catalog_df)}")

# ========== 构建矩阵 ==========
patent_embs = np.stack(patent_df["bge"].values)
catalog_embs = np.stack(catalog_df["完整结构_eb_归一化"].values)
catalog_labels = catalog_df["一级序号/产品类别"].values

print(f"专利嵌入: {patent_embs.shape}, 目录嵌入: {catalog_embs.shape}")

# ========== 余弦相似度 ==========
print("计算余弦相似度...")
sim_matrix = cosine_similarity(patent_embs, catalog_embs)
print(f"相似度矩阵: {sim_matrix.shape}")


# ========== KNN分类 ==========
def knn_classify(sim_matrix, catalog_labels, k, weighted=False):
    predictions = []
    for i in range(sim_matrix.shape[0]):
        top_idx = np.argpartition(sim_matrix[i], -k)[-k:]
        top_sims = sim_matrix[i][top_idx]
        top_labels = catalog_labels[top_idx]

        if weighted:
            scores = {}
            for label, sim in zip(top_labels, top_sims):
                scores[label] = scores.get(label, 0) + sim
            pred = max(scores, key=scores.get)
        else:
            counts = Counter(top_labels)
            max_count = counts.most_common(1)[0][1]
            tied = [l for l, c in counts.items() if c == max_count]
            if len(tied) == 1:
                pred = tied[0]
            else:
                # 票数相同时按相似度之和破局
                scores = {}
                for label, sim in zip(top_labels, top_sims):
                    if label in tied:
                        scores[label] = scores.get(label, 0) + sim
                pred = max(scores, key=scores.get)

        predictions.append(pred)
    return predictions


# ========== 超参数搜索 ==========
K_VALUES = list(range(1, 24, 2))
VOTING = [("majority", False), ("weighted", True)]

y_true = patent_df["一级产品类别（校对）"].values
eval_results = []
pred_cols = {}

for k in K_VALUES:
    for vname, weighted in VOTING:
        print(f"K={k}, voting={vname}...", end=" ")
        y_pred = knn_classify(sim_matrix, catalog_labels, k, weighted)

        acc = accuracy_score(y_true, y_pred)
        macro_f1 = f1_score(y_true, y_pred, labels=LABELS, average="macro", zero_division=0)

        eval_results.append({"K": k, "voting": vname, "accuracy": round(acc, 4), "macro_f1": round(macro_f1, 4)})

        col = f"knn_k{k}_{vname}"
        pred_cols[col] = y_pred
        print(f"Acc={acc:.4f}  MacroF1={macro_f1:.4f}")

# ========== 保存评估结果 ==========
eval_df = pd.DataFrame(eval_results)
eval_path = os.path.join(OUTPUT_DIR, "knn_bge_eval_results.xlsx")
eval_df.to_excel(eval_path, index=False)
print(f"\n评估结果: {eval_path}")

# ========== 保存预测结果 ==========
pred_df = patent_df[["申请号", "标题", "摘要", "一级产品类别（原始）", "一级产品类别（校对）"]].copy()
for col, preds in pred_cols.items():
    pred_df[col] = preds
pred_path = os.path.join(OUTPUT_DIR, "knn_bge_predictions.xlsx")
pred_df.to_excel(pred_path, index=False)
print(f"预测结果: {pred_path}")

print("\n完成!")
