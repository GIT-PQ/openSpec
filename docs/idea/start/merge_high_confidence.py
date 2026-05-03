import pandas as pd

INPUT_PATH = "D:/WorkSpace/JupyterWorkSpace/pq/app/openSpec/docs/idea/start/D1数据集_矫正输血类.parquet"
OUTPUT_PATH = "D:/WorkSpace/JupyterWorkSpace/pq/app/openSpec/docs/idea/start/数据集_D2_D3高置信.parquet"

df = pd.read_parquet(INPUT_PATH)

# 筛选条件：D2全保留，D3仅保留高置信（class_name == last_label_1）
d2 = df[df["isD2"] == True].copy()
d3_high = df[(df["isD2"] == False) & (df["class_name"] == df["last_label_1"])].copy()

# 构造last_label列
d2["last_label"] = d2["标注结果"]
d3_high["last_label"] = d3_high["last_label_1"]

# 合并
result = pd.concat([d2, d3_high], ignore_index=True)
print(f"D2: {len(d2)}条, D3高置信: {len(d3_high)}条, 合计: {len(result)}条")
print(f"last_label分布:")
print(result["last_label"].value_counts().to_string())

result.to_parquet(OUTPUT_PATH, index=False)
print(f"\n已保存到: {OUTPUT_PATH}")
