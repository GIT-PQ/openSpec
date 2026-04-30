from collections import Counter

import numpy as np
import pandas as pd
import os
import re

from joblib import Parallel, delayed
from sentence_transformers import SentenceTransformer
from sklearn.preprocessing import LabelEncoder
from sklearn.preprocessing import normalize
from tqdm import tqdm
import torch
from torch.nn import Identity

def merge_xlsx_file(dirPath,save=False,saveDir='',newFileName=''):
    merged_df = pd.DataFrame()
    for filename in os.listdir(dirPath):
        if filename.endswith('.XLSX'):
            file_path = os.path.join(dirPath, filename)
            # 读取每个 .xlsx 文件并将其追加到合并的 DataFrame
            df = pd.read_excel(file_path)
            merged_df = pd.concat([merged_df, df], ignore_index=True)
    if save:
        if not os.path.exists(saveDir):
            os.makedirs(saveDir)
        merged_df.to_csv(saveDir+newFileName, index=False,encoding='utf-8')
    merged_df.sort_values(by='申请日')
    return merged_df

def get_classification_label(A61B,cols):
    label = '标签_大组'
    cols.append(label)
    label_encoder = LabelEncoder()
    A61B[label] = label_encoder.fit_transform(A61B['大组'])
    A61B[['大组', label]].value_counts()

    label = '标签_小组'
    cols.append(label)
    label_encoder = LabelEncoder()
    A61B[label] = label_encoder.fit_transform(A61B['IPC主分类号'])
    A61B[['IPC主分类号', label]].value_counts()
    A61B = A61B[cols]
    print(A61B.columns)
    print(A61B.info())
    return A61B

def text_len_analysis(A61B,target_cols):
    A61B = A61B.copy()
    BERT_MAX_LEN = 510  # BERT的最大长度

    # 计算每列的文本长度
    length_stats = {}
    for col in target_cols:
        A61B[f'{col}_长度'] = A61B[col].str.len()
        over_count = (A61B[f'{col}_长度'] > BERT_MAX_LEN).sum()  # 超出数量
        total_count = A61B[col].shape[0]  # 总数量

        length_stats[col] = {
            '平均值': A61B[f'{col}_长度'].mean(),
            '标准差': A61B[f'{col}_长度'].std(),
            '最大值': A61B[f'{col}_长度'].max(),
            '75分位数': A61B[f'{col}_长度'].quantile(0.75),
            '中位数': A61B[f'{col}_长度'].median(),
            '25分位数': A61B[f'{col}_长度'].quantile(0.25),
            '最小值': A61B[f'{col}_长度'].min(),
            '超BERT比例(%)': (over_count / total_count) * 100,
            '超BERT数量': over_count
        }

    # 转换为DataFrame便于查看
    stats_df = pd.DataFrame(length_stats).T
    stats_df = stats_df.round(2)  # 保留两位小数
    return stats_df

def clean_text(text, remove_all_spaces=True, unify_punctuation=False):
    """
    清洗文本
    参数:
        text: 原始文本
        remove_all_spaces: 是否删除所有空格（默认True）
        unify_punctuation: 是否统一标点为中文格式（默认False）
    返回:
        清洗后的文本
    """
    if not isinstance(text, str):
        return text

    # 1. 删除HTML标签
    text = re.sub(r'<[^>]+>', '', text)

    # 2. 删除不可见控制字符（保留换行符）
    text = ''.join(char for char in text if ord(char) >= 32 or char in {'\n', '\r', '\t'})

    # 3. 标点统一处理
    if unify_punctuation:
        punct_map = {
            ',': '，', '.': '。', '!': '！', '?': '？',
            ':': '：', ';': '；', '(': '（', ')': '）'
        }
        text = ''.join(punct_map.get(c, c) for c in text)

    # 4. 空格处理
    if remove_all_spaces:
        text = re.sub(r'\s+', '', text)  # 删除所有空格
    else:
        text = re.sub(r'\s+', ' ', text)  # 替换多个空格为一个空格

    return text

def process_abstract_column(df, column_name='abstract', **clean_kwargs):
    """
    处理DataFrame中的摘要列（增强版）

    参数:
        df: 输入的DataFrame
        column_name: 要处理的列名
        clean_kwargs: 传递给clean_abstract_text的参数

    返回:
        cleaned_df: 清洗后的DataFrame
        changed_rows: 变化对比DataFrame
        change_stats: 变化统计字典
    """
    cleaned_df = df.copy()
    original = df[column_name].astype(str).copy()

    # 应用清洗函数
    cleaned = original.apply(lambda x: clean_text(x, **clean_kwargs))
    cleaned_df[column_name] = cleaned

    # 生成变化报告
    changed_mask = original != cleaned
    changed_rows = pd.DataFrame({
        '原始内容': original[changed_mask],
        '清洗后': cleaned[changed_mask]
    })

    # 计算变化统计
    change_stats = {
        '总行数': len(df),
        '修改行数': changed_mask.sum(),
        '修改比例': f"{changed_mask.mean():.1%}",
        '空格删除量': sum(len(s.split()) - 1 for s in original if isinstance(s, str)),
        'HTML标签删除量': sum(len(re.findall(r'<[^>]+>', s)) for s in original if isinstance(s, str))
    }

    return cleaned_df, changed_rows, change_stats


