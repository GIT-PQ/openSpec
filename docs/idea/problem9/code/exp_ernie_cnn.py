"""
实验: ERNIE-CNN 中文专利分类 (雷海卫, 2023)
来源: 基于ERNIE的中文专利分类研究[J].信息技术与信息化,2023
超参数: lr=1e-5, epoch=3, batch_size=16, max_len=400
"""
import os
import random
import logging
import numpy as np
import pandas as pd
import torch
import torch.nn as nn
import torch.nn.functional as F
from datetime import datetime
from sklearn.model_selection import train_test_split
from sklearn.preprocessing import LabelEncoder
from sklearn.metrics import classification_report, f1_score, accuracy_score
from torch.utils.data import Dataset, DataLoader
from transformers import AutoModel, AutoTokenizer
from tqdm import tqdm

# ==================== 配置 ====================
SEED = 42

# --- 数据路径（迁移服务器时修改此处）---
DATA_PATHS = [
    "D:/WorkSpace/JupyterWorkSpace/pq/app/openSpec/docs/idea/start/output/数据集_D2_D3高置信.parquet",
    "D:/WorkSpace/JupyterWorkSpace/pq/app/openSpec/docs/idea/start/output/增强数据集_输血透析体外循环.parquet",
]
ERNIE_PATH = "D:/WorkSpace/JupyterWorkSpace/pq/模型/预训练模型/bert/ernie-3.0-base-zh"

TEXT_COL = "摘要"
LABEL_COL = "last_label"

# --- 论文超参数（保持不变）---
SAMPLE_PER_CLASS = 0   # 每类抽样条数，0=使用全部数据
EPOCHS = 3             # 论文设定
BATCH_SIZE = 16        # 论文设定（显存不足时可用梯度累积模拟）
ACCUMULATION_STEPS = 4 # 梯度累积步数，BATCH_SIZE//ACCUMULATION_STEPS为实际batch
MAX_LEN = 400          # 论文设定
LR = 1e-5              # 论文设定

# --- 模型超参数 ---
DROPOUT = 0.1
CNN_KERNELS = [2, 3, 4, 5]
CNN_CHANNELS = 256
FREEZE_LAYERS = 11
PATIENCE = 3
WEIGHT_DECAY = 0.001
LABEL_SMOOTHING = 0.1
OUTPUT_DIR = "./output"

# ==================== 种子 ====================
def set_seed(seed):
    random.seed(seed)
    np.random.seed(seed)
    torch.manual_seed(seed)
    torch.cuda.manual_seed_all(seed)
    torch.backends.cudnn.deterministic = True
    torch.backends.cudnn.benchmark = False

# ==================== 数据 ====================
class TextDataset(Dataset):
    def __init__(self, texts, labels):
        self.samples = list(zip(texts, labels))
    def __len__(self):
        return len(self.samples)
    def __getitem__(self, idx):
        return self.samples[idx]

def collate_fn(batch, tokenizer, max_length):
    texts = [item[0] for item in batch]
    labels = torch.tensor([item[1] for item in batch], dtype=torch.long)
    enc = tokenizer(texts, add_special_tokens=True, padding=True,
                    truncation=True, return_tensors="pt", max_length=max_length)
    return enc["input_ids"], enc["attention_mask"], labels

def load_and_split():
    dfs = []
    for p in DATA_PATHS:
        if os.path.exists(p):
            dfs.append(pd.read_parquet(p))
        else:
            print(f"警告: 文件不存在 {p}")
    data = pd.concat(dfs, ignore_index=True)
    data = data[data[LABEL_COL].notna()]
    print(f"总数据: {len(data)}")

    if SAMPLE_PER_CLASS > 0:
        data = data.groupby(LABEL_COL, group_keys=False).apply(
            lambda g: g.sample(n=min(SAMPLE_PER_CLASS, len(g)), random_state=SEED)
        ).reset_index(drop=True)
        print(f"调试抽样: 每类{SAMPLE_PER_CLASS}条, 共{len(data)}条")

    le = LabelEncoder()
    le.fit(data[LABEL_COL])
    target_names = list(le.classes_)

    train_df, tv_df = train_test_split(data, test_size=0.2, random_state=SEED, stratify=data[LABEL_COL])
    valid_df, test_df = train_test_split(tv_df, test_size=0.5, random_state=SEED, stratify=tv_df[LABEL_COL])

    def to_set(df):
        return df[TEXT_COL].tolist(), le.transform(df[LABEL_COL]).tolist()

    print(f"训练/验证/测试: {len(train_df)}/{len(valid_df)}/{len(test_df)}")
    return to_set(train_df), to_set(valid_df), to_set(test_df), target_names

