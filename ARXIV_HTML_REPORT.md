# arXiv HTML/Markdown 下载功能报告

**日期**: 2026-04-01  
**版本**: 2.2.0

---

## 新增功能

### 1. arXiv HTML 版本检测

arXiv 为部分论文提供 HTML 版本（取决于作者上传的源文件格式）。新增功能：

- 自动检测论文是否有 HTML 版本
- 在搜索结果中显示 HTML 可用性
- `--has-html` 过滤选项

### 2. HTML 下载

```bash
zhuai search "transformer" -s arxiv --download --download-format html
```

### 3. Markdown 下载

自动将 HTML 转换为 Markdown 格式：

```bash
zhuai search "neural network" -s arxiv --download --download-format markdown
```

### 4. 多格式下载

一次性下载所有可用格式：

```bash
zhuai search "deep learning" -s arxiv --download --download-format all
```

---

## 技术实现

### 新增文件

| 文件 | 说明 |
|------|------|
| `zhuai/utils/html_converter.py` | HTML 到 Markdown 转换器 |
| `zhuai/sources/arxiv.py` (更新) | HTML 检测和下载支持 |
| `zhuai/models/paper.py` (更新) | 新增 `html_url`, `has_html` 字段 |
| `zhuai/core/downloader.py` (更新) | 支持多格式下载 |

### HTML 检测逻辑

```python
def _check_html_available(self, arxiv_id: str) -> bool:
    html_url = f"https://arxiv.org/html/{arxiv_id}"
    response = requests.get(html_url, timeout=10)
    
    # 检查是否有 "No HTML" 消息
    if "No HTML" in response.text or "HTML is not available" in response.text:
        return False
    
    # 检查内容长度（有效页面通常 > 15000 字符）
    if 'arXiv' in response.text and len(response.text) > 15000:
        return True
    
    return False
```

### Markdown 转换

HTML 到 Markdown 转换器支持：

- 标题转换（h1-h6 → # ## ###）
- 链接转换
- 粗体/斜体
- 代码块
- 数学公式保留
- 图片提取
- 表格转换

---

## CLI 参数更新

| 参数 | 说明 |
|------|------|
| `--download-format` | 下载格式 (pdf/html/markdown/all) |
| `--has-html` | 仅显示有 HTML 版本的论文 |

---

## 使用示例

### 检查 HTML 可用性

```python
from zhuai.sources.arxiv import ArxivSource

source = ArxivSource(check_html=True)
papers = source.search_sync("machine learning")

for paper in papers:
    if paper.has_html:
        print(f"✅ {paper.title}")
        print(f"   HTML: {paper.html_url}")
```

### 下载 Markdown

```python
from zhuai import PaperSearcher

searcher = PaperSearcher()
papers = searcher.search_sync("transformer", max_results=10)

# 下载 Markdown
results = searcher.download_papers_sync(papers, format="markdown")

for title, (success, path) in results.items():
    if success:
        print(f"✅ {title}: {path}")
```

---

## 注意事项

1. **HTML 可用性**：并非所有 arXiv 论文都有 HTML 版本
   - 只有作者上传了可转换的 LaTeX 源码的论文才有
   - 大约 30-50% 的论文有 HTML 版本

2. **Markdown 质量**：
   - 数学公式可能需要手动调整
   - 部分复杂排版可能转换不完美
   - 建议作为阅读参考，不建议直接引用

3. **下载速度**：
   - HTML 下载比 PDF 快（文件更小）
   - Markdown 转换需要额外处理时间

---

## 测试结果

```
Testing arXiv HTML availability:
  2301.07041: ❌ No HTML
  2401.00001: ✅ HTML available
  2312.00001: ❌ No HTML
  2309.00001: ❌ No HTML
  2208.00001: ❌ No HTML

HTML Download Test (2401.00001):
  Status: 200
  Content length: 183382 chars
  Markdown length: 133808 chars
  ✅ Successfully converted to Markdown
```

---

*报告生成时间: 2026-04-01*