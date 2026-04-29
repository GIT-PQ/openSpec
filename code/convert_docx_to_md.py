#!/usr/bin/env python3
"""
将DOCX转换为Markdown
使用markitdown库
"""

from markitdown import MarkItDown
import os

# 输入文件路径
docx_file = "/Users/pangqin/Desktop/paper/openspec/docs/202364035-庞勤-基于LLM与深度学习的医疗器械专利自动分类研究与应用.docx"

# 输出文件路径（与输入文件同名，扩展名改为.md）
output_dir = os.path.dirname(docx_file)
output_file = os.path.join(output_dir, "论文内容.md")

print(f"正在转换: {docx_file}")
print(f"输出位置: {output_file}")

# 创建MarkItDown实例并转换
md = MarkItDown()
result = md.convert(docx_file)
markdown_content = result.text_content

# 写入文件
with open(output_file, mode="w", encoding="utf-8") as f:
    f.write(markdown_content)

print(f"\n转换完成！")
print(f"文件已保存至: {output_file}")
print(f"内容长度: {len(markdown_content)} 字符")
