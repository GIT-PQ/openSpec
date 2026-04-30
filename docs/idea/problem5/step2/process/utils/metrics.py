"""分类评估指标：Accuracy、Macro F1、Fleiss' Kappa"""

import pandas as pd
import numpy as np
from sklearn.metrics import accuracy_score, f1_score


def evaluate_classification(
    df: pd.DataFrame,
    true_col: str,
    pred_cols: list[str],
    labels: list[str] | None = None,
    calc_kappa: bool = False,
) -> pd.DataFrame:
    """计算分类评估指标。

    对每个 pred_col 分别计算 Accuracy 和 Macro F1（以 true_col 为基准）。
    若 calc_kappa=True 且 pred_cols >= 2，额外计算 Fleiss' Kappa 衡量标注间一致性。

    Args:
        df: 含标签列的数据框
        true_col: 真实标签列名
        pred_cols: 预测/标注标签列名列表
        labels: 类别标签列表，用于保证 Macro F1 计算时类别一致；为 None 时自动推断
        calc_kappa: 是否计算 Fleiss' Kappa

    Returns:
        DataFrame，每行一个 pred_col，列为 metric 名称
    """
    y_true = df[true_col].astype(str)

    rows = []
    for col in pred_cols:
        y_pred = df[col].astype(str)
        acc = accuracy_score(y_true, y_pred)
        f1 = f1_score(y_true, y_pred, average="macro", labels=labels, zero_division=0)
        rows.append({"pred_col": col, "accuracy": acc, "macro_f1": f1})

    result = pd.DataFrame(rows)

    if calc_kappa and len(pred_cols) >= 2:
        kappa = _fleiss_kappa(df, pred_cols)
        result["fleiss_kappa"] = kappa

    return result


def _fleiss_kappa(df: pd.DataFrame, pred_cols: list[str]) -> float:
    """Fleiss' Kappa：衡量多标注者间一致性。

    将每行的多个预测视为多个标注者对同一样本的分类，计算一致性。
    """
    n = len(df)
    if n == 0:
        return np.nan

    # 所有出现过的类别
    all_labels = sorted(
        set().union(*(set(df[col].astype(str).unique()) for col in pred_cols))
    )
    label_to_idx = {l: i for i, l in enumerate(all_labels)}
    n_categories = len(all_labels)
    n_raters = len(pred_cols)

    # 构建计数矩阵: n x n_categories
    counts = np.zeros((n, n_categories), dtype=int)
    for col in pred_cols:
        for i, val in enumerate(df[col].astype(str).values):
            counts[i, label_to_idx[val]] += 1

    # Fleiss' Kappa 公式
    p_e = np.sum(counts, axis=0) / (n * n_raters)
    p_e_bar = np.sum(p_e ** 2)

    p_i = (np.sum(counts ** 2, axis=1) - n_raters) / (n_raters * (n_raters - 1))
    p_bar = np.mean(p_i)

    if p_e_bar == 1.0:
        return 1.0

    return (p_bar - p_e_bar) / (1.0 - p_e_bar)
