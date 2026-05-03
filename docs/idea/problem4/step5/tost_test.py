import pandas as pd
import numpy as np
from scipy import stats

# ==================== 配置 ====================
D3_SAMPLE_PATH = "D:/WorkSpace/JupyterWorkSpace/pq/app/openSpec/docs/idea/problem4/step5/output/D3_sample_校对.xlsx"
D2_PATH = "D:/WorkSpace/JupyterWorkSpace/pq/app/openSpec/docs/idea/problem5/step2/input/D2.xlsx"

DELTA = 0.03   # 等价边界
ALPHA = 0.05   # 显著性水平

# ==================== D2高置信基准（全量，非抽样估计） ====================
d2 = pd.read_excel(D2_PATH)
real_col = "一级产品类别（校对）"
d2_valid = d2[d2[real_col].notna()].copy()
d2_orig = "一级产品类别（原始）"
d2_real = "一级产品类别（校对）"
d2_pred = "一级产品类别（last模型众数）"

d2_high = d2_valid[d2_valid[d2_orig] == d2_valid[d2_pred]]
d2_low = d2_valid[d2_valid[d2_orig] != d2_valid[d2_pred]]

d2_high_correct = (d2_high[d2_real] == d2_high[d2_pred]).sum()
d2_high_n = len(d2_high)
d2_high_acc = d2_high_correct / d2_high_n

d2_low_correct = (d2_low[d2_real] == d2_low[d2_pred]).sum()
d2_low_n = len(d2_low)
d2_low_acc = d2_low_correct / d2_low_n

print("=" * 60)
print("D2基准（全量专家标注，非抽样估计）")
print(f"  高置信: acc={d2_high_acc:.4f} ({d2_high_correct}/{d2_high_n})")
print(f"  低置信: acc={d2_low_acc:.4f} ({d2_low_correct}/{d2_low_n})")

# ==================== D3高置信抽样结果 ====================
d3s = pd.read_excel(D3_SAMPLE_PATH)
cols = d3s.columns.tolist()
conf_col = cols[5]    # 置信度
wf_col = cols[4]      # 工作流标签
proof_col = cols[6]   # 校对标签

d3s_high = d3s[(d3s[conf_col] == "高置信") & (d3s[proof_col].notna())]
d3_high_correct = (d3s_high[proof_col] == d3s_high[wf_col]).sum()
d3_high_n = len(d3s_high)
d3_high_acc = d3_high_correct / d3_high_n

print(f"\nD3高置信抽样: acc={d3_high_acc:.4f} ({d3_high_correct}/{d3_high_n})")

# ==================== TOST等价性检验 ====================
def tost_one_sample(observed_acc, n, reference_acc, delta, alpha):
    """单样本TOST等价性检验（参考值为已知总体值）"""
    p_hat = observed_acc
    se = np.sqrt(p_hat * (1 - p_hat) / n)

    # 两个单侧检验
    # T1: H0: p <= reference - delta  vs  H1: p > reference - delta
    z1 = (p_hat - (reference_acc - delta)) / se
    p1 = 1 - stats.norm.cdf(z1)

    # T2: H0: p >= reference + delta  vs  H1: p < reference + delta
    z2 = (p_hat - (reference_acc + delta)) / se
    p2 = stats.norm.cdf(z2)

    # TOST通过：两个单侧检验均拒绝H0
    p_max = max(p1, p2)
    passed = p_max < alpha

    # 90% CI (TOST对应90% CI)
    z_alpha = stats.norm.ppf(1 - alpha)
    ci_lower = p_hat - z_alpha * se
    ci_upper = p_hat + z_alpha * se

    eq_lower = reference_acc - delta
    eq_upper = reference_acc + delta

    return {
        "p_hat": p_hat, "se": se,
        "z1": z1, "p1": p1,
        "z2": z2, "p2": p2,
        "p_max": p_max,
        "ci_lower": ci_lower, "ci_upper": ci_upper,
        "eq_lower": eq_lower, "eq_upper": eq_upper,
        "passed": passed
    }

print("\n" + "=" * 60)
print("TOST等价性检验: D3高置信 acc vs D2高置信 acc")
print(f"  等价边界 delta={DELTA}, alpha={ALPHA}")
print(f"  H0: |p_D3 - {d2_high_acc:.4f}| >= {DELTA}")
print(f"  H1: |p_D3 - {d2_high_acc:.4f}| < {DELTA}")
print(f"  等价区间: ({d2_high_acc - DELTA:.4f}, {d2_high_acc + DELTA:.4f})")

r = tost_one_sample(d3_high_acc, d3_high_n, d2_high_acc, DELTA, ALPHA)

print(f"\n  观测acc: {r['p_hat']:.4f}")
print(f"  SE: {r['se']:.4f}")
print(f"  90% CI: ({r['ci_lower']:.4f}, {r['ci_upper']:.4f})")
print(f"  等价区间: ({r['eq_lower']:.4f}, {r['eq_upper']:.4f})")
print(f"\n  T1 (左边界): z={r['z1']:.4f}, p={r['p1']:.6f}")
print(f"  T2 (右边界): z={r['z2']:.4f}, p={r['p2']:.6f}")
print(f"  max(p1, p2) = {r['p_max']:.6f}")

if r["passed"]:
    print(f"\n  >>> TOST通过: 90% CI ({r['ci_lower']:.4f}, {r['ci_upper']:.4f}) 完全落在等价区间内")
    print(f"  >>> D3高置信acc与D2统计等价 (差异 < {DELTA})")
else:
    print(f"\n  >>> TOST未通过")
    if r["ci_lower"] < r["eq_lower"]:
        print(f"  >>> CI下界 {r['ci_lower']:.4f} < 等价下界 {r['eq_lower']:.4f}")
    if r["ci_upper"] > r["eq_upper"]:
        print(f"  >>> CI上界 {r['ci_upper']:.4f} > 等价上界 {r['eq_upper']:.4f}")
