"""
BM25 评估：调用 utils/metrics.py 计算 Accuracy 和 Macro F1
"""
import pandas as pd
from pathlib import Path
from utils.metrics import evaluate_classification

# ── 22 类标签 ─────────────────────────────────────────
LABELS = [
    "有源手术器械", "无源手术器械", "神经和心血管手术器械", "骨科手术器械",
    "放射治疗器械", "医用成像器械", "医用诊察和监护器械", "呼吸、麻醉和急救器械",
    "物理治疗器械", "输血、透析和体外循环器械", "医疗器械消毒灭菌器械",
    "有源植入器械", "无源植入器械", "注输、护理和防护器械",
    "患者承载器械", "眼科器械", "口腔科器械", "妇产科、辅助生殖和避孕器械",
    "医用康复器械", "中医器械", "医用软件", "临床检验器械"
]

base = Path(__file__).resolve().parent.parent
INPUT_XLSX = base / "output" / "bm25_results.xlsx"
OUTPUT_XLSX = base / "output" / "bm25_eval.xlsx"


def main():
    df = pd.read_excel(INPUT_XLSX)
    pred_cols = [c for c in df.columns if c.startswith("pred_")]
    print(f"预测列数: {len(pred_cols)}")

    result = evaluate_classification(df, true_col="true_label", pred_cols=pred_cols,
                                    labels=LABELS, calc_kappa=False)
    # 按 accuracy 降序排列
    result = result.sort_values("accuracy", ascending=False).reset_index(drop=True)
    print(result.to_string(index=False))

    result.to_excel(OUTPUT_XLSX, index=False)
    print(f"\n[输出] {OUTPUT_XLSX}")


if __name__ == "__main__":
    main()
