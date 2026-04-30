# KNN + BGE 语义匹配标注方案

## 目标

作为实验对照组③，验证基于语义嵌入的检索方法在医疗器械专利分类上的表现，填补词法匹配（BM25）与LLM推理（RAG+规则）之间的空白。

## 方法定位

```
方法              匹配方式      领域知识         语义能力
──────────────────────────────────────────────────────
① BM25            词法匹配      分类目录(文档)    ✗
② LLM zero-shot   推理          ✗               ✓
③ KNN + BGE       语义匹配      分类目录(嵌入)    ✓    ← 本方案
④ 你的方法         RAG+规则+LLM  分类目录+规则     ✓
```

对比链条：
- ① → ③：语义嵌入 > 词法匹配，证明embedding的价值
- ③ → ④：RAG+规则引导 > 纯嵌入相似度，证明LLM推理+规则的增量价值
- ② → ③/④：领域知识注入 > 裸LLM，证明领域适配的必要性

## 方法概述

```
分类目录 xlsx（22个sheet，每sheet多条记录）
      │
      ▼
┌──────────────────────────────────────────┐
│  Step 1: 构建分类目录向量库               │
│  每条记录（品名+描述+用途）→ BGE 嵌入      │
│  保留类别标签作为 ground truth             │
└──────────────┬───────────────────────────┘
               │
               ▼
┌──────────────────────────────────────────┐
│  Step 2: 专利文本嵌入 + KNN 检索           │
│  专利（标题+摘要）→ BGE 嵌入               │
│  → 与向量库计算余弦相似度                  │
│  → 取 K 个最近邻 → 投票/加权投票 → 类别    │
└──────────────┬───────────────────────────┘
               │
               ▼
         分类结果
```

**核心设计：** 按条目嵌入而非按类别聚合。同一类下条目差异可能很大（如"有源手术器械"下既有超声刀也有激光设备），按条目嵌入再投票能更好地捕捉类内多样性。

## 物料

| 物料 | 来源 | 用途 |
|------|------|------|
| 医疗器械分类目录 | `work/data/医疗器械分类目录.xlsx` | 22个sheet，每条记录嵌入为向量 |
| BGE-large-zh-v1.5 | BAAI开源模型 | 中文文本嵌入模型，1024维 |
| 待标注数据 | ~1100条专利 | 含标题、摘要、原始分类标签 |

## 为什么选 BGE-large-zh-v1.5

| 考量 | 说明 |
|------|------|
| 中文能力 | MTEB中文榜单排名靠前，专为中文优化 |
| 向量维度 | 1024维，语义表达充分 |
| 开源可用 | HuggingFace可下载，无需API调用 |
| 社区验证 | 被广泛用于中文检索/分类任务，结果可信 |

## 实现步骤

### Step 1: 构建分类目录向量库

