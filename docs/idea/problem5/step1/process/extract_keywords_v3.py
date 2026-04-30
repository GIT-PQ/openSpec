#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
医疗器械分类目录关键字提取脚本 v3
优化版：从多个字段提取关键词，改进预期用途提取策略
"""

import pandas as pd
import json
import re
from datetime import datetime
from pathlib import Path
from collections import defaultdict

# 文件路径
INPUT_FILE = Path(__file__).parent.parent / "data" / "医疗器械分类目录.xlsx"
OUTPUT_FILE = Path(__file__).parent.parent / "data" / "医疗器械关键字_full.json"


def extract_keywords_from_cell(cell_value):
    """从单元格提取关键词列表"""
    if pd.isna(cell_value) or not str(cell_value).strip():
        return []
    text = str(cell_value).strip()
    keywords = re.split(r'[、,，;；\s]+', text)
    return [kw.strip() for kw in keywords if kw.strip()]


def extract_terms_from_description(text):
    """
    从产品描述中提取组件/部件术语
    策略：提取"XX 器"、"XX 仪"、"XX 装置"等名词，以及"由...组成"结构中的组件
    """
    if pd.isna(text) or not str(text).strip():
        return []

    terms = set()
    text = str(text)

    # 提取 "XX 器"、"XX 仪"、"XX 机"、"XX 系统"、"XX 装置" 等
    patterns = [
        r'(\w+?器)',
        r'(\w+?仪)',
        r'(\w+?机)',
        r'(\w+?系统)',
        r'(\w+?装置)',
        r'(\w+?设备)',
        r'(\w+?组件)',
        r'(\w+?部件)',
        r'(\w+?单元)',
        r'(\w+?模块)',
        r'(\w+?头)',  # 治疗头、刀头等
        r'(\w+?尖端)',
        r'(\w+?构件)',
        r'(\w+?发生器)',
    ]

    for pattern in patterns:
        matches = re.findall(pattern, text)
        terms.update(matches)

    return sorted(list(terms))


def extract_terms_from_usage(text):
    """
    从预期用途中提取关键词
    策略：直接按分隔符拆分，提取治疗/检查/诊断等动作对象
    """
    if pd.isna(text) or not str(text).strip():
        return []

    text = str(text)
    terms = set()

    # 去掉"用于"、"适用于"等前缀
    text = re.sub(r'^(?:用于|适用于|主要用于|适用于)', '', text)

    # 按顿号、逗号分隔
    raw_terms = re.split(r'[、,，;；]+', text)

    for term in raw_terms:
        term = term.strip()
        if len(term) >= 2:
            # 去掉句末的句号
            term = re.sub(r'[。\.]+$', '', term)
            if term:
                terms.add(term)

    return sorted(list(terms))


def main():
    print(f"读取文件：{INPUT_FILE}\n")

    xls = pd.ExcelFile(INPUT_FILE)
    sheet_names = xls.sheet_names

    print(f"发现 {len(sheet_names)} 个 sheet\n")

    # 存储结果
    category_keywords = {}
    all_product_names = set()
    all_category_terms = set()
    all_description_terms = set()
    all_usage_terms = set()

    for i, sheet_name in enumerate(sheet_names, 1):
        print(f"[{i:2d}/22] {sheet_name}")

        df = pd.read_excel(xls, sheet_name=sheet_name, header=0)

        product_name_set = set()
        category_term_set = set()
        description_term_set = set()
        usage_term_set = set()

        for _, row in df.iterrows():
            # 1. 品名举例
            names = extract_keywords_from_cell(row.get('品名举例'))
            product_name_set.update(names)

            # 2. 三级分类名称（去掉序号）
            level3 = row.get('三级序号/产品类别', '')
            if pd.notna(level3):
                match = re.search(r'[\d.]+\s*(.+)', str(level3))
                if match:
                    category_term_set.add(match.group(1).strip())

            # 3. 产品描述术语
            desc = row.get('产品描述', '')
            if pd.notna(desc):
                desc_terms = extract_terms_from_description(desc)
                description_term_set.update(desc_terms)

            # 4. 预期用途术语
            usage = row.get('预期用途', '')
            if pd.notna(usage):
                usage_terms = extract_terms_from_usage(usage)
                usage_term_set.update(usage_terms)

        # 合并到全局集合
        all_product_names.update(product_name_set)
        all_category_terms.update(category_term_set)
        all_description_terms.update(description_term_set)
        all_usage_terms.update(usage_term_set)

        # 保存该类别的结果
        category_keywords[sheet_name] = {
            "product_names": sorted(list(product_name_set)),
            "category_terms": sorted(list(category_term_set)),
            "description_terms": sorted(list(description_term_set)),
            "usage_terms": sorted(list(usage_term_set)),
            "counts": {
                "product_names": len(product_name_set),
                "category_terms": len(category_term_set),
                "description_terms": len(description_term_set),
                "usage_terms": len(usage_term_set),
                "total_unique": len(product_name_set | category_term_set | description_term_set | usage_term_set)
            }
        }

        print(f"       品名:{len(product_name_set):4d} | 分类:{len(category_term_set):3d} | "
              f"描述:{len(description_term_set):3d} | 用途:{len(usage_term_set):3d} | "
              f"合计:{len(product_name_set | category_term_set | description_term_set | usage_term_set):4d}")

    xls.close()

    # 扁平化合并版本
    flat_keywords = {}
    for cat_name, cat_data in category_keywords.items():
        if cat_name != '_metadata':
            all_terms = set()
            all_terms.update(cat_data['product_names'])
            all_terms.update(cat_data['category_terms'])
            all_terms.update(cat_data['description_terms'])
            all_terms.update(cat_data['usage_terms'])
            flat_keywords[cat_name] = sorted(list(all_terms))

    # 元数据
    result = {
        "categories": category_keywords,
        "flat_keywords": flat_keywords,
        "global_sets": {
            "all_product_names": sorted(list(all_product_names)),
            "all_category_terms": sorted(list(all_category_terms)),
            "all_description_terms": sorted(list(all_description_terms)),
            "all_usage_terms": sorted(list(all_usage_terms)),
        },
        "_metadata": {
            "total_categories": len(sheet_names),
            "total_product_names": len(all_product_names),
            "total_category_terms": len(all_category_terms),
            "total_description_terms": len(all_description_terms),
            "total_usage_terms": len(all_usage_terms),
            "generated_at": datetime.now().isoformat(),
            "source_file": "医疗器械分类目录.xlsx"
        }
    }

    # 写入文件
    OUTPUT_FILE.parent.mkdir(parents=True, exist_ok=True)
    with open(OUTPUT_FILE, 'w', encoding='utf-8') as f:
        json.dump(result, f, ensure_ascii=False, indent=2)

    print(f"\n{'='*60}")
    print("提取完成!")
    print(f"输出文件：{OUTPUT_FILE}")
    print(f"\n全局统计:")
    print(f"  品名举例术语：{len(all_product_names):,} 个")
    print(f"  三级分类术语：{len(all_category_terms):,} 个")
    print(f"  产品描述术语：{len(all_description_terms):,} 个")
    print(f"  预期用途术语：{len(all_usage_terms):,} 个")
    print(f"  总计（合并去重）：{len(all_product_names | all_category_terms | all_description_terms | all_usage_terms):,} 个唯一关键词")


if __name__ == "__main__":
    main()