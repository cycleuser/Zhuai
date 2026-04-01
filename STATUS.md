# Zhuai 开发状态

## ✅ 已完成所有功能

### 核心功能

1. **多数据源搜索**
   - ✅ arXiv - HTTP API，快速稳定，支持 HTML/Markdown 下载
   - ✅ PubMed - API + PMC 开放获取
   - ✅ CrossRef - Unpaywall 开放获取 PDF
   - ✅ Semantic Scholar - 学术搜索
   - ✅ CNKI - 浏览器访问
   - ✅ Wanfang - 浏览器访问
   - ✅ VIP - 浏览器访问

2. **高级搜索功能**
   - ✅ 字段限定搜索 (`title:`, `author:`, `journal:`, `year:`)
   - ✅ 作者过滤 (`--author "Smith; Johnson"`)
   - ✅ 标题关键词过滤 (`--title "deep learning"`)
   - ✅ 期刊过滤 (`--journal Nature`)
   - ✅ 年份/年份范围过滤 (`--year 2020-2024`)
   - ✅ JCR 分区过滤 (`--quartile Q1`)
   - ✅ CAS 分区过滤 (`--cas-quartile 1区`)
   - ✅ 最小引用数过滤 (`--min-citations 100`)
   - ✅ PDF 可用性过滤 (`--has-pdf`)
   - ✅ HTML 版本过滤 (`--has-html`)
   - ✅ 多输出格式 (`--format csv/json/html/all`)

3. **多格式下载** ✨ NEW
   - ✅ PDF 下载（默认）
   - ✅ HTML 下载（arXiv 论文）
   - ✅ Markdown 下载（从 HTML 转换）
   - ✅ 全部格式下载 (`--download-format all`)

4. **Web 界面**
   - ✅ 响应式搜索界面
   - ✅ 多数据源选择
   - ✅ 高级过滤面板
   - ✅ 实时搜索结果展示
   - ✅ 批量选择与下载
   - ✅ 引用格式生成（多格式）
   - ✅ CSV/JSON 导出
   - ✅ 期刊信息查询

5. **PDF/HTML 下载**
   - ✅ 异步并发下载
   - ✅ 重复文件跳过
   - ✅ PDF 有效性验证
   - ✅ arXiv HTML 版本检测

6. **导出功能**
   - ✅ CSV 导出（完整元数据）
   - ✅ JSON 导出
   - ✅ HTML 导出（可点击链接）
   - ✅ 双语引用格式（APA + GB/T 7714）

7. **期刊数据库**
   - ✅ 10,104 个期刊（来自 OpenAlex API）
   - ✅ ISSN、出版商、官网链接
   - ✅ JCR 分区、影响因子
   - ✅ CAS 分区、EI 收录状态
   - ✅ 可持续更新机制

### 使用示例

```bash
# 基础搜索
zhuai search "deep learning" -s arxiv -s pubmed --download

# 下载 PDF（默认）
zhuai search "transformer" -s arxiv --download

# 下载 HTML 版本（arXiv）
zhuai search "neural network" -s arxiv --download --download-format html

# 下载 Markdown 版本
zhuai search "machine learning" -s arxiv --download --download-format markdown

# 下载所有格式
zhuai search "deep learning" -s arxiv --download --download-format all

# 高级搜索 - 作者过滤
zhuai search "machine learning" --author "Hinton; LeCun" --year 2020-2024

# 高级搜索 - 分区过滤
zhuai search "transformer" --quartile Q1 --min-citations 100

# 高级搜索 - 字段限定
zhuai search "title:transformer author:Vaswani" --download

# 中文数据源
zhuai search "定和效应" -s cnki --max-results 10

# 启动 Web 界面
zhuai web --port 5000

# 指定输出格式
zhuai search "neural networks" --format all --output results.csv
```

### CLI 参数

| 参数 | 说明 |
|------|------|
| `-s, --sources` | 数据源选择 |
| `-n, --max-results` | 最大结果数 |
| `-o, --output` | 输出文件 |
| `-d, --download` | 下载论文 |
| `--download-format` | 下载格式 (pdf/html/markdown/all) |
| `-a, --author` | 作者过滤 |
| `-t, --title` | 标题关键词 |
| `-j, --journal` | 期刊过滤 |
| `--year` | 年份/范围 (如 2020-2024) |
| `-q, --quartile` | JCR 分区 (Q1/Q2/Q3/Q4) |
| `--cas-quartile` | CAS 分区 (1区/2区/3区/4区) |
| `--min-citations` | 最小引用数 |
| `--has-pdf` | 仅显示有 PDF 的论文 |
| `--has-html` | 仅显示有 HTML 版本的论文 |
| `-f, --format` | 输出格式 (csv/json/html/all) |

### 项目结构

```
zhuai/
├── __init__.py
├── cli.py                      # CLI 入口
├── core/
│   ├── searcher.py            # 主搜索类（含高级搜索）
│   ├── query_parser.py        # 查询解析器
│   ├── downloader.py          # 下载管理（支持多格式）
│   ├── citation.py            # 引用格式化
│   └── validator.py           # PDF 验证
├── web/                        # Web 模块
│   ├── app.py                 # Flask 应用
│   ├── templates/             # HTML 模板
│   └── static/                # 静态文件
├── models/
│   └── paper.py               # Paper 数据类（含 HTML 支持）
├── sources/
│   ├── base.py                # 数据源基类
│   ├── arxiv.py               # arXiv（含 HTML 检测）
│   ├── pubmed.py              # PubMed
│   ├── crossref.py            # CrossRef
│   ├── semanticscholar.py     # Semantic Scholar
│   ├── cnki.py                # CNKI
│   ├── wanfang.py             # 万方
│   ├── vip.py                 # 维普
│   └── browser_base.py        # 浏览器基类
├── journals/
│   ├── models.py              # 期刊数据模型
│   ├── manager.py             # 期刊管理器
│   ├── openalex_source.py     # OpenAlex API 获取器
│   └── data/
│       └── journals.json      # 10,104 期刊数据库
└── utils/
    ├── __init__.py
    └── html_converter.py      # HTML 到 Markdown 转换器 ✨ NEW
```

### 技术栈

- **CLI**: Click
- **Web**: Flask
- **浏览器自动化**: Playwright
- **HTTP 客户端**: httpx
- **数据格式**: dataclasses

---

**状态：开发完成，功能正常** ✅