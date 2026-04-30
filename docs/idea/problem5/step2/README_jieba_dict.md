# 医疗器械术语词表 - Jieba分词使用说明

## 处理结果

已成功将 `step1/output/医疗器械术语_八维度.json` 转换为jieba分词可用的词表格式。

### 生成文件位置

`step2/output/jieba_dict/`

### 文件列表

| 文件名 | 原始词汇数 | 去重后词汇数 | 说明 |
|--------|-----------|-------------|------|
| 01_有源手术器械.txt | 179 | 170 | |
| 02_无源手术器械.txt | 758 | 732 | |
| 03_神经和心血管手术器械.txt | 314 | 293 | |
| 04_骨科手术器械.txt | 791 | 766 | |
| 05_放射治疗器械.txt | 145 | 138 | |
| 06_医用成像器械.txt | 522 | 477 | |
| 07_医用诊察和监护器械.txt | 237 | 221 | |
| 08_呼吸、麻醉和急救器械.txt | 272 | 240 | |
| 09_物理治疗器械.txt | 250 | 246 | |
| 10_输血、透析和体外循环器械.txt | 224 | 214 | |
| 11_医疗器械消毒灭菌器械.txt | 70 | 58 | |
| 12_有源植入器械.txt | 127 | 120 | |
| 13_无源植入器械.txt | 324 | 307 | |
| 14_注输、护理和防护器械.txt | 942 | 898 | |
| 15_患者承载器械.txt | 140 | 136 | |
| 16_眼科器械.txt | 634 | 595 | |
| 17_口腔科器械.txt | 724 | 700 | |
| 18_妇产科、辅助生殖和避孕器械.txt | 307 | 299 | |
| 19_医用康复器械.txt | 147 | 141 | |
| 20_中医器械.txt | 121 | 111 | |
| 21_医用软件.txt | 81 | 76 | |
| 22_临床检验器械.txt | 581 | 565 | |
| **医疗器械术语_合并.txt** | **7890** | **7354** | **所有类别合并** |

## 词表格式

jieba分词支持的标准格式：`词语 词频 词性`

示例：
```
超声 1000 n
手术刀 1000 n
高频电刀 1000 n
```

- **词频**: 统一设为1000，确保这些词在分词时优先切分
- **词性**: 统一设为'n'（名词）

## 使用方法

### 基础用法

```python
import jieba

# 加载合并词表（推荐）
jieba.load_userdict("step2/output/jieba_dict/医疗器械术语_合并.txt")

# 分词示例
text = "这是一台超声手术刀，用于切割和凝固软组织。"
words = jieba.lcut(text)
print(words)
# 输出: ['这是', '一台', '超声手术刀', '，', '用于', '切割', '和', '凝固', '软组织', '。']
```

### 按类别加载

```python
import jieba

# 只加载特定类别
jieba.load_userdict("step2/output/jieba_dict/01_有源手术器械.txt")
jieba.load_userdict("step2/output/jieba_dict/02_无源手术器械.txt")
```

### 按需加载

```python
import jieba

# 先初始化jieba
jieba.initialize()

# 根据分类结果动态加载对应类别的词表
category = "01_有源手术器械"
jieba.load_userdict(f"step2/output/jieba_dict/{category}.txt")
```

## 处理脚本

- **转换脚本**: `step2/process/convert_to_jieba_dict.py`
- **使用示例**: `step2/process/jieba_usage_example.py`

运行转换脚本：
```bash
cd step2/process
python convert_to_jieba_dict.py
```

## 注意事项

1. **词频设置**: 统一为1000，可根据需要调整
2. **词性标记**: 统一为'n'，可按实际需要修改脚本
3. **去重策略**: 按类别内去重，合并词表全局去重
4. **加载时机**: 建议在程序初始化时加载一次，避免重复加载

## 数据来源

- 原始文件: `step1/output/医疗器械术语_八维度.json`
- 维度字段: 8个维度（category_indicators, clinical_domain, functional_level等）
- 类别数量: 22个医疗器械分类
