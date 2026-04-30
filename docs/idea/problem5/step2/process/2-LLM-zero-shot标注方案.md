# LLM Zero-Shot 标注方案

## 目标

作为实验对照组②，验证"裸LLM"（无领域知识注入）在医疗器械专利分类上的表现，证明领域适配的必要性。

## 方法定位

```
方法                    分类目录    分类规则    RAG检索
─────────────────────────────────────────────────
① 关键词匹配(BM25)       ✗          ✗         ✗
② LLM zero-shot         ✗          ✗         ✗    ← 本方案
③ LLM + 分类目录        ✓(全量)     ✗         ✗
④ 你的方法(RAG+规则)     ✓(检索)     ✓         ✓
```

**核心原则：** 不注入任何领域知识，仅提供22个类别名称和简短描述，测试LLM自身语义理解能力。

## Prompt 设计

### System Prompt

```
你是一位专利分类专家。你的任务是将医疗器械相关专利分类到以下22个类别之一。

22个医疗器械类别如下：
1. 中医器械 - 基于中医理论的诊断、治疗器械
2. 临床检验器械 - 用于实验室检验、体外诊断的器械
3. 医用康复器械 - 用于患者康复训练的器械
4. 医用成像器械 - 用于医学影像的器械（如X光、CT、MRI、超声成像等）
5. 医用诊察和监护器械 - 用于生理参数监测、诊察的器械
6. 医用软件 - 医疗用途的独立软件
7. 医疗器械消毒灭菌器械 - 用于医疗器械消毒灭菌的设备
8. 口腔科器械 - 牙科、口腔科专用器械
9. 呼吸、麻醉和急救器械 - 呼吸支持、麻醉、急救用器械
10. 妇产科、辅助生殖和避孕器械 - 妇产科及生殖健康相关器械
11. 患者承载器械 - 手术床、轮椅、担架等承载患者的器械
12. 放射治疗器械 - 用于放射治疗的设备及配套器械
13. 无源手术器械 - 不依赖电源的手术器械（如手术刀、钳、剪等）
14. 无源植入器械 - 植入体内且无源动的器械（如人工关节、骨板等）
15. 有源手术器械 - 依赖电源的手术器械（如电刀、超声刀、激光手术设备等）
16. 有源植入器械 - 植入体内且有源动的器械（如心脏起搏器等）
17. 注输、护理和防护器械 - 注射、输液、护理防护用品
18. 物理治疗器械 - 利用物理因子（光、电、热、磁等）进行治疗的器械
19. 眼科器械 - 眼科专用诊断、手术器械
20. 神经和心血管手术器械 - 神经外科和心血管手术专用器械
21. 输血、透析和体外循环器械 - 血液处理和体外循环相关器械
22. 骨科手术器械 - 骨科手术专用器械

分类规则：
- 每条专利必须且只能归入一个类别
- 请根据专利的标题和摘要内容判断其主要功能和用途
- 当专利涉及多个类别时，选择其主要功能或核心用途对应的类别
- 请仅输出类别编号（1-22），不要输出其他内容
```

### User Prompt

```
请对以下专利进行分类：

摘要：{abstract}

请输出该专利所属的类别编号（1-22）。
```

## 类别描述说明

类别描述的设计原则：

1. **简短但区分性强**——每类仅1句话，控制在20字以内，避免注入过多领域知识
2. **突出核心特征**——用"用于XX"的功能描述，而非枚举具体产品
3. **消除歧义**——对容易混淆的类别加括号举例（如"有源手术器械"标注"电刀、超声刀"以区别于"无源手术器械"）
4. **不引用分类目录原文**——描述来自通用认知，不抄录分类目录，确保这是LLM自身知识而非检索知识

## 易混淆类别对及区分要点

以下类别对在zero-shot下最易混淆，prompt中已通过描述区分：

| 类别对 | 混淆原因 | prompt中的区分策略 |
|--------|----------|-------------------|
| 有源手术器械 vs 无源手术器械 | 都是手术器械 | 明确标注"依赖电源"vs"不依赖电源"，并给典型例子 |
| 有源植入器械 vs 无源植入器械 | 都是植入器械 | 同上，标注"有源动"vs"无源动"，举例心脏起搏器vs人工关节 |
| 医用成像器械 vs 物理治疗器械 | 都可能用到超声/电磁 | 成像强调"医学影像"，治疗强调"利用物理因子治疗" |
| 神经和心血管手术器械 vs 骨科手术器械 | 都是手术专科器械 | 明确标注"神经外科和心血管"vs"骨科" |
| 注输、护理和防护器械 vs 呼吸、麻醉和急救器械 | 都涉及患者支持 | 注输强调"注射输液护理防护"，呼吸强调"呼吸支持麻醉急救" |

