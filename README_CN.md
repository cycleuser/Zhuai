# Zhuai (拽)

<div align="center">

[![Python](https://img.shields.io/badge/Python-3.8%2B-blue.svg)](https://www.python.org/)
[![License](https://img.shields.io/badge/License-GPL%20v3-green.svg)](LICENSE)
[![GitHub](https://img.shields.io/badge/GitHub-cycleuser%2FZhuai-blue.svg)](https://github.com/cycleuser/Zhuai)

**拽** - 简单好用的学术文献搜索工具

[中文](README_CN.md) | [English](README_EN.md)

</div>

---

## 这是什么？

Zhuai（拽）是一个简单的工具，帮你从网上找文章和下载论文。设计简洁，使用方便。

## 能做什么？

- 从多个网站搜索论文（arXiv、PubMed、知网、万方等）
- 自动下载PDF文件
- 导出搜索结果到CSV
- 生成文献引用格式

## 支持哪些网站？

**国际网站：**
- arXiv - 预印本论文
- PubMed - 生物医学文献
- CrossRef - DOI数据库
- Semantic Scholar - 学术搜索引擎
- Bing Academic - 微软学术

**中文网站：**
- 知网 (CNKI)
- 万方数据
- 维普 (VIP)
- 百度学术

## 怎么安装？

```bash
# 安装工具
pip install zhuai

# 如果要用浏览器访问中文网站，还需要安装浏览器
playwright install chromium
```

或者从源码安装：

```bash
git clone https://github.com/cycleuser/Zhuai.git
cd Zhuai
pip install -e .
playwright install chromium
```

## 怎么用？

### 命令行

```bash
# 搜索论文
zhuai search "深度学习"

# 指定网站搜索
zhuai search "人工智能" --sources cnki wanfang

# 搜索并下载
zhuai search "summation effect" --download

# 查看支持的网站
zhuai sources
```

### Python代码

```python
from zhuai import PaperSearcher

# 创建搜索器
searcher = PaperSearcher()

# 搜索论文
papers = searcher.search_sync("定和效应", max_results=50)

# 下载PDF
searcher.download_papers_sync(papers)

# 保存结果
searcher.export_to_csv(papers, "results.csv")

# 导出无法下载的论文引用
searcher.export_unavailable_citations(papers, "citations.txt")
```

### 选择特定网站

```python
# 只用中文网站
searcher = PaperSearcher(sources=["cnki", "wanfang", "baidu"])

# 只用API网站（速度快）
searcher = PaperSearcher(sources=["arxiv", "pubmed", "semanticscholar"])

# 自定义组合
searcher = PaperSearcher(sources=["arxiv", "cnki", "pubmed"])
```

## 引用格式

支持几种常见的引用格式：

- **APA** - 美国心理学会格式
- **MLA** - 现代语言协会格式
- **Chicago** - 芝加哥格式
- **GB/T 7714** - 中国国家标准
- **BibTeX** - LaTeX格式
- **Simple** - 简单格式

## 输出什么？

### CSV文件
包含论文的详细信息：标题、作者、年份、期刊、DOI、摘要等

### 引用文件
对于无法下载PDF的论文，会生成两个文件：

1. **文本文件**（unavailable_citations.txt）：简单文本格式
2. **CSV文件**（unavailable_citations_with_citations.csv）：包含以下信息：
   - 论文基本信息（标题、作者、年份、期刊等）
   - 下载链接和DOI
   - 5种国际标准引用格式（APA、GB/T 7714、MLA、Chicago、BibTeX）

这个CSV文件包含了中英文双语的标准引用格式，方便直接使用。

## 技术细节

- 使用异步并发提高效率
- 支持浏览器自动化访问需要交互的网站
- 智能去重，避免重复结果
- 完整的类型提示

## 开发相关

```bash
# 安装开发工具
pip install -e ".[dev]"

# 运行测试
pytest

# 代码格式化
black . && isort .
```

## 许可证

GPL v3 License

## 有问题？

- 提Issue：https://github.com/cycleuser/Zhuai/issues
- 看代码：https://github.com/cycleuser/Zhuai

---

**拽** - 简单好用，就这么简单