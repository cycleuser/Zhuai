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

### ✅ 已验证可用

| 数据源 | 说明 | PDF支持 | 访问方式 |
|--------|------|---------|----------|
| arXiv | 预印本论文库 | ✅ | API |
| CrossRef | DOI数据库 | ✅ | API |

### ⚠️ 需要调试

**国际数据源：**
- PubMed - 生物医学文献
- Semantic Scholar - 学术搜索引擎
- Bing Academic - 微软学术

**中文数据源：**
- 知网 (CNKI)
- 万方数据
- 维普 (VIP)
- 百度学术

## 安装

```bash
pip install zhuai
playwright install chromium
```

## 使用

### 命令行

```bash
# 搜索论文
zhuai search "summation effect"

# 指定数据源
zhuai search "人工智能" --sources arxiv crossref

# 搜索并下载
zhuai search "summation effect" --download

# 查看支持的网站
zhuai sources
```

### Python代码

```python
from zhuai import PaperSearcher

# 创建搜索器（推荐只用可用的数据源）
searcher = PaperSearcher(sources=["arxiv", "crossref"])

# 搜索论文
papers = searcher.search_sync("summation effect", max_results=50)

# 下载PDF
download_results = searcher.download_papers_sync(papers)

# 导出结果（生成CSV和HTML）
searcher.export_papers_with_citations(
    papers, 
    download_results,
    output_dir="./output"
)
```

## 输出文件

运行后会生成以下文件：

### 已下载文献
- `available_papers.csv` - 包含引用和本地文件路径
- `available_papers.html` - 格式化HTML，可点击打开本地文件

### 未下载文献
- `unavailable_papers.csv` - 包含引用和下载链接
- `unavailable_papers.html` - 格式化HTML，可点击访问原文

### CSV文件内容

**已下载文献CSV：**
- 标题、作者、年份、期刊、DOI
- APA引用格式
- GB/T 7714引用格式（中国国家标准）
- 本地PDF文件路径
- 数据来源

**未下载文献CSV：**
- 标题、作者、年份、期刊、DOI
- APA引用格式
- GB/T 7714引用格式
- 原文链接
- DOI链接

## 核心特性

- **搜索**：从arXiv和CrossRef搜索论文
- **下载**：自动下载PDF，跳过已存在的文件
- **引用**：自动生成APA和GB/T 7714格式引用
- **导出**：CSV和HTML两种格式
- **去重**：基于DOI和标题自动去重

## 测试结果

✅ **已验证功能：**
- arXiv搜索：✓ 正常
- CrossRef搜索：✓ 正常
- PDF下载：✓ 正常（自动跳过重复文件）
- CSV导出：✓ 正常（含引用和路径/链接）
- HTML导出：✓ 正常（格式化显示）

📊 **测试统计：**
- 搜索文献：20篇
- 下载PDF：11个
- 输出文件：CSV和HTML格式完整

## 许可证

GPL v3 License

## 联系方式

- GitHub: https://github.com/cycleuser/Zhuai
- 作者: CycleUser

---

**拽** - 简单好用，输出规范！