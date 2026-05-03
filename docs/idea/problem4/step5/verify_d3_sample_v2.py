import sys
import random
import numpy as np
from scipy import stats

sys.stdout.reconfigure(encoding='utf-8')

# ============================================================
# 配置
# ============================================================
LABELS = [
    "有源手术器械", "无源手术器械", "神经和心血管手术器械", "骨科手术器械",
    "放射治疗器械", "医用成像器械", "医用诊察和监护器械", "呼吸、麻醉和急救器械",
    "物理治疗器械", "输血、透析和体外循环器械", "医疗器械消毒灭菌器械",
    "有源植入器械", "无源植入器械", "注输、护理和防护器械",
    "患者承载器械", "眼科器械", "口腔科器械", "妇产科、辅助生殖和避孕器械",
    "医用康复器械", "中医器械", "医用软件", "临床检验器械",
]

P_D2 = 0.932          # D2基准准确率
DELTA = 0.03           # 等价边界
ALPHA = 0.05           # 显著性水平
N_PER_CLASS = 30       # 每类抽样数
LABEL_COL = "原始标签"  # D3中22类标签的列名
SEED = 42


# ============================================================
# 阶段1：生成分层抽样清单
# ============================================================
def generate_sampling(input_path, output_path):
    """从D3中按22类分层随机抽样，输出待标注清单"""
    import pandas as pd

    df = pd.read_excel(input_path)
    samples = []

    for label in LABELS:
        subset = df[df[LABEL_COL] == label]
        n_available = len(subset)
        n_draw = min(N_PER_CLASS, n_available)

        if n_draw < N_PER_CLASS:
            print(f"  ⚠ {label}: 仅{n_available}条, 不足{N_PER_CLASS}条, 全部抽取")

        sampled = subset.sample(n=n_draw, random_state=SEED)
        samples.append(sampled)

    result = pd.concat(samples)
    result = result.reset_index(drop=True)
    result["校对标签"] = ""  # 人工标注列

    result.to_excel(output_path, index=False)
    print(f"\n抽样完成: {len(result)}条 -> {output_path}")
    print(f"  每类: {N_PER_CLASS}条 x {len(LABELS)}类 = {N_PER_CLASS * len(LABELS)}条")


# ============================================================
# 阶段2：TOST等价性检验
# ============================================================
def wilson_ci(p_hat, n, z=1.645):
    """Wilson score置信区间，比Wald更稳健（p接近0或1时）"""
    denom = 2 * (n + z**2)
    center = (2 * n * p_hat + z**2) / denom
    margin = z * np.sqrt(n * p_hat * (1 - p_hat) + z**2 / 4) / denom
    return center - margin, center + margin


def tost_proportion(n_correct, n_total, p0, delta, alpha=0.05):
    """
    单样本比例TOST等价性检验

    H0: |p - p0| >= delta  (不等价)
    H1: |p - p0| < delta   (等价)

    参数:
        n_correct: 正确数
        n_total:   总数
        p0:        基准比例
        delta:     等价边界
        alpha:     显著性水平
    """
    p_hat = n_correct / n_total
    se = np.sqrt(p_hat * (1 - p_hat) / n_total)
    z = stats.norm.ppf(1 - alpha)  # 单侧检验，z=1.645

    # 两个单侧检验
    # 检验1: H0: p <= p0 - delta  vs  H1: p > p0 - delta
    z1 = (p_hat - (p0 - delta)) / se
    p1 = stats.norm.cdf(-z1)  # P(Z < z1) 的左尾 = 1 - Phi(z1) 的等价写法
    p1 = 1 - stats.norm.cdf(z1)

    # 检验2: H0: p >= p0 + delta  vs  H1: p < p0 + delta
    z2 = ((p0 + delta) - p_hat) / se
    p2 = 1 - stats.norm.cdf(z2)

    # TOST的p值 = max(p1, p2)
    p_value = max(p1, p2)

    # 90% CI (TOST标准)
    ci_low, ci_high = wilson_ci(p_hat, n_total, z)

    # 等价边界
    eq_low = p0 - delta
    eq_high = p0 + delta

    # 判断: CI完全落在等价边界内
    passed = ci_low >= eq_low and ci_high <= eq_high

    return {
        "p_hat": p_hat,
        "se": se,
        "ci_low": ci_low,
        "ci_high": ci_high,
        "eq_low": eq_low,
        "eq_high": eq_high,
        "z1": z1,
        "p1": p1,
        "z2": z2,
        "p2": p2,
        "p_value": p_value,
        "passed": passed,
    }
