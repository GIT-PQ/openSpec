import json
import os

# 输入文件路径
input_file = "../../step1/output/医疗器械术语_八维度.json"
# 输出目录
output_dir = "../output/jieba_dict"

# 创建输出目录
os.makedirs(output_dir, exist_ok=True)

# 读取JSON文件
with open(input_file, 'r', encoding='utf-8') as f:
    data = json.load(f)

categories = data['categories']

print(f"共处理 {len(categories)} 个类别\n")

# 维度字段列表
dimension_fields = [
    'category_indicators',
    'clinical_domain',
    'functional_level',
    'technical_principle',
    'target_object',
    'product_form',
    'product_examples',
    'category_terms'
]

# 为每个类别生成jieba词表
for category_name, category_data in categories.items():
    # 收集该类别下所有维度的词汇
    all_words = []

    for field in dimension_fields:
        if field in category_data and isinstance(category_data[field], list):
            all_words.extend(category_data[field])

    # 去重（保持顺序）
    seen = set()
    unique_words = []
    for word in all_words:
        if word not in seen:
            seen.add(word)
            unique_words.append(word)

    # 生成jieba词表格式（每行一个词，带词频和词性）
    # 格式：词语 词频 词性
    jieba_dict = []
    for word in unique_words:
        # 给词频设一个较高的值，确保分词时优先使用这些词
        # 词性可以设为'n'（名词）或其他，也可以留空
        jieba_dict.append(f"{word} 10000")

    # 生成类别文件名（将特殊字符替换为下划线）
    safe_category_name = category_name.replace('/', '_').replace(' ', '_')
    output_file = os.path.join(output_dir, f"{safe_category_name}.txt")

    # 写入文件
    with open(output_file, 'w', encoding='utf-8') as f:
        f.write('\n'.join(jieba_dict))

    print(f"类别: {category_name}")
    print(f"  - 原始词汇数: {len(all_words)}")
    print(f"  - 去重后词汇数: {len(unique_words)}")
    print(f"  - 输出文件: {output_file}\n")

# 生成合并词表（所有类别的词合并后去重）
print("=" * 50)
print("生成合并词表...")

all_category_words = []
for category_data in categories.values():
    for field in dimension_fields:
        if field in category_data and isinstance(category_data[field], list):
            all_category_words.extend(category_data[field])

# 全局去重
seen_global = set()
unique_global_words = []
for word in all_category_words:
    if word not in seen_global:
        seen_global.add(word)
        unique_global_words.append(word)

# 生成合并词表
merged_dict = [f"{word} 10000" for word in unique_global_words]
merged_output_file = os.path.join(output_dir, "医疗器械术语_合并.txt")

with open(merged_output_file, 'w', encoding='utf-8') as f:
    f.write('\n'.join(merged_dict))

print(f"合并词表:")
print(f"  - 原始词汇数: {len(all_category_words)}")
print(f"  - 去重后词汇数: {len(unique_global_words)}")
print(f"  - 输出文件: {merged_output_file}")
print(f"\n处理完成！词表已保存到 {output_dir} 目录")
