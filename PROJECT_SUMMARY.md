# Zhuai (拽) - 项目说明

## 项目概述

**Zhuai（拽）** 是一个强大的学术文献搜索和下载工具，支持中英文学术数据库的访问和文献获取。

## 主要特性

### 1. 多源搜索
- ✅ **国际数据源**：arXiv, PubMed, CrossRef, Semantic Scholar, Bing Academic
- ✅ **中文数据源**：知网(CNKI), 万方, 维普, 百度学术
- ✅ **混合搜索**：支持同时从多个数据源搜索

### 2. 浏览器自动化
- ✅ 使用 Playwright 实现浏览器自动化
- ✅ 模拟真实用户访问行为
- ✅ 支持需要交互的学术网站
- ✅ 可配置无头/有头模式

### 3. 文献管理
- ✅ PDF 自动下载
- ✅ 智能去重
- ✅ 标准引用格式生成
- ✅ CSV 导出

### 4. 双语支持
- ✅ 中文关键词搜索
- ✅ 英文关键词搜索
- ✅ 中文文献引用格式（GB/T 7714）

## 安装

```bash
# 安装包
pip install zhuai

# 安装浏览器自动化支持
playwright install chromium
```

## 使用方法

### 命令行

```bash
# 基本搜索
zhuai search "深度学习"

# 指定数据源
zhuai search "人工智能" --sources cnki wanfang

# 搜索并下载
zhuai search "summation effect" --download

# 列出所有数据源
zhuai sources
```

### Python API

```python
from zhuai import PaperSearcher

# 创建搜索器（默认所有数据源）
searcher = PaperSearcher()

# 搜索文献
papers = searcher.search_sync("深度学习", max_results=50)

# 指定数据源搜索
papers = searcher.search_sync(
    "artificial intelligence",
    sources=["arxiv", "semanticscholar"],
    max_results=50
)

# 下载PDF
results = searcher.download_papers_sync(papers)

# 导出结果
searcher.export_to_csv(papers, "results.csv")

# 导出无法下载的文献引用
searcher.export_unavailable_citations(
    papers,
    "citations.txt",
    style="gb_t_7714"
)
```

## 数据源说明

### API 数据源

| 数据源 | 特点 | PDF支持 |
|--------|------|---------|
| arXiv | 预印本论文，访问快速 | ✅ |
| PubMed | 生物医学文献，权威可靠 | ❌ |
| CrossRef | DOI元数据最全 | ✅ |
| Semantic Scholar | AI驱动，引用分析强大 | ✅ |

### 浏览器自动化数据源

| 数据源 | 特点 | PDF支持 | 说明 |
|--------|------|---------|------|
| 知网(CNKI) | 中文学术文献最全 | ✅ | 需要浏览器自动化 |
| 万方 | 中文学位论文丰富 | ✅ | 需要浏览器自动化 |
| 维普 | 中文期刊文献 | ❌ | 需要浏览器自动化 |
| 百度学术 | 中文文献搜索 | ❌ | 需要浏览器自动化 |
| Bing Academic | 国际文献搜索 | ❌ | 需要浏览器自动化 |

## 引用格式

支持6种标准引用格式：

1. **APA** - 美国心理学会格式
2. **MLA** - 现代语言协会格式
3. **Chicago** - 芝加哥格式
4. **GB/T 7714** - 中国国家标准格式
5. **BibTeX** - LaTeX 引用格式
6. **Simple** - 简单格式

## 技术特点

- **异步并发**：使用 asyncio 提高访问效率
- **类型安全**：完整的类型提示支持
- **错误处理**：完善的异常处理机制
- **进度显示**：使用 tqdm 显示进度条

## 开发

```bash
# 安装开发依赖
pip install -e ".[dev]"

# 运行测试
python test_zhuai.py

# 代码格式化
black . && isort .

# 类型检查
mypy zhuai
```

## 许可证

GPL v3 License

## 联系方式

- GitHub: https://github.com/cycleuser/Zhuai
- Author: CycleUser

---

**Zhuai（拽）** - 让学术文献搜索和获取更简单！