def run_tost(annotation_path, label_col=LABEL_COL, correct_col="校对标签",
             workflow_col="工作流标签"):
    """读取标注结果，执行TOST检验"""
    import pandas as pd

    df = pd.read_excel(annotation_path)

    # 过滤已标注
    checked = df[df[correct_col].notna() & (df[correct_col] != "") & (df[correct_col].isin(LABELS))]
    if len(checked) == 0:
        print("请先在'校对标签'列填写标注结果")
        sys.exit(0)

    print(f"已标注: {len(checked)}条\n")

    # ---- 各类别准确率 ----
    print("=" * 60)
    print("1. 各类别准确率")
    print("=" * 60)
    class_stats = []
    for label in LABELS:
        c = checked[checked[label_col] == label]
        if len(c) == 0:
            continue
        correct = (c[workflow_col] == c[correct_col]).sum()
        total = len(c)
        acc = correct / total
        class_stats.append({"类别": label, "正确": correct, "总数": total, "准确率": acc})
        print(f"  {label}: {correct}/{total} = {acc:.2%}")

    # ---- 整体准确率 + TOST ----
    n_correct = (checked[workflow_col] == checked[correct_col]).sum()
    n_total = len(checked)
    p_hat = n_correct / n_total

    print("\n" + "=" * 60)
    print("2. 整体TOST等价性检验")
    print("=" * 60)
    print(f"  D3抽样: {n_correct}/{n_total}, acc = {p_hat:.4f} ({p_hat:.2%})")
    print(f"  D2基准: acc = {P_D2:.4f} ({P_D2:.2%})")
    print(f"  等价边界 Δ = {DELTA:.1%}")
    print(f"  显著性水平 α = {ALPHA}")

    result = tost_proportion(n_correct, n_total, P_D2, DELTA, ALPHA)

    print(f"\n  D3 90% CI: [{result['ci_low']:.4f}, {result['ci_high']:.4f}]"
          f" = [{result['ci_low']:.2%}, {result['ci_high']:.2%}]")
    print(f"  等价边界:  [{result['eq_low']:.4f}, {result['eq_high']:.4f}]"
          f" = [{result['eq_low']:.2%}, {result['eq_high']:.2%}]")
    print(f"\n  检验1 (p > {result['eq_low']:.2%}): z = {result['z1']:.3f}, p = {result['p1']:.4f}")
    print(f"  检验2 (p < {result['eq_high']:.2%}): z = {result['z2']:.3f}, p = {result['p2']:.4f}")
    print(f"  TOST p值 = {result['p_value']:.4f}")

    # ---- 结论 ----
    print("\n" + "=" * 60)
    print("3. 结论")
    print("=" * 60)
    if result["passed"]:
        print(f"  ✓ TOST通过 (p={result['p_value']:.4f} < {ALPHA})")
        print(f"  D3与D2的整体准确率差异不超过{DELTA:.0%}，统计等价成立。")
        print(f"  D3准确率的90%置信区间为[{result['ci_low']:.2%}, {result['ci_high']:.2%}]，"
              f"完全落在等价边界({result['eq_low']:.2%}, {result['eq_high']:.2%})内。")
    else:
        print(f"  ✗ TOST未通过 (p={result['p_value']:.4f})")
        if result["ci_low"] < result["eq_low"]:
            print(f"  CI下界{result['ci_low']:.2%} < 等价边界下界{result['eq_low']:.2%}，"
                  f"无法证明D3准确率显著高于{result['eq_low']:.2%}。")
        if result["ci_high"] > result["eq_high"]:
            print(f"  CI上界{result['ci_high']:.2%} > 等价边界上界{result['eq_high']:.2%}，"
                  f"无法证明D3准确率显著低于{result['eq_high']:.2%}。")

    # ---- 最小可证明的Δ ----
    ci_half_width = (result["ci_high"] - result["ci_low"]) / 2
    print(f"\n  [参考] 当前样本量下CI半宽={ci_half_width:.2%}，"
          f"最小可证明的Δ ≈ {ci_half_width:.2%}")


# ============================================================
# 主入口
# ============================================================
if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description="D3数据集TOST等价性检验")
    sub = parser.add_subparsers(dest="action")

    # 阶段1：抽样
    p_sample = sub.add_parser("sample", help="生成分层抽样清单")
    p_sample.add_argument("--input", required=True, help="D3数据集路径(.xlsx)")
    p_sample.add_argument("--output", default="d3_sample.xlsx", help="抽样输出路径")

    # 阶段2：TOST
    p_tost = sub.add_parser("tost", help="执行TOST等价性检验")
    p_tost.add_argument("--input", required=True, help="标注完成后的抽样文件路径(.xlsx)")

    args = parser.parse_args()

    if args.action == "sample":
        generate_sampling(args.input, args.output)
    elif args.action == "tost":
        run_tost(args.input)
    else:
        parser.print_help()
