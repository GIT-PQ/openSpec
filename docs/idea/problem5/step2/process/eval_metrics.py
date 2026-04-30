"""调用 metrics.py 计算分类评估指标"""

import pandas as pd
from utils.metrics import evaluate_classification

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


def main():
    import argparse

    parser = argparse.ArgumentParser(description="计算分类评估指标")
    parser.add_argument("input_file", help="输入 Excel 文件路径")
    parser.add_argument("--true_col", default="true_label", help="真实标签列名")
    parser.add_argument("--pred_cols", nargs="+", help="预测列名列表，默认 pred_label_1 ~ pred_label_10")
    parser.add_argument("--labels", nargs="+", help="类别标签列表，默认使用内置 LABELS")
    parser.add_argument("--kappa", action="store_true", help="计算 Fleiss' Kappa")
    parser.add_argument("--output", help="输出文件路径，默认打印到终端")
    args = parser.parse_args()

    df = pd.read_excel(args.input_file)

    pred_cols = args.pred_cols or [f"pred_label_{i}" for i in range(1, 11)]
    labels = args.labels or LABELS

    result = evaluate_classification(
        df=df,
        true_col=args.true_col,
        pred_cols=pred_cols,
        labels=labels,
        calc_kappa=args.kappa,
    )

    if args.output:
        result.to_excel(args.output, index=False)
        print(f"结果已保存到 {args.output}")
    else:
        print(result.to_string(index=False))


if __name__ == "__main__":
    main()