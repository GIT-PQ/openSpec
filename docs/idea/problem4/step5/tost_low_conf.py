import numpy as np
from scipy import stats
import sys

sys.stdout.reconfigure(encoding="utf-8")

# ============================================================
# 配置
# ============================================================
D2_LOW_ACC = 0.8716       # D2低置信基准准确率
D3_LOW_ACC = 0.8212       # D3低置信观测准确率
D3_LOW_N = 330            # D3低置信抽样数
DELTA = 0.09              # 等价边界
ALPHA = 0.05              # 显著性水平

# ============================================================
# TOST等价性检验
# ============================================================
p_hat = D3_LOW_ACC
n = D3_LOW_N
p0 = D2_LOW_ACC
se = np.sqrt(p_hat * (1 - p_hat) / n)
z_alpha = stats.norm.ppf(1 - ALPHA)  # 1.645

# 两个单侧检验
z1 = (p_hat - (p0 - DELTA)) / se
p1 = 1 - stats.norm.cdf(z1)

z2 = (p_hat - (p0 + DELTA)) / se
p2 = stats.norm.cdf(z2)

p_value = max(p1, p2)

# 90% CI
ci_low = p_hat - z_alpha * se
ci_high = p_hat + z_alpha * se

# 等价边界
eq_low = p0 - DELTA
eq_high = p0 + DELTA

passed = ci_low >= eq_low and ci_high <= eq_high

print("=" * 60)
print("TOST等价性检验: D3低置信 acc vs D2低置信 acc")
print("=" * 60)
print(f"  D2低置信acc: {p0:.4f} (全量专家标注)")
print(f"  D3低置信acc: {p_hat:.4f} (330/330抽样校对)")
print(f"  等价边界 delta={DELTA}, alpha={ALPHA}")
print(f"  H0: |p_D3 - {p0:.4f}| >= {DELTA}")
print(f"  H1: |p_D3 - {p0:.4f}| < {DELTA}")
print(f"  等价区间: ({eq_low:.4f}, {eq_high:.4f})")
print()
print(f"  观测acc: {p_hat:.4f}")
print(f"  SE: {se:.4f}")
print(f"  90% CI: ({ci_low:.4f}, {ci_high:.4f})")
print(f"  等价区间: ({eq_low:.4f}, {eq_high:.4f})")
print()
print(f"  T1 (左边界): z={z1:.4f}, p={p1:.6f}")
print(f"  T2 (右边界): z={z2:.4f}, p={p2:.6f}")
print(f"  max(p1, p2) = {p_value:.6f}")
print()

if passed:
    print(f">>> TOST通过: 90% CI ({ci_low:.4f}, {ci_high:.4f}) 完全落在等价区间内")
    print(f">>> D3低置信acc与D2统计等价 (差异 < {DELTA})")
else:
    print(f">>> TOST未通过")
    if ci_low < eq_low:
        print(f">>> CI下界 {ci_low:.4f} < 等价下界 {eq_low:.4f}")
    if ci_high > eq_high:
        print(f">>> CI上界 {ci_high:.4f} > 等价上界 {eq_high:.4f}")
