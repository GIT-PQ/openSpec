import pandas as pd

# 读取Excel文件
input_path = '../input/D2.xlsx'
df = pd.read_excel(input_path)

# 添加新列：预测结果不等于真实标签则为True，否则为False
df['v12预测错误'] = df['一级产品类别（v12模型众数）'] != df['一级产品类别（校对）']
df['v16预测错误'] = df['一级产品类别（v16模型众数）'] != df['一级产品类别（校对）']

# 统计错误数量
error_count_v12 = df['v12预测错误'].sum()
error_count_v16 = df['v16预测错误'].sum()
total_count = len(df)
accuracy_v12 = (total_count - error_count_v12) / total_count * 100
accuracy_v16 = (total_count - error_count_v16) / total_count * 100

print(f"总样本数: {total_count}")
print(f"\nv12模型:")
print(f"  预测错误数: {error_count_v12}")
print(f"  准确率: {accuracy_v12:.2f}%")
print(f"\nv16模型:")
print(f"  预测错误数: {error_count_v16}")
print(f"  准确率: {accuracy_v16:.2f}%")

# 保存结果
output_path = '../input/D2.xlsx'
df.to_excel(output_path, index=False)
print(f"\n已保存到: {output_path}")
