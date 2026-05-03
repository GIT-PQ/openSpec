"""
task6 BGE向量相似度分析
分析增强数据与原始数据之间的语义相似度，佐证LLM改写未发生语义偏移

数据来源:
  - 增强数据集: problem6/input/增强数据集_输血透析体外循环.parquet
  - 原始数据集: start/output/数据集_D2_D3高置信.parquet

三个相似度指标:
  1. 增强-原始（同申请号）: 每条增强摘要与同一申请号的原始摘要的余弦相似度
  2. 原始类内（同类不同专利）: 同类别中不同专利摘要两两之间的余弦相似度，作为参照基准
  3. 增强类内: 增强摘要两两之间的余弦相似度

计算流程:
  1. 读取bge列（未归一化嵌入向量）
  2. 在内存中L2归一化（不写回原文件）
  3. 计算余弦相似度（归一化后点积）
  4. 分组统计并输出
"""

import pandas as pd
import numpy as np
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from itertools import combinations
import sys
import os

sys.stdout.reconfigure(encoding='utf-8')

# ============================================================
# 配置
# ============================================================
SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
PROJECT_DIR = os.path.dirname(os.path.dirname(SCRIPT_DIR))

AUG_PATH = os.path.join(PROJECT_DIR, 'problem6', 'input', '增强数据集_输血透析体外循环.parquet')
ORIG_PATH = os.path.join(PROJECT_DIR, 'start', 'output', '数据集_D2_D3高置信.parquet')
TARGET_LABEL = '输血、透析和体外循环器械'
OUTPUT_DIR = SCRIPT_DIR

# ============================================================
# 1. 读取数据
# ============================================================
aug = pd.read_parquet(AUG_PATH)
orig_all = pd.read_parquet(ORIG_PATH)
orig = orig_all[orig_all['last_label'] == TARGET_LABEL].copy()

print(f'增强数据集记录数: {len(aug)}')
print(f'原始数据集({TARGET_LABEL})记录数: {len(orig)}')

# ============================================================
# 2. 申请号关联
# ============================================================
aug_ids = aug['申请号'].values
orig_ids = orig['申请号'].values
orig_id_to_idx = {aid: idx for idx, aid in enumerate(orig_ids)}

matched = sum(1 for aid in aug_ids if aid in orig_id_to_idx)
unmatched_list = [aid for aid in aug_ids if aid not in orig_id_to_idx]
print(f'匹配成功: {matched}, 未匹配: {len(unmatched_list)}')
if unmatched_list:
    for aid in set(unmatched_list):
        print(f'  未匹配申请号: {aid}')

# ============================================================
# 3. 提取bge向量，内存中L2归一化
# ============================================================
aug_bge = np.stack(aug['bge'].values)
orig_bge = np.stack(orig['bge'].values)

aug_bge_norm = aug_bge / np.linalg.norm(aug_bge, axis=1, keepdims=True)
orig_bge_norm = orig_bge / np.linalg.norm(orig_bge, axis=1, keepdims=True)

# ============================================================
# 4. 计算增强-原始相似度（同申请号）
# ============================================================
aug_orig_sim = []
for i, aid in enumerate(aug_ids):
    if aid in orig_id_to_idx:
        j = orig_id_to_idx[aid]
        sim = np.dot(aug_bge_norm[i], orig_bge_norm[j])
        aug_orig_sim.append(sim)
aug_orig_sim = np.array(aug_orig_sim)

# ============================================================
# 5. 计算原始类内两两相似度（同类不同专利间）
# ============================================================
orig_intra_sims = []
for i, j in combinations(range(len(orig)), 2):
    sim = np.dot(orig_bge_norm[i], orig_bge_norm[j])
    orig_intra_sims.append(sim)
orig_intra_sims = np.array(orig_intra_sims)

# ============================================================
# 6. 计算增强类内两两相似度
# ============================================================
aug_intra_sims = []
for i, j in combinations(range(len(aug)), 2):
    sim = np.dot(aug_bge_norm[i], aug_bge_norm[j])
    aug_intra_sims.append(sim)
aug_intra_sims = np.array(aug_intra_sims)

