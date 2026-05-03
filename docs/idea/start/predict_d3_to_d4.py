"""
D3预测脚本：对D1中isD2=False的样本进行预测，筛选错误样本作为D4
"""
import os
import sys
import torch
import torch.nn.functional as F
import pandas as pd
from tqdm import tqdm
from transformers import BertTokenizer
from omegaconf import OmegaConf

# 添加模型路径
sys.path.insert(0, r'D:\WorkSpace\JupyterWorkSpace\pq\app\zl-back-py')
from utils.model_utils import get_model

# === 标签映射（与训练一致）===
LABELS = [
    '中医器械', '临床检验器械', '医用康复器械', '医用成像器械', '医用诊察和监护器械', '医用软件',
    '医疗器械消毒灭菌器械', '口腔科器械', '呼吸、麻醉和急救器械', '妇产科、辅助生殖和避孕器械',
    '患者承载器械', '放射治疗器械', '无源手术器械', '无源植入器械', '有源手术器械', '有源植入器械',
    '注输、护理和防护器械', '物理治疗器械', '眼科器械', '神经和心血管手术器械', '输血、透析和体外循环器械', '骨科手术器械'
]

def load_model(config_path, model_path, num_labels=22):
    """加载模型"""
    config = OmegaConf.load(config_path)

    # 将配置中的相对路径转换为绝对路径（相对于zl-back-py目录）
    base_dir = r"D:\WorkSpace\JupyterWorkSpace\pq\app\zl-back-py"
    config.input.pre_train_model.dir = os.path.join(base_dir, config.input.pre_train_model.dir)

    device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
    print(f"[INFO] 使用设备: {device}")

    model = get_model(config, num_labels)
    # 注意：训练时用了DataParallel，加载时也需要包装
    model = torch.nn.DataParallel(model)

    state_dict = torch.load(model_path, map_location=device)
    model.load_state_dict(state_dict)
    model.to(device)
    model.eval()

    print(f"[INFO] 模型加载成功: {model_path}")
    return model, config, device


def batch_predict(model, tokenizer, texts, device, batch_size=16, max_length=512):
    """批量预测"""
    results = []

    for i in tqdm(range(0, len(texts), batch_size), desc="预测进度"):
        batch_texts = texts[i:i+batch_size]

        # 编码
        encoded = tokenizer(
            batch_texts,
            return_tensors="pt",
            max_length=max_length,
            truncation=True,
            padding=True
        )
        if "token_type_ids" in encoded:
            del encoded["token_type_ids"]

        encoded = {k: v.to(device) for k, v in encoded.items()}

        # 预测
        with torch.no_grad():
            outputs = model(**encoded)
            logits = outputs if isinstance(outputs, torch.Tensor) else outputs[0]
            probs = F.softmax(logits, dim=-1)
            pred_indices = torch.argmax(probs, dim=-1).cpu().tolist()

        for j, pred_idx in enumerate(pred_indices):
            results.append({
                "pred_index": pred_idx,
                "pred_label": LABELS[pred_idx]
            })

    return results


def main():
    # === 路径配置 ===
    # d1_path = r"D:\WorkSpace\JupyterWorkSpace\pq\app\openSpec\docs\idea\start\D1数据集.parquet"
    d1_path = r"D:\WorkSpace\JupyterWorkSpace\pq\app\openSpec\docs\idea\start\D1数据集_矫正输血类.parquet"
    model_dir = r"D:\WorkSpace\JupyterWorkSpace\pq\app\zl-back-py\myModel"
    output_path = r"D:\WorkSpace\JupyterWorkSpace\pq\app\openSpec\docs\idea\start\D4_矫正输血类_错误样本.xlsx"

    # === 加载模型 ===
    config_path = os.path.join(model_dir, "curr_config.yaml")
    model_path = os.path.join(model_dir, "best_model.pth")
    model, config, device = load_model(config_path, model_path, num_labels=len(LABELS))

    # === 加载分词器 ===
    bert_path = r"D:\WorkSpace\JupyterWorkSpace\pq\app\zl-back-py\preTModel\bert\chinese-roberta-wwm-ext"
    tokenizer = BertTokenizer.from_pretrained(bert_path)
    print(f"[INFO] 分词器加载成功: {bert_path}")

    # === 加载D1数据集 ===
    print(f"[INFO] 加载数据集: {d1_path}")
    df = pd.read_parquet(d1_path)
    print(f"[INFO] 数据集总量: {len(df)}")

    # === 筛选D3 (isD2=False) ===
    d3 = df[df['isD2'] == False].copy()
    print(f"[INFO] D3样本数 (isD2=False): {len(d3)}")

    # === 提取摘要进行预测 ===
    texts = d3['摘要'].astype(str).tolist()

    # === 批量预测 (4060 8G, batch_size设为16) ===
    batch_size = 128
    max_length = config.model.BERT.max_length
    results = batch_predict(model, tokenizer, texts, device, batch_size=batch_size, max_length=max_length)

    # === 合并预测结果 ===
    d3['pred_label'] = [r['pred_label'] for r in results]
    d3['pred_index'] = [r['pred_index'] for r in results]

    # === 筛选错误样本作为D4 ===
    d4 = d3[d3['pred_label'] != d3['标注结果']].copy()
    print(f"[INFO] D4错误样本数: {len(d4)}")

    # === 保存D4 ===
    # 只保留指定字段
    save_cols = ['申请号', '摘要', 'pred_label', '标注结果']
    d4_save = d4[save_cols].copy()
    d4_save.columns = ['申请号', '摘要', '预测标签', '真实标签']

    d4_save.to_excel(output_path, index=False)
    print(f"[INFO] D4已保存: {output_path}")

    # === 统计 ===
    print("\n=== 预测统计 ===")
    print(f"D3总量: {len(d3)}")
    print(f"正确: {len(d3) - len(d4)} ({(len(d3)-len(d4))/len(d3)*100:.2f}%)")
    print(f"错误: {len(d4)} ({len(d4)/len(d3)*100:.2f}%)")


if __name__ == "__main__":
    main()