```python
import pandas as pd
import numpy as np
from sentence_transformers import SentenceTransformer
import json
from tqdm import tqdm

# 加载BGE模型
model = SentenceTransformer('BAAI/bge-large-zh-v1.5')

# 读取分类目录，按条目构建语料
LABELS = [
    '中医器械', '临床检验器械', '医用康复器械', '医用成像器械', '医用诊察和监护器械', '医用软件',
    '医疗器械消毒灭菌器械', '口腔科器械', '呼吸、麻醉和急救器械', '妇产科、辅助生殖和避孕器械',
    '患者承载器械', '放射治疗器械', '无源手术器械', '无源植入器械', '有源手术器械', '有源植入器械',
    '注输、护理和防护器械', '物理治疗器械', '眼科器械', '神经和心血管手术器械', '输血、透析和体外循环器械', '骨科手术器械'
]

xls = pd.ExcelFile("work/data/医疗器械分类目录.xlsx")

catalog_texts = []   # 每条记录的拼接文本
catalog_labels = []  # 对应的类别标签（0-indexed）

for label_idx, label in enumerate(LABELS):
    for sheet_name in xls.sheet_names:
        if label in sheet_name:
            df = pd.read_excel(xls, sheet_name=sheet_name, header=0)
            for _, row in df.iterrows():
                parts = []
                for col in ['品名举例', '产品描述', '预期用途']:
                    val = row.get(col, '')
                    if pd.notna(val) and str(val).strip():
                        parts.append(str(val).strip())
                if parts:
                    catalog_texts.append(" ".join(parts))
                    catalog_labels.append(label_idx)
            break

xls.close()

print(f"分类目录共 {len(catalog_texts)} 条记录，覆盖 {len(set(catalog_labels))} 个类别")

# BGE推荐：在文本前加指令以提升检索效果
instruction = "为这个医疗器械专利文本生成表示以用于检索相关类别："
catalog_texts_instruction = [instruction + t for t in catalog_texts]

# 批量嵌入
catalog_embeddings = model.encode(
    catalog_texts_instruction,
    batch_size=64,
    show_progress_bar=True,
    normalize_embeddings=True  # BGE推荐：归一化后直接用点积=余弦相似度
)

# 构建DataFrame保存为parquet（跨平台，含向量+元数据）
catalog_df = pd.DataFrame({
    "text": catalog_texts,
    "label_idx": catalog_labels,
    "label": [LABELS[i] for i in catalog_labels],
    "embedding": catalog_embeddings.tolist()  # 每行一个list，parquet原生支持
})
catalog_df.to_parquet("work/data/catalog_vectors.parquet", index=False)
print(f"向量库保存完成：{catalog_embeddings.shape}，共 {len(catalog_df)} 条记录")
```

### Step 2: KNN 分类

```python
from sklearn.metrics.pairwise import cosine_similarity

def classify_patent_knn(title: str, abstract: str, model, catalog_embeddings,
                        catalog_labels, labels, k=5, weighted=True) -> dict:
    """
    使用KNN+BGE对专利文本进行分类

    Args:
        title: 专利标题
        abstract: 专利摘要
        model: BGE嵌入模型
        catalog_embeddings: 分类目录向量库 (N, 1024)
        catalog_labels: 分类目录类别标签 (N,)
        labels: 类别名称列表
        k: 近邻数量
        weighted: 是否使用距离加权投票

    Returns:
        dict: 包含预测类别、top-5类别及分数
    """
    # 嵌入查询文本
    query_text = f"{title} {abstract}"
    instruction = "为这个医疗器械专利文本生成表示以用于检索相关类别："
    query_embedding = model.encode(
        [instruction + query_text],
        normalize_embeddings=True
    )

    # 计算相似度
    similarities = cosine_similarity(query_embedding, catalog_embeddings)[0]

    # 取top-k近邻
    top_k_indices = np.argsort(similarities)[-k:][::-1]
    top_k_sims = similarities[top_k_indices]
    top_k_labels = catalog_labels[top_k_indices]

    # 投票
    vote_scores = np.zeros(len(labels))
    for i in range(k):
        label_idx = top_k_labels[i]
        if weighted:
            # 加权投票：权重=相似度
            vote_scores[label_idx] += top_k_sims[i]
        else:
            # 等权投票
            vote_scores[label_idx] += 1

    # 排序
    sorted_indices = np.argsort(vote_scores)[::-1]

    result = {
        "pred_label": labels[sorted_indices[0]],
        "pred_score": float(vote_scores[sorted_indices[0]]),
        "top5": [
            {"label": labels[idx], "score": float(vote_scores[idx])}
            for idx in sorted_indices[:5]
        ],
        "top_k_details": [
            {"label": labels[top_k_labels[i]], "similarity": float(top_k_sims[i]),
             "matched_text": catalog_texts[top_k_indices[i]][:80]}
            for i in range(k)
        ]
    }

    return result
```

### Step 3: 批量标注并评估