# ==================== 模型 ====================
class ErnieCNN(nn.Module):
    def __init__(self, model_path, class_num, freeze_layers=11,
                 kernel_sizes=[2,3,4,5], num_channels=256, dropout=0.1):
        super().__init__()
        # 使用AutoModel正确加载ERNIE
        self.bert = AutoModel.from_pretrained(model_path)
        for name, param in self.bert.named_parameters():
            if any(f"encoder.layer.{i}." in name for i in range(freeze_layers)):
                param.requires_grad = False

        hidden_size = self.bert.config.hidden_size
        self.convs = nn.ModuleList([
            nn.Conv1d(hidden_size, num_channels, k) for k in kernel_sizes
        ])
        self.dropout = nn.Dropout(dropout)
        self.fc = nn.Linear(num_channels * len(kernel_sizes), class_num)

    def forward(self, input_ids, attention_mask):
        bert_out = self.bert(input_ids=input_ids, attention_mask=attention_mask)
        embeddings = bert_out.last_hidden_state
        x = embeddings.permute(0, 2, 1)
        conv_outs = []
        for conv in self.convs:
            c = F.relu(conv(x))
            c = F.max_pool1d(c, c.size(2)).squeeze(2)
            conv_outs.append(c)
        cat = torch.cat(conv_outs, dim=1)
        return self.fc(self.dropout(cat))