# ============================================================
# 7. 输出统计
# ============================================================
def print_stats(name, data):
    print(f'\n{"="*60}')
    print(f'{name}')
    print(f'{"="*60}')
    print(f'  样本数: {len(data)}')
    print(f'  均值:   {data.mean():.4f}')
    print(f'  标准差: {data.std():.4f}')
    print(f'  最小值: {data.min():.4f}')
    print(f'  最大值: {data.max():.4f}')
    print(f'  中位数: {np.median(data):.4f}')
    for q in [0.01, 0.05, 0.10, 0.25, 0.50, 0.75, 0.90, 0.95, 0.99]:
        print(f'  P{int(q*100):02d}:    {np.percentile(data, q*100):.4f}')

print_stats('一、增强数据 vs 对应原始数据（同申请号）', aug_orig_sim)
print_stats('二、原始数据类内两两相似度（同类不同专利间）', orig_intra_sims)
print_stats('三、增强数据类内两两相似度', aug_intra_sims)

# 关键对比
print(f'\n{"="*60}')
print('四、关键对比')
print(f'{"="*60}')
print(f'  增强-原始均值 / 原始类内均值 = {aug_orig_sim.mean():.4f} / {orig_intra_sims.mean():.4f} = {aug_orig_sim.mean()/orig_intra_sims.mean():.2f}x')
print(f'  增强-原始P5 ({np.percentile(aug_orig_sim,5):.4f}) vs 原始类内P95 ({np.percentile(orig_intra_sims,95):.4f})')
print(f'  增强-原始最小值 ({aug_orig_sim.min():.4f}) vs 原始类内均值 ({orig_intra_sims.mean():.4f})')

# 每个申请号明细
print(f'\n{"="*60}')
print('五、每个申请号的增强-原始相似度明细')
print(f'{"="*60}')
aug_orig_detail = {}
for i, aid in enumerate(aug_ids):
    if aid in orig_id_to_idx:
        j = orig_id_to_idx[aid]
        sim = np.dot(aug_bge_norm[i], orig_bge_norm[j])
        if aid not in aug_orig_detail:
            aug_orig_detail[aid] = []
        aug_orig_detail[aid].append(sim)

for aid, sims in sorted(aug_orig_detail.items()):
    sims_arr = np.array(sims)
    print(f'  {aid} | n={len(sims)} | mean={sims_arr.mean():.4f} | min={sims_arr.min():.4f} | max={sims_arr.max():.4f}')

# ============================================================
# 8. 绘图保存
# ============================================================
plt.rcParams['font.sans-serif'] = ['SimHei']
plt.rcParams['axes.unicode_minus'] = False

fig, axes = plt.subplots(1, 3, figsize=(18, 5))

axes[0].hist(aug_orig_sim, bins=20, color='steelblue', edgecolor='white', alpha=0.8)
axes[0].set_title('增强 vs 原始 (同申请号)', fontsize=13)
axes[0].set_xlabel('余弦相似度')
axes[0].set_ylabel('频数')
axes[0].axvline(aug_orig_sim.mean(), color='red', linestyle='--', label=f'Mean={aug_orig_sim.mean():.4f}')
axes[0].legend()

axes[1].hist(orig_intra_sims, bins=20, color='darkorange', edgecolor='white', alpha=0.8)
axes[1].set_title('原始类内两两相似度', fontsize=13)
axes[1].set_xlabel('余弦相似度')
axes[1].set_ylabel('频数')
axes[1].axvline(orig_intra_sims.mean(), color='red', linestyle='--', label=f'Mean={orig_intra_sims.mean():.4f}')
axes[1].legend()

axes[2].hist(aug_intra_sims, bins=20, color='green', edgecolor='white', alpha=0.8)
axes[2].set_title('增强类内两两相似度', fontsize=13)
axes[2].set_xlabel('余弦相似度')
axes[2].set_ylabel('频数')
axes[2].axvline(aug_intra_sims.mean(), color='red', linestyle='--', label=f'Mean={aug_intra_sims.mean():.4f}')
axes[2].legend()

plt.tight_layout()
save_path = os.path.join(OUTPUT_DIR, 'similarity_distribution.png')
plt.savefig(save_path, dpi=150, bbox_inches='tight')
plt.close()
print(f'\n图片已保存到: {save_path}')
