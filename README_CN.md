# Zhuai (拽)

<div align="center">

[![Python](https://img.shields.io/badge/Python-3.8%2B-blue.svg)](https://www.python.org/)
[![License](https://img.shields.io/badge/License-GPL%20v3-green.svg)](LICENSE)
[![GitHub](https://img.shields.io/badge/GitHub-cycleuser%2FZhuai-blue.svg)](https://github.com/cycleuser/Zhuai)

**拽** - 学术论文检索、下载与引用工具

[English](README.md)

</div>

---

## 功能特点

- **多数据源论文搜索**：arXiv、PubMed、CrossRef、Semantic Scholar、知网、万方、维普
- **平台资源搜索**：GitHub、Hugging Face、Kaggle、ModelScope
- **高级过滤**：按作者、标题、期刊、年份、分区、引用数过滤
- **多格式下载**：PDF、HTML、Markdown
- **趋势发现**：获取热门仓库、模型、数据集
- **README 提取**：从仓库和模型提取文档
- **引用生成**：APA、MLA、Chicago、GB/T 7714、BibTeX
- **Web 界面**：浏览器访问
- **期刊数据库**：10,000+ 期刊，含 JCR/CAS 分区信息

## 安装

```bash
pip install zhuai
```

或从源码安装：

```bash
git clone https://github.com/cycleuser/Zhuai.git
cd Zhuai
pip install -e .
```

## 使用方法

### 命令行

```bash
# 基础搜索
zhuai search "deep learning" -s arxiv -s pubmed --download

# 下载 PDF（默认）
zhuai search "transformer" -s arxiv --download

# 下载 HTML 版本（有 HTML 的 arXiv 论文）
zhuai search "neural network" -s arxiv --download --download-format html

# 下载 Markdown 版本（从 HTML 转换）
zhuai search "machine learning" -s arxiv --download --download-format markdown

# 下载所有格式
zhuai search "deep learning" -s arxiv --download --download-format all

# 高级过滤
zhuai search "machine learning" --author "Hinton" --year 2020-2024

# 按分区过滤
zhuai search "transformer" --quartile Q1 --min-citations 100

# 字段限定搜索
zhuai search "title:neural network author:LeCun"

# Web 界面
zhuai web --port 5000
```

### Python API

```python
from zhuai import PaperSearcher

# 创建搜索器
searcher = PaperSearcher(sources=["arxiv", "pubmed", "crossref"])

# 搜索论文
papers = searcher.search_sync("deep learning", max_results=50)

# 下载 PDF
results = searcher.download_papers_sync(papers, format="pdf")

# 下载 HTML 版本
results = searcher.download_papers_sync(papers, format="html")

# 下载 Markdown 版本
results = searcher.download_papers_sync(papers, format="markdown")

# 下载所有格式
results = searcher.download_papers_sync(papers, format="all")

# 导出结果
searcher.export_to_csv(papers, "results.csv")

# 生成引用
searcher.export_unavailable_citations(papers, "citations.txt", style="apa")
```

### 带过滤条件的高级搜索

```python
from zhuai import PaperSearcher
from zhuai.core.query_parser import SearchFilter

searcher = PaperSearcher()

# 创建过滤器
search_filter = SearchFilter(
    authors=["Hinton", "LeCun"],
    year_from=2020,
    year_to=2024,
    jcr_quartile="Q1",
    min_citations=100
)

# 使用过滤条件搜索
papers = searcher.search_advanced_sync(
    query="neural networks",
    search_filter=search_filter,
    max_results=50
)
```

## 平台资源搜索

搜索代码仓库、模型和数据集：

```bash
# GitHub
zhuai search-platforms "transformer" -p github -l python
zhuai trending -p github -l python --since weekly
zhuai repo-info "microsoft/transformers" -p github

# Hugging Face
zhuai search-platforms "bert" -p huggingface -t model
zhuai search-platforms "image dataset" -p huggingface -t dataset

# HF Mirror（国内加速）
zhuai search-platforms "llama" -p hfmirror

# Kaggle
zhuai search-platforms "image classification" -p kaggle -t dataset

# ModelScope
zhuai search-platforms "qwen" -p modelscope
```

### Python API

```python
from zhuai.sources.github import GitHubSource
from zhuai.sources.huggingface import HuggingFaceSource

# GitHub
github = GitHubSource()
repos = github.search("transformer", language="python", min_stars=100)
readme = github.get_readme("owner", "repo")

# Hugging Face
hf = HuggingFaceSource()
models = hf.search_models("bert", task="text-generation")
datasets = hf.search_datasets("image classification")
```

## 支持的数据源

| 数据源 | 类型 | PDF |
|--------|------|-----|
| arXiv | API | ✅ |
| PubMed | API | ✅ |
| CrossRef | API | ✅ |
| Semantic Scholar | API | ✅ |
| 知网 (CNKI) | 浏览器 | ✅ |
| 万方数据 | 浏览器 | ✅ |
| 维普 (VIP) | 浏览器 | ✅ |

## 支持的平台

| 平台 | 资源类型 | 功能 |
|------|---------|------|
| GitHub | 代码 | 搜索、趋势、README、Releases |
| Hugging Face | 模型、数据集 | 搜索、Model Card、文件 |
| HF Mirror | 模型、数据集 | 国内加速访问 |
| Kaggle | 数据集、模型 | 搜索、文件 |
| ModelScope | 模型、数据集 | 搜索、文件 |

## CLI 命令

| 命令 | 说明 |
|------|------|
| `zhuai search` | 搜索论文 |
| `zhuai search-platforms` | 搜索仓库/模型/数据集 |
| `zhuai trending` | 获取趋势资源 |
| `zhuai repo-info` | 获取仓库/模型详情 |
| `zhuai get-readme` | 获取 README 内容 |
| `zhuai web` | 启动 Web 界面 |
| `zhuai journals` | 搜索期刊 |
| `zhuai sources` | 列出数据源 |

| 命令 | 说明 |
|------|------|
| `zhuai search` | 搜索论文 |
| `zhuai web` | 启动 Web 界面 |
| `zhuai journals` | 搜索期刊 |
| `zhuai journal-info` | 查看期刊详情 |
| `zhuai sources` | 列出数据源 |

## CLI 参数

| 参数 | 说明 |
|------|------|
| `-s, --sources` | 数据源选择 |
| `-n, --max-results` | 最大结果数 |
| `-d, --download` | 下载 PDF |
| `-a, --author` | 作者过滤 |
| `-j, --journal` | 期刊过滤 |
| `--year` | 年份/范围 (如 2020-2024) |
| `-q, --quartile` | JCR 分区 (Q1/Q2/Q3/Q4) |
| `--min-citations` | 最小引用数 |
| `--has-pdf` | 仅显示有 PDF 的论文 |
| `-f, --format` | 输出格式 (csv/json/html/all) |

## Web 界面

启动 Web 服务：

```bash
zhuai web
# 访问 http://localhost:5000
```

Web 功能：
- 多数据源搜索
- 高级过滤面板
- 批量下载
- 多种引用格式
- CSV/JSON 导出

## 引用格式

- **APA** - 美国心理学会格式
- **MLA** - 现代语言协会格式
- **Chicago** - 芝加哥格式
- **GB/T 7714** - 中国国家标准
- **BibTeX** - LaTeX 格式

## 期刊数据库

10,000+ 期刊，包含：
- ISSN、出版商、官网链接
- JCR 分区、影响因子
- CAS 分区（1区/2区/3区/4区）
- EI 收录状态

```bash
# 搜索期刊
zhuai journals "nature"

# 按分区过滤
zhuai journals "computer" --quartile Q1 --sci

# 查看期刊详情
zhuai journal-info 0028-0836
```

## 系统要求

- Python 3.8+
- Chromium 浏览器（部分数据源需要，由 Playwright 自动安装）

## 开发

```bash
# 安装开发依赖
pip install -e ".[dev]"

# 运行测试
pytest

# 格式化代码
black . && isort .
```

## 许可证

GPL v3 License

## 链接

- 问题反馈: https://github.com/cycleuser/Zhuai/issues
- 代码仓库: https://github.com/cycleuser/Zhuai

---

**拽** - 简单好用的学术论文检索工具