# ==================== 训练 ====================
def train():
    set_seed(SEED)
    device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
    actual_batch = max(1, BATCH_SIZE // ACCUMULATION_STEPS)
    print(f"设备: {device}, 等效batch={BATCH_SIZE}(实际{actual_batch}x{ACCUMULATION_STEPS}累积)")

    ts = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
    save_dir = os.path.join(OUTPUT_DIR, f"{ts}_ERNIE-CNN")
    os.makedirs(save_dir, exist_ok=True)

    logging.basicConfig(
        level=logging.INFO, filename=os.path.join(save_dir, "train.log"),
        filemode='w', format='%(asctime)s - %(message)s', encoding='utf-8'
    )
    logging.info(f"配置: lr={LR}, batch={BATCH_SIZE}(实际{actual_batch}x{ACCUMULATION_STEPS}累积), max_len={MAX_LEN}, dropout={DROPOUT}, "
                 f"kernels={CNN_KERNELS}, channels={CNN_CHANNELS}, freeze_layers={FREEZE_LAYERS}, "
                 f"sample_per_class={SAMPLE_PER_CLASS}, epochs={EPOCHS}")

    (train_t, train_l), (valid_t, valid_l), (test_t, test_l), target_names = load_and_split()
    # 使用AutoTokenizer正确加载ERNIE tokenizer
    tokenizer = AutoTokenizer.from_pretrained(ERNIE_PATH)

    train_loader = DataLoader(TextDataset(train_t, train_l), batch_size=actual_batch, shuffle=True,
                              collate_fn=lambda b: collate_fn(b, tokenizer, MAX_LEN))
    valid_loader = DataLoader(TextDataset(valid_t, valid_l), batch_size=actual_batch, shuffle=False,
                              collate_fn=lambda b: collate_fn(b, tokenizer, MAX_LEN))
    test_loader = DataLoader(TextDataset(test_t, test_l), batch_size=actual_batch, shuffle=False,
                             collate_fn=lambda b: collate_fn(b, tokenizer, MAX_LEN))

    class_num = len(target_names)
    model = ErnieCNN(ERNIE_PATH, class_num, FREEZE_LAYERS,
                     CNN_KERNELS, CNN_CHANNELS, DROPOUT)
    if torch.cuda.device_count() > 1:
        print(f"使用多卡并行: {torch.cuda.device_count()} 张GPU")
        model = nn.DataParallel(model)
    model.to(device)

    optimizer = torch.optim.AdamW(model.parameters(), lr=LR, weight_decay=WEIGHT_DECAY)
    scheduler = torch.optim.lr_scheduler.ReduceLROnPlateau(optimizer, 'min', patience=2, factor=0.5)
    criterion = nn.CrossEntropyLoss(label_smoothing=LABEL_SMOOTHING)

    best_f1, best_epoch, counter = 0, 0, 0

    for epoch in range(1, EPOCHS + 1):
        model.train()
        total_loss = 0
        optimizer.zero_grad()
        for i, (input_ids, attn_mask, labels) in enumerate(tqdm(train_loader, desc=f"Epoch {epoch}", ncols=80)):
            input_ids, attn_mask, labels = input_ids.to(device), attn_mask.to(device), labels.to(device)
            # 梯度累积：损失除以累积步数
            loss = criterion(model(input_ids, attn_mask), labels) / ACCUMULATION_STEPS
            loss.backward()
            total_loss += loss.item() * ACCUMULATION_STEPS

            # 每累积ACCUMULATION_STEPS步才更新参数
            if (i + 1) % ACCUMULATION_STEPS == 0:
                optimizer.step()
                optimizer.zero_grad()

        model.eval()
        v_preds, v_labels, v_loss = [], [], 0.0
        with torch.no_grad():
            for input_ids, attn_mask, labels in valid_loader:
                input_ids, attn_mask, labels = input_ids.to(device), attn_mask.to(device), labels.to(device)
                out = model(input_ids, attn_mask)
                v_loss += criterion(out, labels).item()
                v_preds.extend(torch.argmax(out, dim=1).cpu().numpy())
                v_labels.extend(labels.cpu().numpy())

        v_acc = accuracy_score(v_labels, v_preds)
        v_f1 = f1_score(v_labels, v_preds, average='macro')
        v_report = classification_report(v_labels, v_preds, digits=4, target_names=target_names)

        logging.info(f"Epoch {epoch}: train_loss={total_loss:.4f}, valid_loss={v_loss:.4f}, "
                     f"valid_acc={v_acc:.4f}, valid_macro_f1={v_f1:.4f}")
        logging.info(f"\n验证集分类报告:\n{v_report}")

        t_preds, t_labels = [], []
        with torch.no_grad():
            for input_ids, attn_mask, labels in test_loader:
                input_ids, attn_mask, labels = input_ids.to(device), attn_mask.to(device), labels.to(device)
                t_preds.extend(torch.argmax(model(input_ids, attn_mask), dim=1).cpu().numpy())
                t_labels.extend(labels.cpu().numpy())

        t_acc = accuracy_score(t_labels, t_preds)
        t_f1 = f1_score(t_labels, t_preds, average='macro')
        t_report = classification_report(t_labels, t_preds, digits=4, target_names=target_names)

        logging.info(f"测试集: acc={t_acc:.4f}, macro_f1={t_f1:.4f}")
        logging.info(f"\n测试集分类报告:\n{t_report}")

        scheduler.step(v_loss)

        if v_f1 > best_f1:
            best_f1, best_epoch, counter = v_f1, epoch, 0
            state_dict = model.module.state_dict() if hasattr(model, 'module') else model.state_dict()
            torch.save(state_dict, os.path.join(save_dir, "best_model.pth"))
        else:
            counter += 1
            if counter >= PATIENCE:
                logging.info(f"早停: 验证集macro_f1 {PATIENCE}轮未提升, 最佳在第{best_epoch}轮")
                break

    logging.info(f"训练完成, 验证集最佳macro_f1={best_f1:.4f}(第{best_epoch}轮)")
    print(f"训练完成, 最佳macro_f1={best_f1:.4f}(第{best_epoch}轮), 日志: {save_dir}")

if __name__ == "__main__":
    train()