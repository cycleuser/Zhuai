# Zhuai (拽)

<div align="center">

[![Python](https://img.shields.io/badge/Python-3.8%2B-blue.svg)](https://www.python.org/)
[![License](https://img.shields.io/badge/License-GPL%20v3-green.svg)](LICENSE)
[![GitHub](https://img.shields.io/badge/GitHub-cycleuser%2FZhuai-blue.svg)](https://github.com/cycleuser/Zhuai)

**拽** - 简单好用的学术文献搜索工具，支持 Vision AI 全自动处理

</div>

---

## 这是什么？

Zhuai（拽）是一个简单的工具，帮你从网上找文章和下载论文。使用本地视觉模型自动处理验证码和页面解析，**完全自动化，无需人工干预**。

## 主要功能

- **全自动运行**：Vision AI 自动处理验证码和页面解析
- **多数据源搜索**：arXiv、PubMed、CNKI、万方、维普、CrossRef 等
- **PDF 下载**：自动下载，跳过重复文件
- **双语引用**：支持 APA + GB/T 7714 格式
- **CSV/HTML 导出**：完整元数据，可点击链接

## 支持的网站

### 国际数据源（API 接口，无验证码）
- arXiv - 预印本论文库
- PubMed - 生物医学文献
- CrossRef - DOI 数据库
- Semantic Scholar - 学术搜索引擎

### 中文数据源（Vision AI 自动处理）
- 知网 (CNKI) - 自动验证码识别
- 万方数据 - 自动验证码识别
- 维普 (VIP) - 自动验证码识别

## 安装

```bash
# 安装工具
pip install zhuai

# 安装浏览器（中文数据源需要）
playwright install chromium

# 安装 Ollama（Vision AI 必需）
# macOS/Linux:
curl -fsSL https://ollama.com/install.sh | sh

# 下载视觉模型
ollama pull gemma3:4b
```

或从源码安装：

```bash
git clone https://github.com/cycleuser/Zhuai.git
cd Zhuai
pip install -e .
playwright install chromium
```

## 使用

### 基本搜索

```bash
# 国际数据源（快速，无验证码）
zhuai search "deep learning" -s arxiv -s pubmed --download

# 中文数据源（Vision AI 自动处理验证码）
zhuai search "定和效应" -s cnki --max-results 10

# 多个数据源
zhuai search "人工智能" -s arxiv -s cnki -s pubmed
```

### 高级选项

```bash
# 指定视觉模型
zhuai search "高维度空间距离" -s cnki --vision-model gemma3:4b

# 从浏览器导入登录 Cookies
zhuai search "定和效应" -s cnki --import-browser firefox

# 调整结果数量
zhuai search "机器学习" -s arxiv --max-results 50 --download

# 查看支持的数据源
zhuai sources
```

### Python API

```python
from zhuai import PaperSearcher

# 创建搜索器
searcher = PaperSearcher(
    sources=["arxiv", "cnki", "pubmed"],
    vision_model="gemma3:4b"
)

# 搜索论文
papers = searcher.search_sync("summation effect", max_results=50)

# 下载 PDF
results = searcher.download_papers_sync(papers)

# 保存结果
searcher.export_to_csv(papers, "results.csv")

# 导出引用
searcher.export_unavailable_citations(papers, "citations.txt", style="apa")
```

## Vision AI 功能

Zhuai 使用本地 Ollama 视觉模型实现完全自动化：

1. **自动验证码检测**：截图分析页面状态
2. **验证码自动解决**：
   - 滑块验证码：计算拖动距离，模拟鼠标移动
   - 点击验证码：识别点击位置
   - 文字验证码：OCR 识别并输入
3. **页面解析**：当 CSS 选择器失效时，Vision AI 从截图提取论文信息

### 支持的视觉模型

- `gemma3:4b`（默认，推荐）
- `gemma3:1b`（更快，精度略低）
- 任何 Ollama 兼容的视觉模型

## 引用格式

- **APA** - 美国心理学会格式
- **MLA** - 现代语言协会格式
- **Chicago** - 芝加哥格式
- **GB/T 7714** - 中国国家标准
- **BibTeX** - LaTeX 格式

## 输出文件

### CSV 文件
包含：标题、作者、年份、期刊、DOI、PDF URL、来源、语言

### 引用文件
对于无法下载的论文：
- `unavailable.txt` - 文本格式引用
- `results.csv` - 完整元数据和引用

## 技术特点

- **异步操作**：并发搜索，效率高
- **Playwright Stealth**：隐藏自动化痕迹
- **Vision AI**：基于 Ollama 的本地视觉模型
- **类型注解**：完整的类型提示

## 系统要求

- Python 3.8+
- Ollama + 视觉模型（中文数据源需要）
- Chromium 浏览器（Playwright 自动安装）

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

**拽** - 简单、全自动、无需人工干预