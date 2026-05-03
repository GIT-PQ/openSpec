import pandas as pd
import numpy as np

# ==================== 配置 ====================
INPUT_PATH = "D:/WorkSpace/JupyterWorkSpace/pq/app/openSpec/docs/idea/start/D1数据集_矫正输血类.parquet"
OUTPUT_PATH = "./output/D3_sample_校对.xlsx"
RANDOM_SEED = 42

HIGH_N = 440   # 高置信抽样总量
LOW_N = 330    # 低置信抽样总量

# ==================== 读取数据 ====================
df = pd.read_parquet(INPUT_PATH)
d3 = df[df["isD2"] == False].copy()
print(f"D3总量: {len(d3)}")

# 置信度标记
d3["置信度"] = (d3["class_name"] == d3["last_label_1"]).map({True: "高置信", False: "低置信"})
print(f"高置信: {(d3['置信度'] == '高置信').sum()}, 低置信: {(d3['置信度'] == '低置信').sum()}")

# ==================== 分层抽样 ====================
LABELS = [
    "有源手术器械", "无源手术器械", "神经和心血管手术器械", "骨科手术器械",
    "放射治疗器械", "医用成像器械", "医用诊察和监护器械", "呼吸、麻醉和急救器械",
    "物理治疗器械", "输血、透析和体外循环器械", "医疗器械消毒灭菌器械",
    "有源植入器械", "无源植入器械", "注输、护理和防护器械",
    "患者承载器械", "眼科器械", "口腔科器械", "妇产科、辅助生殖和避孕器械",
    "医用康复器械", "中医器械", "医用软件", "临床检验器械"
]

sampled_frames = []
warnings = []

for conf, total_n in [("高置信", HIGH_N), ("低置信", LOW_N)]:
    per_class_n = total_n // len(LABELS)
    remainder = total_n - per_class_n * len(LABELS)
    print(f"\n{conf}: 每类{per_class_n}条, 余{remainder}条分配给前{remainder}类")

    conf_df = d3[d3["置信度"] == conf]
    sampled_list = []

    for i, label in enumerate(LABELS):
        cell = conf_df[conf_df["last_label_1"] == label]
        n = per_class_n + (1 if i < remainder else 0)

        if len(cell) < n:
            warnings.append(f"  {conf}/{label}: 需抽{n}条, 仅{len(cell)}条可用, 全量抽取")
            n = len(cell)

        sampled = cell.sample(n=n, random_state=RANDOM_SEED)
        sampled_list.append(sampled)

    layer_sampled = pd.concat(sampled_list)
    sampled_frames.append(layer_sampled)
    print(f"  {conf}实际抽取: {len(layer_sampled)}条")

if warnings:
    print("\n警告:")
    for w in warnings:
        print(w)

result = pd.concat(sampled_frames)
print(f"\n总计抽取: {len(result)}条")

# ==================== 输出 ====================
output_cols = ["申请号", "标题", "摘要", "class_name", "last_label_1", "置信度"]
result = result[output_cols].copy()
result.rename(columns={
    "class_name": "原始标签",
    "last_label_1": "工作流标签",
}, inplace=True)
result["校对标签"] = ""
result = result.sort_values(["置信度", "工作流标签"]).reset_index(drop=True)

result.to_excel(OUTPUT_PATH, index=False)
print(f"已保存到: {OUTPUT_PATH}")

# 打印分布
print("\n抽样分布:")
ct = pd.crosstab(result["工作流标签"], result["置信度"], margins=True)
print(ct.to_string())