def _encode_batch(batch_texts, model_path, device_id, batch_size, normalize_embeddings):
    device = f"cuda:{device_id}"
    model = SentenceTransformer(model_path, device=device)
    # 如果是bge模型 取消模型的默认归一化结构
    if model_path.find('bge'):
        model[2] = Identity()
    embeddings = model.encode(
        batch_texts,
        batch_size=batch_size,
        show_progress_bar=False,
        device=device,
        convert_to_numpy=True,
        normalize_embeddings=normalize_embeddings
    )
    return embeddings

def sbert_embedding_v2(df, model_path, text_col='摘要', target_col = 'SBERT_Embedding',batch_size=1024):
    df = df.copy()
    texts = df[text_col].tolist()
    total = len(texts)

    n_gpus = torch.cuda.device_count()
    assert n_gpus > 0, "没有可用的GPU设备"

    # 切分数据
    batches = [texts[i:i + batch_size] for i in range(0, total, batch_size)]
    num_batches = len(batches)

    # 轮询GPU分配任务
    tasks = [(batches[i], model_path, i % n_gpus, batch_size // n_gpus) for i in range(num_batches)]

    print(f"使用 {n_gpus} 个 GPU 进行并行嵌入，共 {num_batches} 个批次...")

    results = Parallel(n_jobs=n_gpus)(
        delayed(_encode_batch)(batch_texts, model_path, device_id, bsz, normalize_embeddings=False)
        for batch_texts, model_path, device_id, bsz in tqdm(tasks)
    )


    all_embeddings = np.vstack(results)
    # all_embeddings = normalize(all_embeddings)
    print(all_embeddings.shape)

    df[target_col] = list(all_embeddings)
    return df

def sim_embedding(data,batch_size=512,class_col='大组',embedding_col='abstract_eb',l2_norm=True):
    embeddings = np.stack(data[embedding_col].values)  # shape: (N, dim)
    labels = data[class_col].values  # 类别标签
    # 所有类别及其索引
    unique_classes = np.unique(labels)
    num_classes = len(unique_classes)

    # 构建每类对应样本的索引列表
    class_to_indices = {cls: np.where(labels == cls)[0] for cls in unique_classes}

    # =======================
    # Step 2: 转换为 PyTorch Tensor 并归一化
    # =======================
    device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
    embeddings_tensor = torch.tensor(embeddings, dtype=torch.float32).to(device)  # (N, dim)
    if l2_norm:
        embeddings_tensor = torch.nn.functional.normalize(embeddings_tensor, p=2, dim=1)  # L2归一化

    # 初始化相似度矩阵 (N, num_classes)
    similarity_matrix = torch.zeros((len(data), num_classes), device=device)

    # =======================
    # Step 3: 逐类处理
    # =======================
    batch_size = batch_size

    for i, cls in enumerate(tqdm(unique_classes, desc="Processing by class")):
        cls_indices = class_to_indices[cls]  # 当前类的样本索引
        cls_embeddings = embeddings_tensor[cls_indices]  # 当前类的样本嵌入 (N_cls, dim)

        for j, other_cls in enumerate(unique_classes):
            # if cls == other_cls:
            #     continue  # 跳过自身类
            other_indices = class_to_indices[other_cls]
            other_embeddings = embeddings_tensor[other_indices]  # 其他类的嵌入

            # 分批计算当前类的样本与该其他类的所有样本的余弦相似度
            sim_results = []

            for start in range(0, len(cls_indices), batch_size):
                end = min(start + batch_size, len(cls_indices))
                batch_emb = cls_embeddings[start:end]  # (batch, dim)
                sim = torch.matmul(batch_emb, other_embeddings.T)  # (batch, other_class_size)
                sim_mean = sim.mean(dim=1)  # (batch,)
                sim_results.append(sim_mean)

            # 拼接结果，并写入 similarity_matrix
            similarity_matrix[cls_indices, j] = torch.cat(sim_results)

    # =======================
    # Step 4: 保存结果到 DataFrame
    # =======================
    # 从 GPU 拷贝回 CPU
    sim_numpy = similarity_matrix.cpu().numpy()

    # 构造列名
    sim_columns = [f"SimTo_{cls}" for cls in unique_classes]
    sim_df = pd.DataFrame(sim_numpy, columns=sim_columns)

    # 合并原始数据
    result_df = pd.concat([data.reset_index(drop=True), sim_df], axis=1)
    sim_columns = [col for col in result_df.columns if col.startswith("SimTo_")]

    # 提取类内相似度
    def extract_intra(row):
        cls = row[class_col]
        return row[f"SimTo_{cls}"]

    # 提取类间相似度（即非自身类的平均）
    def extract_inter_avg(row):
        cls = row[class_col]
        other_sims = [col for col in sim_columns if col != f"SimTo_{cls}"]
        return row[other_sims].mean()

    # 提取类间相似度（即非自身类的最大值）
    def extract_inter_max(row):
        cls = row[class_col]
        other_sims = [col for col in sim_columns if col != f"SimTo_{cls}"]
        return row[other_sims].max()
    col1 = f'{class_col}类内相似度'
    col2 = f'{class_col}类间相似度avg'
    col3 = f'{class_col}类间相似度max'
    col4 = f'{class_col}类内-类间avg'
    col5 = f'{class_col}类内-类间max'
    # 添加新列
    result_df[col1] = result_df.apply(extract_intra, axis=1)
    result_df[col2] = result_df.apply(extract_inter_avg, axis=1)
    result_df[col3] = result_df.apply(extract_inter_max, axis=1)
    result_df[col4] = result_df[col1] - result_df[col2]
    result_df[col5] = result_df[col1] - result_df[col3]
    return result_df



def analyze_ipc_classification(df, start_date, end_date,save=False,file_prefix=''):
    """
    对指定时间范围内的数据进行IPC分类分析，并保存到Excel文件。

    参数：
    - df: pd.DataFrame，包含数据的DataFrame。
    - start_date: str，起始日期（格式：'YYYY-MM-DD'）。
    - end_date: str，终止日期（格式：'YYYY-MM-DD'）。

    输出：
    - str，保存的文件路径。
    """
    # 筛选时间范围内的数据
    df_filtered = df[(df['申请日'] >= start_date) & (df['申请日'] <= end_date)]

    # 数据处理部分
    subgroup = df_filtered['IPC主分类号'].value_counts()
    group = df_filtered['IPC主分类号'].apply(lambda x: x.split('/')[0]).value_counts()
    subclass = df_filtered['IPC主分类号'].apply(lambda x: x.split('/')[0][:4]).value_counts()
    classs = df_filtered['IPC主分类号'].apply(lambda x: x.split('/')[0][:3]).value_counts()

    # 转换为DataFrame并重命名列
    subgroup_df = pd.DataFrame(subgroup).reset_index()
    subgroup_df.columns = ['IPC主分类号', 'count']
    group_df = pd.DataFrame(group).reset_index()
    group_df.columns = ['IPC主分类号', 'count']
    subclass_df = pd.DataFrame(subclass).reset_index()
    subclass_df.columns = ['IPC主分类号', 'count']
    classs_df = pd.DataFrame(classs).reset_index()
    classs_df.columns = ['IPC主分类号', 'count']

    # 排序
    subgroup_sorted = subgroup_df.sort_values(by='IPC主分类号', ascending=True)
    group_sorted = group_df.sort_values(by='IPC主分类号', ascending=True)
    subclass_sorted = subclass_df.sort_values(by='IPC主分类号', ascending=True)
    classs_sorted = classs_df.sort_values(by='IPC主分类号', ascending=True)

    saveDir = 'D:\WorkSpace\JupyterWorkSpace\专利分类\A61专利\IPC分类号分析'
    if save:
        if not os.path.exists(saveDir):
            os.makedirs(saveDir)
            # 输出文件路径
        output_path = f'{saveDir}{file_prefix}_{start_date}_to_{end_date}.xlsx'
        # 保存到Excel文件
        with pd.ExcelWriter(output_path, engine='xlsxwriter') as writer:
            subgroup_sorted.to_excel(writer, sheet_name='Subgroup', index=False)
            group_sorted.to_excel(writer, sheet_name='Group', index=False)
            subclass_sorted.to_excel(writer, sheet_name='Subclass', index=False)
            classs_sorted.to_excel(writer, sheet_name='Classs', index=False)
    return subgroup_sorted, group_sorted, subclass_sorted, classs_sorted

# 提取并统计词频
def extract_keywords_by_frequency(keywords, min_frequency=3):
    # 用空格分隔并统计词频
    all_words = " ".join(keywords)

    # 使用正则去除非中文字符
    all_words = re.sub(r'[^a-zA-Z\u4e00-\u9fa5]', ' ', all_words)

    # 统计每个词的频率
    word_counts = Counter(all_words.split())

    # 提取频率大于给定值的关键词
    filtered_keywords = {word: count for word, count in word_counts.items() if count >= min_frequency}

    return filtered_keywords