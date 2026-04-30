- D:\WorkSpace\JupyterWorkSpace\pq\app\openSpec\docs\idea\problem5\step2\output\医疗器械分类目录_eb_with_full_structure_normalized.parquet
> '完整结构_eb_归一化'列的值是完整结构的嵌入向量
> '完整结构'列的值是由'三级序号/产品类别'、'产品描述'和'预期用途'值拼接而成的字符串
```python
['一级序号/产品类别', '二级序号/产品类别', '三级序号/产品类别', '产品描述', '预期用途', '品名举例', '管理类别','产品描述_eb', '预期用途_eb', '三级序号/产品类别_产品描述_预期用途_eb', '完整结构']
```


- D:\WorkSpace\JupyterWorkSpace\pq\app\openSpec\docs\idea\problem5\step2\output\D2_eb.parquet
> 'bge'是摘要列的值经过文本嵌入处理后的结果，是一个向量表示，包含了摘要文本的语义信息。
```python
['申请号', '申请日', '公开(公告)号', '法律状态/事件', '标题', '摘要', '独立权利要求', '第一权利要求','IPC主分类号', '大组', '一级产品类别（原始）', 'bge']
```

- D:\WorkSpace\JupyterWorkSpace\pq\app\openSpec\docs\idea\problem5\step2\input\D2.xlsx
> 用于存储预测的结果
> '一级产品类别（原始）' 原始的标签。
> '一级产品类别（校对）' 专家标注后的标签。

- D:\WorkSpace\JupyterWorkSpace\pq\app\openSpec\docs\idea\problem5\step2\output\jieba_dict
> 目录：医疗器械分类目录中所有的关键词，可用于分词和bm25
