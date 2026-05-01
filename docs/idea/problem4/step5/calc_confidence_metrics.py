import sys
sys.stdout.reconfigure(encoding='utf-8')
import pandas as pd

orig_col = '一级产品类别（原始）'
wf_col = '一级产品类别（last模型众数）'
true_col = '一级产品类别（校对）'

# ============ D2: 从D2.xlsx计算高/低置信比例和正确率/错误率 ============
d2 = pd.read_excel(r'D:\WorkSpace\JupyterWorkSpace\pq\app\openSpec\docs\idea\problem5\step2\input\D2.xlsx')
d2['is_high'] = d2[orig_col] == d2[wf_col]
d2['is_correct'] = d2[wf_col] == d2[true_col]

high = d2['is_high'].sum()
low = len(d2) - high
print("D2. 高置信比例: {:.4f} ({}/{}), 低置信比例: {:.4f} ({}/{})".format(
    high/len(d2), high, len(d2), low/len(d2), low, len(d2)))

for conf_name, conf_mask in [('高置信', d2['is_high'] == True), ('低置信', d2['is_high'] == False)]:
    sub = d2[conf_mask]
    correct = sub['is_correct'].sum()
    wrong = len(sub) - correct
    print("D2 {}. 正确率: {:.4f} ({}/{}), 错误率: {:.4f} ({}/{})".format(
        conf_name, correct/len(sub), correct, len(sub), wrong/len(sub), wrong, len(sub)))

# ============ D3: 从D1计算高/低置信比例 ============
d1 = pd.read_parquet(r'D:\WorkSpace\JupyterWorkSpace\pq\模型\数据集\D1数据集.parquet')
d3 = d1[d1['isD2'] == False]
d3_high = (d3['class_name'] == d3['标注结果']).sum()
d3_low = len(d3) - d3_high
print("D3. 高置信比例: {:.4f} ({}/{}), 低置信比例: {:.4f} ({}/{})".format(
    d3_high/len(d3), d3_high, len(d3), d3_low/len(d3), d3_low, len(d3)))
