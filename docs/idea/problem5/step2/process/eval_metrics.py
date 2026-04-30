"""调用 metrics.py 计算分类评估指标"""

import pandas as pd
import numpy as np
from sklearn.metrics import accuracy_score, f1_score

LABELS = [
    "有源手术器械",
    "无源手术器械",
    "神经和心血管手术器械",
    "骨科手术器械",
    "放射治疗器械",
    "医用成像器械",
    "医用诊察和监护器械",
    "呼吸、麻醉和急救器械",
    "物理治疗器械",
    "输血、透析和体外循环器械",
    "医疗器械消毒灭菌器械",
    "有源植入器械",
    "无源植入器械",
    "注输、护理和防护器械",
    "患者承载器械",
    "眼科器械",
    "口腔科器械",
    "妇产科、辅助生殖和避孕器械",
    "医用康复器械",
    "中医器械",
    "医用软件",
    "临床检验器械",
]


def compute_mode_prediction(df: pd.DataFrame, pred_cols: list[str]) -> pd.Series:
    """计算多列预测的众数作为最终预测。

    Args:
        df: 数据框
        pred_cols: 预测列名列表

    Returns:
        众数预测的 Series。n=1 时直接返回该列；n>1 时返回众数。
    """
    if len(pred_cols) == 1:
        return df[pred_cols[0]].astype(str)

    # 使用 pandas 逐行计算众数
    def get_mode(row):
        modes = row.mode()
        return modes.iloc[0] if len(modes) > 0 else np.nan

    return df[pred_cols].astype(str).apply(get_mode, axis=1)


def evaluate_mode_prediction(
    df: pd.DataFrame,
    true_col: str,
    pred_cols: list[str],
    labels: list[str] | None = None,
) -> dict:
    """评估众数预测结果。

    Args:
        df: 数据框
        true_col: 真实标签列名
        pred_cols: 预测列名列表
        labels: 类别标签列表

    Returns:
        包含 accuracy、macro_f1、n_predictions 的字典
    """
    y_true = df[true_col].astype(str)
    y_pred = compute_mode_prediction(df, pred_cols)

    acc = accuracy_score(y_true, y_pred)
    f1 = f1_score(y_true, y_pred, average="macro", labels=labels, zero_division=0)

    return {
        "accuracy": acc,
        "macro_f1": f1,
        "n_predictions": len(pred_cols),
    }


def fleiss_kappa(df: pd.DataFrame, pred_cols: list[str]) -> float:
    """Fleiss' Kappa：衡量多标注者间一致性。

    Args:
        df: 数据框
        pred_cols: 预测列名列表

    Returns:
        Fleiss' Kappa 值
    """
    n = len(df)
    if n == 0:
        return np.nan

    all_labels = sorted(
        set().union(*(set(df[col].astype(str).unique()) for col in pred_cols))
    )
    label_to_idx = {l: i for i, l in enumerate(all_labels)}
    n_categories = len(all_labels)
    n_raters = len(pred_cols)

    counts = np.zeros((n, n_categories), dtype=int)
    for col in pred_cols:
        for i, val in enumerate(df[col].astype(str).values):
            counts[i, label_to_idx[val]] += 1

    p_e = np.sum(counts, axis=0) / (n * n_raters)
    p_e_bar = np.sum(p_e ** 2)

    p_i = (np.sum(counts ** 2, axis=1) - n_raters) / (n_raters * (n_raters - 1))
    p_bar = np.mean(p_i)

    if p_e_bar == 1.0:
        return 1.0

    return (p_bar - p_e_bar) / (1.0 - p_e_bar)


def main():
    import argparse

    parser = argparse.ArgumentParser(description="计算分类评估指标")
    parser.add_argument("input_file", help="输入 Excel 文件路径")
    parser.add_argument("--true_col", default="true_label", help="真实标签列名")
    parser.add_argument("--pred_cols", nargs="+", help="预测列名列表，默认 pred_label_1 ~ pred_label_10")
    parser.add_argument("--labels", nargs="+", help="类别标签列表，默认使用内置 LABELS")
    parser.add_argument("--output", help="输出文件路径，默认打印到终端")
    args = parser.parse_args()

    df = pd.read_excel(args.input_file)

    pred_cols = args.pred_cols or [f"pred_label_{i}" for i in range(1, 11)]
    labels = args.labels or LABELS

    # 评估众数预测
    mode_result = evaluate_mode_prediction(df, args.true_col, pred_cols, labels)

    print(f"众数预测结果 (n={mode_result['n_predictions']}):")
    print(f"  Accuracy: {mode_result['accuracy']:.6f}")
    print(f"  Macro F1:  {mode_result['macro_f1']:.6f}")

    # 计算 Fleiss' Kappa
    if len(pred_cols) >= 2:
        kappa = fleiss_kappa(df, pred_cols)
        print(f"\nFleiss' Kappa: {kappa:.6f}")
    else:
        print("\nFleiss' Kappa: 需要 >=2 个预测列")

    if args.output:
        result_df = pd.DataFrame([mode_result])
        if len(pred_cols) >= 2:
            result_df["fleiss_kappa"] = fleiss_kappa(df, pred_cols)
        result_df.to_excel(args.output, index=False)
        print(f"\n结果已保存到 {args.output}")


if __name__ == "__main__":
    main()