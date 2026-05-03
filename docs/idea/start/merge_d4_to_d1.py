import pandas as pd

D1_PATH = "D1数据集_矫正输血类.parquet"
D4_PATH = "D4_矫正输血类_错误样本.xlsx"
OUTPUT_PATH = D1_PATH

df1 = pd.read_parquet(D1_PATH)
df4 = pd.read_excel(D4_PATH)

print(f"D1: {len(df1)} 行, D4: {len(df4)} 行")

# 构建 D4 的申请号 -> last_label_1 映射
d4_map = df4.set_index("申请号")["last_label_1"].to_dict()

# 写入新列
df1["last_label_1"] = df1["申请号"].map(d4_map)

# 缺失的用 D1 的 标注结果 填充
filled = df1["last_label_1"].isna().sum()
df1["last_label_1"] = df1["last_label_1"].fillna(df1["标注结果"])

print(f"从D4回填: {len(df1) - filled} 条, 用标注结果填充: {filled} 条")
print(f"last_label_1 缺失: {df1['last_label_1'].isna().sum()} 条")

df1.to_parquet(OUTPUT_PATH, index=False)
print(f"已保存到: {OUTPUT_PATH}")
