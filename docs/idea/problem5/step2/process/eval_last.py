import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
from sklearn.metrics import (
    accuracy_score, precision_score, recall_score, f1_score,
    classification_report, confusion_matrix
)
from statsmodels.stats.inter_rater import fleiss_kappa

plt.rcParams['font.sans-serif'] = ['SimHei']

# ==================== 配置 ====================
INPUT_PATH = "../input/D2.xlsx"
REAL_COL = "一级产品类别（校对）"
V16_ENSEMBLE_COL = "一级产品类别（v16模型众数）"
V16_PREDICTION_COLS = [f"v16_top5_local_qwen3_{i}" for i in range(1, 11)]
LAST_PREDICTION_COLS = [f"last_label_{i}" for i in range(1, 11)]
LAST_ENSEMBLE_COL = "一级产品类别（last模型众数）"

# ==================== 读取数据 ====================
data = pd.read_excel(INPUT_PATH)
print(f"总行数: {len(data)}")

# ==================== 合并预测列 ====================
# v16预测正确的行：取v16的10列预测
# v16预测错误的行：取last的10列预测
merged_cols = [f"merged_{i}" for i in range(1, 11)]
v16_error_mask = data["v16预测错误"] == True

for i, (v16_col, last_col, merged_col) in enumerate(
    zip(V16_PREDICTION_COLS, LAST_PREDICTION_COLS, merged_cols)
):
    data[merged_col] = data[v16_col]
    data.loc[v16_error_mask, merged_col] = data.loc[v16_error_mask, last_col]

# 合并列取众数
data[LAST_ENSEMBLE_COL] = data[merged_cols].mode(axis=1)[0]

print(f"\nlast模型众数分布:")
print(data[LAST_ENSEMBLE_COL].value_counts())

# ==================== 筛选真实标签非空 ====================
notnull_df = data[data[REAL_COL].notnull()].copy()
all_labels = sorted(notnull_df[REAL_COL].unique())

# ==================== Fleiss' Kappa ====================
def count_votes(row):
    return [list(row).count(label) for label in all_labels]

vote_matrix = notnull_df[merged_cols].apply(count_votes, axis=1, result_type='expand')
vote_matrix.columns = all_labels
kappa_score = fleiss_kappa(vote_matrix.values)
print(f"\nFleiss' Kappa: {kappa_score:.4f}")

# ==================== 各轮指标 ====================
print("\n各轮预测指标:")
metrics_result = {}
for col in merged_cols:
    y_true = notnull_df[REAL_COL]
    y_pred = notnull_df[col]
    acc = accuracy_score(y_true, y_pred)
    macro_p = precision_score(y_true, y_pred, average='macro', zero_division=0)
    weighted_p = precision_score(y_true, y_pred, average='weighted', zero_division=0)
    metrics_result[col] = {"accuracy": acc, "macro_precision": macro_p, "weighted_precision": weighted_p}
    print(f"  {col}: accuracy={acc:.4f}, macro_precision={macro_p:.4f}, weighted_precision={weighted_p:.4f}")

# ==================== 众数指标 ====================
print(f"\n==== {LAST_ENSEMBLE_COL} ====")
y_true = notnull_df[REAL_COL]
y_pred = notnull_df[LAST_ENSEMBLE_COL]

acc = accuracy_score(y_true, y_pred)
macro_p = precision_score(y_true, y_pred, average='macro', zero_division=0)
weighted_p = precision_score(y_true, y_pred, average='weighted', zero_division=0)
macro_r = recall_score(y_true, y_pred, average='macro', zero_division=0)
macro_f1 = f1_score(y_true, y_pred, average='macro', zero_division=0)

print(f"准确率 Accuracy: {acc:.4f}")
print(f"精确率 Precision (Macro): {macro_p:.4f}")
print(f"精确率 Precision (Weighted): {weighted_p:.4f}")
print(f"召回率 Recall (Macro): {macro_r:.4f}")
print(f"F1 分数 F1 (Macro): {macro_f1:.4f}")

# ==================== 每类别详细统计 ====================
print("\n每类别统计表：")
report = classification_report(y_true, y_pred, digits=4, output_dict=True)
report_df = pd.DataFrame(report).transpose()
report_df["support"] = report_df["support"].astype(int)
report_df = report_df.sort_values(by="f1-score", ascending=False)
print(report_df)