## 批量标注实现

```python
import json
import pandas as pd
from openai import OpenAI  # 或其他LLM客户端

client = OpenAI(api_key="your-api-key", base_url="your-base-url")

SYSTEM_PROMPT = """（同上 System Prompt）"""

def classify_patent_zero_shot(title: str, abstract: str) -> dict:
    """使用LLM zero-shot对专利进行分类"""

    user_prompt = f"""请对以下专利进行分类：

标题：{title}
摘要：{abstract}

请输出该专利所属的类别编号（1-22）。"""

    response = client.chat.completions.create(
        model="your-model-name",  # 与你的方法使用同一模型
        messages=[
            {"role": "system", "content": SYSTEM_PROMPT},
            {"role": "user", "content": user_prompt}
        ],
        temperature=0,  # 确保结果可复现
        max_tokens=10,   # 只需输出一个数字
    )

    raw_output = response.choices[0].message.content.strip()

    # 解析输出
    try:
        pred_idx = int(raw_output) - 1  # 转为0-indexed
        if 0 <= pred_idx < 22:
            pred_label = LABELS[pred_idx]
        else:
            pred_label = "解析错误"
    except ValueError:
        pred_label = "解析错误"

    return {
        "pred_label": pred_label,
        "raw_output": raw_output
    }


# 批量标注
LABELS = [
    '中医器械', '临床检验器械', '医用康复器械', '医用成像器械', '医用诊察和监护器械', '医用软件',
    '医疗器械消毒灭菌器械', '口腔科器械', '呼吸、麻醉和急救器械', '妇产科、辅助生殖和避孕器械',
    '患者承载器械', '放射治疗器械', '无源手术器械', '无源植入器械', '有源手术器械', '有源植入器械',
    '注输、护理和防护器械', '物理治疗器械', '眼科器械', '神经和心血管手术器械', '输血、透析和体外循环器械', '骨科手术器械'
]

df = pd.read_json("待标注数据路径")
results = []

for idx, row in df.iterrows():
    pred = classify_patent_zero_shot(row["title"], row["abstract"])
    results.append({
        "patent_id": row.get("id", ""),
        "title": row["title"],
        "true_label": row["label"],
        "pred_label": pred["pred_label"],
        "raw_output": pred["raw_output"]
    })
    if (idx + 1) % 100 == 0:
        print(f"已处理 {idx + 1}/{len(df)}")

result_df = pd.DataFrame(results)
result_df.to_csv("llm_zeroshot_results.csv", index=False, encoding="utf-8-sig")

# 评估
from sklearn.metrics import classification_report, accuracy_score
valid = result_df[result_df["pred_label"] != "解析错误"]
print(f"有效预测: {len(valid)}/{len(result_df)}")
print(f"Accuracy: {accuracy_score(valid['true_label'], valid['pred_label']):.4f}")
print(classification_report(valid['true_label'], valid['pred_label']))
```

## 关键实验控制变量

| 变量 | 取值 | 理由 |
|------|------|------|
| LLM模型 | 与你的方法使用**同一模型** | 控制模型能力变量，仅对比领域知识注入的效果 |
| temperature | 0 | 确保结果可复现 |
| 类别描述 | 1句话通用描述 | 不引用分类目录原文，避免隐性注入领域知识 |
| 分类规则 | 仅"每条一个类别"+"按主要功能判断" | 不提供分类目录中的专业判定规则 |

## 预期结果与分析要点

### 预期表现

Zero-shot LLM 在以下类别上可能表现尚可：
- **类别名称直观**：中医器械、口腔科器械、眼科器械、骨科手术器械——名称本身足够区分
- **功能边界清晰**：医用软件、放射治疗器械——功能描述独特

Zero-shot LLM 在以下类别上预计表现较差：
- **有源/无源区分**：需要专业知识才能判断器械是否有源
- **细分专科器械**：神经和心血管手术器械 vs 骨科手术器械——需要了解手术场景
- **功能重叠类别**：物理治疗器械 vs 医用成像器械——超声既可成像也可治疗

### 论文分析角度

1. **整体准确率对比**：zero-shot vs 你的方法，量化领域知识的价值
2. **混淆矩阵分析**：zero-shot在哪些类别对上容易混淆？你的方法如何解决？
3. **错误模式分析**：zero-shot的错误集中在"需要领域知识才能区分"的类别，证明领域适配（RAG+分类规则）的必要性
4. **与BM25对比**：zero-shot可能在小样本/短文本上优于BM25（语义理解 > 关键词匹配），但在专业术语密集的类别上可能不如BM25

## 依赖

```
openai>=1.0.0  # 或其他LLM SDK
pandas
scikit-learn
```
