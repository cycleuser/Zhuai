# Zhuai 开发状态

## ✅ 已完成所有功能

### 核心功能

1. **多数据源搜索**
   - ✅ arXiv - HTTP API，支持 HTML/Markdown 下载
   - ✅ PubMed - API + PMC 开放获取
   - ✅ CrossRef - Unpaywall 开放获取 PDF
   - ✅ Semantic Scholar - 学术搜索
   - ✅ CNKI - 浏览器访问
   - ✅ Wanfang - 浏览器访问
   - ✅ VIP - 浏览器访问

2. **平台资源搜索** ✨ NEW
   - ✅ GitHub - 代码仓库搜索、趋势、README 提取
   - ✅ Hugging Face - 模型和数据集搜索
   - ✅ HF Mirror - Hugging Face 镜像（国内加速）
   - ✅ Kaggle - 数据集和模型搜索
   - ✅ ModelScope - 阿里模型平台

3. **高级搜索功能**
   - ✅ 字段限定搜索 (`title:`, `author:`, `journal:`, `year:`)
   - ✅ 作者过滤 (`--author`)
   - ✅ 期刊过滤 (`--journal`)
   - ✅ 年份范围过滤 (`--year 2020-2024`)
   - ✅ JCR 分区过滤 (`--quartile Q1`)
   - ✅ 最小引用数过滤 (`--min-citations`)

4. **多格式下载**
   - ✅ PDF 下载（默认）
   - ✅ HTML 下载（arXiv 论文）
   - ✅ Markdown 下载（从 HTML 转换）

5. **Web 界面**
   - ✅ 响应式搜索界面
   - ✅ 批量下载
   - ✅ 引用格式生成

6. **期刊数据库**
   - ✅ 10,104 个期刊

### 使用示例

```bash
# 论文搜索
zhuai search "deep learning" -s arxiv --download

# 平台资源搜索
zhuai search-platforms "transformer" -p github -l python
zhuai search-platforms "bert" -p huggingface -t model
zhuai search-platforms "image dataset" -p kaggle

# 趋势查看
zhuai trending -p github -l python
zhuai trending -p huggingface

# 详情查看
zhuai repo-info "microsoft/transformers" -p github
zhuai get-readme "bert-base-uncased" -p huggingface

# Web 界面
zhuai web
```

### CLI 命令

| 命令 | 说明 |
|------|------|
| `search` | 搜索论文 |
| `search-platforms` | 搜索平台资源 |
| `trending` | 获取趋势资源 |
| `repo-info` | 获取详情 |
| `get-readme` | 获取 README |
| `journals` | 搜索期刊 |
| `web` | 启动 Web |

---

**状态：开发完成** ✅
