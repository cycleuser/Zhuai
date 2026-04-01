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

- **多数据源搜索**：arXiv、PubMed、CrossRef、Semantic Scholar、知网、万方、维普
- **高级过滤**：按作者、标题、期刊、年份、分区、引用数过滤
- **PDF 下载**：自动下载，跳过重复文件
- **引用生成**：APA、MLA、Chicago、GB/T 7714、BibTeX 等格式
- **Web 界面**：浏览器访问，支持高级筛选
- **期刊数据库**：10,000+ 期刊，含 JCR/CAS 分区信息
- **多格式导出**：CSV、JSON、HTML

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
results = searcher.download_papers_sync(papers)

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

## CLI 命令

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