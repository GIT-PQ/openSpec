from sentence_transformers import SentenceTransformer
import os
import pandas as pd


from utils.pretreatment_utils import sim_embedding,sbert_embedding_v2

model_infos = {
    # "all-MiniLM-L6-v2": "all-MiniLM-L6-v2",
    # "sbert-base-chinese-nli": "sbert-base-chinese-nli",
    # "text2vec-base-chinese": "text2vec-base-chinese",
    # "text2vec-base-chinese-sentence":"text2vec-base-chinese-sentence",
    # "bge-large-zh": "bge-large-zh",
    # "text2vec-bge-large-chinese":"text2vec-bge-large-chinese",
    # "paecter":"paecter"
    "bge-large-zh-v1.5":"bge-large-zh-v1.5"
}

model_dir = "D:/WorkSpace/JupyterWorkSpace/pq/模型/预训练模型/sbert"
sval_dir = "./embedding"
if not os.path.exists(sval_dir):
    os.makedirs(sval_dir, exist_ok=True)

#data = pd.read_parquet("I:\pq\A61B\D1\数据集\D1数据集.xlsx")
filepath = "../input/D2.xlsx"
savepath = "../output/D2_eb.parquet"
data = pd.read_excel(filepath)
# data = data.iloc[:10].copy()

save_embedding = True

for model_name in model_infos:
    # file_name = f"4.数据集_22_at_dropNa_附图_label1.parquett"
    model_path = os.path.join(model_dir, model_name)
    # model = SentenceTransformer(model_path)
    # data = sbert_embedding_v2(data.copy(), model_path, text_col='产品描述', target_col='产品描述_eb', batch_size=512)
    # data = sbert_embedding_v2(data.copy(), model_path, text_col='预期用途', target_col='预期用途_eb', batch_size=512)
    # ca = '三级序号/产品类别_产品描述_预期用途'
    # data[ca] = data['三级序号/产品类别']+':'+data['产品描述'] + data['预期用途']
    # data = sbert_embedding_v2(data.copy(), model_path, text_col=ca, target_col='三级序号/产品类别_产品描述_预期用途_eb',batch_size=512)
    # del data[ca]
    # data = sbert_embedding_v2(data.copy(), model_path, text_col='标题', target_col='title_eb', batch_size=256)
    data = sbert_embedding_v2(data.copy(), model_path, text_col='摘要', target_col='bge', batch_size=32)

    # result = sim_embedding(df_embed)
    print(data.columns)
    if save_embedding:
        # result.to_parquet(os.path.join(sval_dir, file_name))
        data.to_parquet(savepath)
        # data.to_excel(filepath,index=False)
    # print(result.shape)
    #
    # # 筛选数据
    # # 主分类号属于 keep_all_years 或者 申请日在 start_date 和 end_date 之间
    # keep_all_years = ['A61B7', 'A61B9', 'A61B46', 'A61B42', 'A61B13']
    # start_date = '2019-01-01'
    # end_date = '2023-12-31'
    #
    # A61B_clean = result[
    #     (result['大组'].isin(keep_all_years)) |
    #     ((result['申请日'] >= start_date) & (result['申请日'] <= end_date))
    #     ]
    # print(A61B_clean.shape)
    #
    # plt_sim_margin(result, model_name)
    # plt_sim_margin(A61B_clean, model_name,file_prefix='5')