# ==================== 各类错误率 & 置信度分层对比 ====================
print("\n各类错误率：")
per_class_err = {}
for label in all_labels:
    mask = y_true == label
    if mask.sum() > 0:
        label_err = 1 - accuracy_score(y_true[mask], y_pred[mask])
        per_class_err[label] = label_err
        print(f"  {label}: {label_err:.4f} (n={mask.sum()})")

err_values = list(per_class_err.values())
print(f"\n22类错误率统计: min={min(err_values):.4f}, max={max(err_values):.4f}, "
      f"range={max(err_values)-min(err_values):.4f}, std={pd.Series(err_values).std():.4f}")

# 高/低置信分层
orig_col = "一级产品类别（原始）"
if orig_col in notnull_df.columns:
    high_mask = notnull_df[orig_col] == y_pred
    low_mask = ~high_mask

    high_err = 1 - accuracy_score(y_true[high_mask], y_pred[high_mask])
    low_err = 1 - accuracy_score(y_true[low_mask], y_pred[low_mask])

    print(f"\n置信度分层错误率:")
    print(f"  高置信(原始=工作流): {high_err:.4f} (n={high_mask.sum()})")
    print(f"  低置信(原始≠工作流): {low_err:.4f} (n={low_mask.sum()})")
    print(f"  差距: {abs(high_err - low_err):.4f} ({abs(high_err - low_err)*100:.2f}pp)")
    print(f"\n区分度对比: 22类错误率极差={max(err_values)-min(err_values):.4f} vs 置信度差距={abs(high_err-low_err):.4f}")

    # 各置信层内各类错误率
    for layer_name, layer_mask in [("高置信", high_mask), ("低置信", low_mask)]:
        print(f"\n{layer_name}层各类错误率：")
        layer_err = {}
        for label in all_labels:
            mask = (y_true == label) & layer_mask
            if mask.sum() > 0:
                e = 1 - accuracy_score(y_true[mask], y_pred[mask])
                layer_err[label] = e
                print(f"  {label}: {e:.4f} (n={mask.sum()})")
        if layer_err:
            vals = list(layer_err.values())
            print(f"  统计: min={min(vals):.4f}, max={max(vals):.4f}, "
                  f"range={max(vals)-min(vals):.4f}, std={pd.Series(vals).std():.4f}")
else:
    print(f"\n未找到'{orig_col}'列，跳过置信度分层计算")

# ==================== 混淆矩阵 ====================
cm = confusion_matrix(y_true, y_pred, labels=all_labels)
cm_df = pd.DataFrame(cm, index=all_labels, columns=all_labels)

plt.figure(figsize=(12, 10), dpi=200)
sns.heatmap(cm_df, annot=True, fmt='d', cmap='Blues')
plt.title(LAST_ENSEMBLE_COL)
plt.ylabel('真实标签')
plt.xlabel('预测标签')
plt.tight_layout()
plt.savefig("../output/last_confusion_matrix.png", bbox_inches='tight')
print("\n混淆矩阵已保存到 ../output/last_confusion_matrix.png")
plt.close()

# ==================== 对比v16 ====================
print("\n==== v16 vs last 对比 ====")
v16_acc = accuracy_score(y_true, notnull_df[V16_ENSEMBLE_COL])
v16_macro_p = precision_score(y_true, notnull_df[V16_ENSEMBLE_COL], average='macro', zero_division=0)
v16_weighted_p = precision_score(y_true, notnull_df[V16_ENSEMBLE_COL], average='weighted', zero_division=0)
v16_macro_r = recall_score(y_true, notnull_df[V16_ENSEMBLE_COL], average='macro', zero_division=0)
v16_macro_f1 = f1_score(y_true, notnull_df[V16_ENSEMBLE_COL], average='macro', zero_division=0)

print(f"{'指标':<25} {'v16':>8} {'last':>8} {'提升':>8}")
print("-" * 55)
for name, v16_val, last_val in [
    ("Accuracy", v16_acc, acc),
    ("Precision (Macro)", v16_macro_p, macro_p),
    ("Precision (Weighted)", v16_weighted_p, weighted_p),
    ("Recall (Macro)", v16_macro_r, macro_r),
    ("F1 (Macro)", v16_macro_f1, macro_f1),
]:
    diff = last_val - v16_val
    print(f"{name:<25} {v16_val:>8.4f} {last_val:>8.4f} {diff:>+8.4f}")

# 保存
data.to_excel(INPUT_PATH, index=False)
print(f"\n数据已保存到: {INPUT_PATH}")