```python
# 加载向量库
catalog_df = pd.read_parquet("work/data/catalog_vectors.parquet")
catalog_embeddings = np.array(catalog_df["embedding"].tolist())
catalog_labels = catalog_df["label_idx"].values

# 加载待标注数据
df = pd.read_json("待标注数据路径")

# K值实验：尝试多个K值
for k in [1, 3, 5, 7]:
    results = []
    for _, row in tqdm(df.iterrows(), total=len(df), desc=f"K={k}"):
        pred = classify_patent_knn(
            row["title"], row["abstract"],
            model, catalog_embeddings, catalog_labels,
            LABELS, k=k, weighted=True
        )
        results.append({
            "patent_id": row.get("id", ""),
            "title": row["title"],
            "true_label": row["label"],
            "pred_label": pred["pred_label"],
            "pred_score": pred["pred_score"],
        })

    result_df = pd.DataFrame(results)
    result_df.to_csv(f"knn_bge_k{k}_results.csv", index=False, encoding="utf-8-sig")

    from sklearn.metrics import classification_report, accuracy_score
    acc = accuracy_score(result_df['true_label'], result_df['pred_label'])
    print(f"\nK={k} | Accuracy: {acc:.4f}")
    print(classification_report(result_df['true_label'], result_df['pred_label']))
```

## K值选择策略

| K值 | 特点 | 适用场景 |
|-----|------|----------|
| K=1 | 最近邻，完全依赖最相似条目 | 类内紧凑、类间分离好 |
| K=3 | 少数投票，抗噪声 | 推荐：平衡精度与鲁棒性 |
| K=5 | 多数投票，更鲁棒 | 类内条目多、噪声多 |
| K=7 | 大数投票，偏保守 | 类别边界模糊时 |

**建议：** 实验中测试K=1,3,5,7，选择最优K值作为最终结果。论文中可报告不同K值的表现，展示方法的稳定性。

## BGE 使用注意事项

| 要点 | 说明 |
|------|------|
| 指令前缀 | BGE模型推荐在查询文本前加指令前缀以提升检索效果，文档侧不需要加 |
| 归一化 | `normalize_embeddings=True`，归一化后点积=余弦相似度，计算更快 |
| 文本长度 | BGE-large-zh-v1.5 最大512 tokens，分类目录条目和专利摘要通常在范围内 |
| 批量编码 | 使用batch_size=64加速，GPU环境下约10分钟可完成全量嵌入 |

## 评估指标

| 指标 | 说明 |
|------|------|
| Accuracy | 整体准确率 |
| Precision/Recall/F1 (per class) | 每类别的精确率/召回率/F1 |
| Macro-F1 | 宏平均F1（处理类别不平衡） |
| Weighted-F1 | 加权F1 |
| K值对比 | 不同K值的准确率变化 |

## 预期结果与分析要点

### 预期表现

KNN+BGE 在以下类别上可能表现较好：
- **品名明确的类别**：如"骨科手术器械""眼科器械"——专利文本与分类目录条目语义接近
- **条目丰富的类别**：分类目录中条目多，嵌入覆盖更全面

KNN+BGE 在以下类别上可能表现较差：
- **功能交叉的类别**：如"物理治疗器械"vs"医用成像器械"——超声相关条目语义相近但类别不同
- **条目稀少的类别**：分类目录中条目少，嵌入空间覆盖不足
- **描述抽象的专利**：专利摘要偏方法论而非具体产品，与分类目录条目语义距离远

### 论文分析角度

1. **KNN+BGE vs BM25**：语义匹配能否超越词法匹配？在哪些类别上优势明显？
2. **KNN+BGE vs LLM zero-shot**：领域知识（分类目录嵌入）vs LLM自身知识，谁更强？
3. **KNN+BGE vs 你的方法**：纯相似度检索 vs RAG+规则+LLM推理，LLM推理和分类规则的增量价值有多大？
4. **K值敏感性**：K=1时可能过拟合噪声条目，K增大后投票更稳健但可能引入错误类别

## 依赖

```
sentence-transformers>=2.2.0
torch>=1.12.0
scikit-learn
pandas
numpy
tqdm
openpyxl
```