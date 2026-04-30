"""
合并医疗器械术语：将六维度提取结果与lite版（product_names + category_terms）合并为八维度JSON。
八维度 = 原六维度 + product_examples + category_terms
"""
import json
import re

def normalize_key(k):
    """去除key中的不可见字符"""
    return re.sub(r'[\xa0\u3000]', ' ', k).strip()

def load_json(path):
    with open(path, 'r', encoding='utf-8') as f:
        return json.load(f)

# 加载两个文件
lite = load_json('/tmp/data/医疗器械关键字_lite.json')
six_dim = load_json('/tmp/data/医疗器械术语_六维度提取.json')

# 建立lite的key映射（normalized -> original）
lite_keys = {}
for k in lite['categories']:
    lite_keys[normalize_key(k)] = k

# 建立六维度的key映射
six_keys = {}
for k in six_dim['categories']:
    six_keys[normalize_key(k)] = k

# 合并
merged = {"categories": {}}

for norm_key in six_keys:
    six_k = six_keys[norm_key]
    six_data = six_dim['categories'][six_k]

    # 查找lite中对应的类别
    lite_k = lite_keys.get(norm_key)
    if lite_k:
        lite_data = lite['categories'][lite_k]
        product_names = lite_data.get('product_names', [])
        category_terms = lite_data.get('category_terms', [])
    else:
        print(f"WARNING: lite中未找到类别: {norm_key}")
        product_names = []
        category_terms = []

    merged['categories'][norm_key] = {
        "category_indicators": six_data.get("category_indicators", []),
        "clinical_domain": six_data.get("clinical_domain", []),
        "functional_level": six_data.get("functional_level", []),
        "technical_principle": six_data.get("technical_principle", []),
        "target_object": six_data.get("target_object", []),
        "product_form": six_data.get("product_form", []),
        "product_examples": product_names,
        "category_terms": category_terms
    }

# 输出
out_path = '/tmp/data/医疗器械术语_八维度.json'
with open(out_path, 'w', encoding='utf-8') as f:
    json.dump(merged, f, ensure_ascii=False, indent=2)

# 统计
print(f"合并完成！输出文件: {out_path}")
print(f"类别数: {len(merged['categories'])}")
total = 0
for k, v in merged['categories'].items():
    dims = {dim: len(vals) for dim, vals in v.items()}
    row_total = sum(dims.values())
    total += row_total
    print(f"  {k}: {dims} = {row_total}")
print(f"\n总术语数: {total}")