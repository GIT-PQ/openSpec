"""
实验: BERT-BiGRU 中文专利文本分类 (刘燕, 2023)
来源: 基于BERT-BiGRU的中文专利文本自动分类[J].郑州大学学报(理学版),2023
超参数: lr=3e-5, epoch=5, batch_size=64, dropout=0.1
"""
import os
import sys
import random
import logging
import numpy as np
import pandas as pd
import torch
import torch.nn as nn
from datetime import datetime
from sklearn.model_selection import train_test_split
from sklearn.preprocessing import LabelEncoder
from sklearn.metrics import classification_report, f1_score, accuracy_score
from torch.utils.data import Dataset, DataLoader
from transformers import BertModel, BertTokenizer
from tqdm import tqdm

# ==================== 配置 ====================
SEED = 42
DATA_PATHS = ["./数据集/D1数据集_矫正输血类.parquet", "./数据集/增强数据集.parquet"]
BERT_PATH = "./预训练模型/bert/chinese-roberta-wwm-ext"
TEXT_COL = "摘要"
LABEL_COL = "标注结果"
MAX_LEN = 512
BATCH_SIZE = 64
LR = 3e-5
EPOCHS = 30          # 论文5轮，加早停保底
DROPOUT = 0.1
GRU_HIDDEN = 256
FREEZE_LAYERS = 11   # 微调第12层
PATIENCE = 3
WEIGHT_DECAY = 0.001
LABEL_SMOOTHING = 0.1
OUTPUT_DIR = "./深度学习分类结果/数据增强之后/对比实验"

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
class BertBiGRU(nn.Module):
    def __init__(self, model_path, class_num, freeze_layers=11, gru_hidden=256, dropout=0.1):
        super().__init__()
        self.bert = BertModel.from_pretrained(model_path)
        for name, param in self.bert.named_parameters():
            if any(f"encoder.layer.{i}." in name for i in range(freeze_layers)):
                param.requires_grad = False

        self.gru = nn.GRU(
            input_size=self.bert.config.hidden_size,
            hidden_size=gru_hidden,
            num_layers=1,
            batch_first=True,
            bidirectional=True,
        )
        self.dropout = nn.Dropout(dropout)
        self.fc = nn.Linear(gru_hidden * 2, class_num)

    def forward(self, input_ids, attention_mask):
        bert_out = self.bert(input_ids=input_ids, attention_mask=attention_mask)
        embeddings = bert_out.last_hidden_state  # [B, L, H]

        gru_out, _ = self.gru(embeddings)  # [B, L, gru_hidden*2]

        # Mean pooling (mask padding)
        mask = attention_mask.unsqueeze(-1).float()
        masked = gru_out * mask
        mean_pooled = masked.sum(dim=1) / mask.sum(dim=1).clamp(min=1e-8)

        return self.fc(self.dropout(mean_pooled))

# ==================== 训练 ====================
def train():
    set_seed(SEED)
    device = torch.device("cuda" if torch.cuda.is_available() else "cpu")

    ts = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
    save_dir = os.path.join(OUTPUT_DIR, f"{ts}_BERT-BiGRU")
    os.makedirs(save_dir, exist_ok=True)

    logging.basicConfig(
        level=logging.INFO, filename=os.path.join(save_dir, "train.log"),
        filemode='w', format='%(asctime)s - %(message)s', encoding='utf-8'
    )
    logging.info(f"配置: lr={LR}, batch={BATCH_SIZE}, dropout={DROPOUT}, "
                 f"gru_hidden={GRU_HIDDEN}, freeze_layers={FREEZE_LAYERS}")

    (train_t, train_l), (valid_t, valid_l), (test_t, test_l), target_names = load_and_split()
    tokenizer = BertTokenizer.from_pretrained(BERT_PATH)

    train_loader = DataLoader(TextDataset(train_t, train_l), batch_size=BATCH_SIZE, shuffle=True,
                              collate_fn=lambda b: collate_fn(b, tokenizer, MAX_LEN))
    valid_loader = DataLoader(TextDataset(valid_t, valid_l), batch_size=BATCH_SIZE, shuffle=False,
                              collate_fn=lambda b: collate_fn(b, tokenizer, MAX_LEN))
    test_loader = DataLoader(TextDataset(test_t, test_l), batch_size=BATCH_SIZE, shuffle=False,
                             collate_fn=lambda b: collate_fn(b, tokenizer, MAX_LEN))

    class_num = len(target_names)
    model = nn.DataParallel(BertBiGRU(BERT_PATH, class_num, FREEZE_LAYERS, GRU_HIDDEN, DROPOUT))
    model.to(device)

    optimizer = torch.optim.AdamW(model.parameters(), lr=LR, weight_decay=WEIGHT_DECAY)
    scheduler = torch.optim.lr_scheduler.ReduceLROnPlateau(optimizer, 'min', patience=2, factor=0.5)
    criterion = nn.CrossEntropyLoss(label_smoothing=LABEL_SMOOTHING)

    best_f1, best_epoch, counter = 0, 0, 0

    for epoch in range(1, EPOCHS + 1):
        # ---- 训练 ----
        model.train()
        total_loss = 0
        for input_ids, attn_mask, labels in tqdm(train_loader, desc=f"Epoch {epoch}", ncols=80):
            input_ids, attn_mask, labels = input_ids.to(device), attn_mask.to(device), labels.to(device)
            loss = criterion(model(input_ids, attn_mask), labels)
            loss.backward()
            optimizer.step()
            optimizer.zero_grad()
            total_loss += loss.item()

        # ---- 验证 ----
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

        # ---- 测试 ----
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
            torch.save(model.state_dict(), os.path.join(save_dir, "best_model.pth"))
        else:
            counter += 1
            if counter >= PATIENCE:
                logging.info(f"早停: 验证集macro_f1 {PATIENCE}轮未提升, 最佳在第{best_epoch}轮")
                break

    logging.info(f"训练完成, 验证集最佳macro_f1={best_f1:.4f}(第{best_epoch}轮)")

if __name__ == "__main__":
    train()
