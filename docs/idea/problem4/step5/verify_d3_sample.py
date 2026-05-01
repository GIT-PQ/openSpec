import sys
sys.stdout.reconfigure(encoding='utf-8')
import pandas as pd
import numpy as np
from scipy import stats

# d2已知错误率 (基准)
p_high_d2 = 0.0209
p_low_d2 = 0.1284
p_overall_d2 = 0.578 * p_high_d2 + 0.422 * p_low_d2

LABELS = ["有源手术器械","无源手术器械","神经和心血管手术器械","骨科手术器械",
"放射治疗器械","医用成像器械","医用诊察和监护器械","呼吸、麻醉和急救器械",
"物理治疗器械","输血、透析和体外循环器械","医疗器械消毒灭菌器械",
"有源植入器械","无源植入器械","注输、护理和防护器械",
"患者承载器械","眼科器械","口腔科器械","妇产科、辅助生殖和避孕器械",
"医用康复器械","中医器械","医用软件","临床检验器械"]

sample_path = r"D:\WorkSpace\JupyterWorkSpace\pq\app\openSpec\docs\idea\problem5\step2\input\d3_sample_all_rounds.xlsx"
df = pd.read_excel(sample_path)

# 检查校对完成情况
checked = df[df["校对标签"].notna() & (df["校对标签"] != "") & (df["校对标签"].isin(LABELS))]
unchecked = len(df) - len(checked)
if unchecked > 0:
    print("已校对: {} / {} (未校对: {})".format(len(checked), len(df), unchecked))
else:
    print("全部校对完成: {} 条".format(len(checked)))

if len(checked) == 0:
    print("请先在'校对标签'列填写校对结果")
    sys.exit(0)

# ============ 1. 各轮次错误率 ============
print("\n" + "="*60)
print("1. 各轮次错误率")
print("="*60)
for r in sorted(df["轮次"].unique()):
    sub = checked[checked["轮次"] == r]
    if len(sub) == 0:
        continue
    for conf in ["高置信", "低置信"]:
        c = sub[sub["置信度"] == conf]
        if len(c) == 0:
            continue
        errors = (c["工作流标签"] != c["校对标签"]).sum()
        print("  轮次{} {}:{}条, 错误{}, 错误率{:.2%}".format(r, conf, len(c), errors, errors/len(c)))

# ============ 2. 汇总错误率 vs d2 ============
print("\n" + "="*60)
print("2. 汇总错误率 vs d2基准")
print("="*60)
for conf, p_d2 in [("高置信", p_high_d2), ("低置信", p_low_d2)]:
    c = checked[checked["置信度"] == conf]
    if len(c) == 0:
        continue
    errors = (c["工作流标签"] != c["校对标签"]).sum()
    n = len(c)
    p_hat = errors / n
    # Wilson score interval (比正态近似更稳健, 尤其是p接近0时)
    z = 1.96
    denom = 2 * (n + z**2)
    center = (2*n*p_hat + z**2) / denom
    margin = z * np.sqrt((p_hat*(1-p_hat) + z**2/(4*n)) / n) / denom * 2  # 简化
    # 用标准Wald CI
    se = np.sqrt(p_hat * (1-p_hat) / n) if n > 0 else 0
    ci_low = max(0, p_hat - z * se)
    ci_high = min(1, p_hat + z * se)
    
    in_ci = "包含d2" if ci_low <= p_d2 <= ci_high else "不含d2"
    print("  {}{}条: 错误率={:.2%}, 95%CI=[{:.2%}, {:.2%}], d2={:.2%} -> {}".format(
        conf, n, p_hat, ci_low, ci_high, p_d2, in_ci))

# 整体
all_errors = (checked["工作流标签"] != checked["校对标签"]).sum()
p_overall = all_errors / len(checked)
se = np.sqrt(p_overall * (1-p_overall) / len(checked))
ci_low = max(0, p_overall - 1.96*se)
ci_high = min(1, p_overall + 1.96*se)
print("  整体{}条: 错误率={:.2%}, 95%CI=[{:.2%}, {:.2%}], d2={:.2%}".format(
    len(checked), p_overall, ci_low, ci_high, p_overall_d2))

# ============ 3. 比例检验 ============
print("\n" + "="*60)
print("3. 单样本比例检验 (H0: d3错误率 = d2错误率)")
print("="*60)
for conf, p_d2 in [("高置信", p_high_d2), ("低置信", p_low_d2)]:
    c = checked[checked["置信度"] == conf]
    if len(c) < 5:
        print("  {}样本不足, 跳过".format(conf))
        continue
    errors = (c["工作流标签"] != c["校对标签"]).sum()
    n = len(c)
    # z-test for single proportion
    p_hat = errors / n
    se0 = np.sqrt(p_d2 * (1-p_d2) / n)
    z_stat = (p_hat - p_d2) / se0 if se0 > 0 else 0
    p_value = 2 * (1 - stats.norm.cdf(abs(z_stat)))
    sig = "不拒绝H0" if p_value > 0.05 else "拒绝H0"
    print("  {}: p_hat={:.2%}, z={:.3f}, p-value={:.4f} -> {} (a=0.05)".format(
        conf, p_hat, z_stat, p_value, sig))

# ============ 4. 结论 ============
print("\n" + "="*60)
print("4. 结论")
print("="*60)
print("d2基准: 高置信错误率={:.2%}, 低置信错误率={:.2%}, 加权准确率={:.2%}".format(
    p_high_d2, p_low_d2, 1-p_overall_d2))
print("d3抽样: 整体错误率={:.2%}, 推断d3准确率≈{:.1%}".format(p_overall, 1-p_overall))
