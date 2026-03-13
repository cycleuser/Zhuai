# Zhuai (拽)

<div align="center">

[![Python](https://img.shields.io/badge/Python-3.8%2B-blue.svg)](https://www.python.org/)
[![License](https://img.shields.io/badge/License-GPL%20v3-green.svg)](LICENSE)
[![GitHub](https://img.shields.io/badge/GitHub-cycleuser%2FZhuai-blue.svg)](https://github.com/cycleuser/Zhuai)

**拽** - 简单好用的学术文献搜索工具

</div>

---

## 这是什么？

Zhuai（拽）是一个简单的工具，帮你从网上找文章和下载论文。

## 能做什么？

- 从多个网站搜索论文
- 自动下载PDF文件
- 导出搜索结果
- 生成文献引用

## 支持的网站

**国际：** arXiv, PubMed, CrossRef, Semantic Scholar, Bing Academic

**中文：** 知网, 万方, 维普, 百度学术

## 安装

```bash
pip install zhuai
playwright install chromium
```

## 使用

```bash
# 搜索
zhuai search "深度学习"

# 指定网站
zhuai search "人工智能" --sources cnki wanfang

# 下载
zhuai search "summation effect" --download
```

```python
from zhuai import PaperSearcher

searcher = PaperSearcher()
papers = searcher.search_sync("定和效应")
searcher.download_papers_sync(papers)
searcher.export_to_csv(papers, "results.csv")
```

## 许可证

GPL v3 License