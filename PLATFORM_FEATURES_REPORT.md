# 平台资源搜索功能报告

**日期**: 2026-04-01  
**版本**: 3.0.0

---

## 新增功能

### 1. GitHub 集成

**搜索功能**：
```bash
zhuai search-platforms "transformer" -p github -l python --min-stars 100
```

**趋势查看**：
```bash
zhuai trending -p github -l python --since weekly
```

**README 提取**：
```bash
zhuai get-readme "microsoft/vscode" -p github -o readme.md
```

**详情查看**：
```bash
zhuai repo-info "huggingface/transformers" -p github
```

**支持的功能**：
- 按语言过滤
- 按星标数过滤
- 获取趋势仓库（日/周/月）
- 提取 README 内容
- 获取文件列表
- 获取 Releases
- 获取 Contributors
- 获取 Issues

---

### 2. Hugging Face 集成

**模型搜索**：
```bash
zhuai search-platforms "bert" -p huggingface -t model
```

**数据集搜索**：
```bash
zhuai search-platforms "image classification" -p huggingface -t dataset
```

**支持的功能**：
- 搜索模型和数据集
- 按 Task 过滤（text-generation, image-classification 等）
- 按 Library 过滤（pytorch, tensorflow 等）
- 获取模型文件列表
- 提取 Model Card
- 获取下载量、点赞数

---

### 3. HF Mirror 集成

**用途**：国内访问 Hugging Face 加速

```bash
zhuai search-platforms "llama" -p hfmirror
```

---

### 4. Kaggle 集成

**数据集搜索**：
```bash
zhuai search-platforms "image classification" -p kaggle -t dataset
```

**支持的功能**：
- 搜索数据集
- 搜索模型
- 获取数据集文件列表

**注意**：需要 Kaggle API 凭证才能完整使用

---

### 5. ModelScope 集成

**模型搜索**：
```bash
zhuai search-platforms "qwen" -p modelscope
```

**支持的功能**：
- 搜索模型和数据集
- 按 Task 过滤
- 获取模型文件列表
- 提取 README

---

## CLI 命令详解

### search-platforms

搜索代码仓库、模型和数据集。

```bash
zhuai search-platforms <query> [options]

Options:
  -p, --platform      平台选择 (github/huggingface/hfmirror/kaggle/modelscope)
  -t, --type          资源类型 (code/model/dataset/all)
  -l, --language      编程语言过滤
  --min-stars         最小星标数
  -n, --max-results   最大结果数 (默认: 30)
  -o, --output        输出文件 (CSV/JSON)
```

**示例**：
```bash
# GitHub Python 项目
zhuai search-platforms "machine learning" -p github -l python -n 50

# Hugging Face 模型
zhuai search-platforms "text generation" -p huggingface -t model

# 导出结果
zhuai search-platforms "transformer" -p github -o results.csv
```

---

### trending

获取热门/趋势资源。

```bash
zhuai trending [options]

Options:
  -p, --platform      平台 (github/huggingface/modelscope)
  -l, --language      语言过滤
  --since             时间范围 (daily/weekly/monthly)
  -n, --max-results   最大结果数
```

**示例**：
```bash
# GitHub 今日热门 Python 项目
zhuai trending -p github -l python --since daily

# Hugging Face 热门模型
zhuai trending -p huggingface -n 50
```

---

### repo-info

获取仓库/模型的详细信息。

```bash
zhuai repo-info <repo_id> [options]

Options:
  -p, --platform      平台 (github/huggingface/kaggle/modelscope)
```

**示例**：
```bash
zhuai repo-info "microsoft/transformers" -p github
zhuai repo-info "bert-base-uncased" -p huggingface
zhuai repo-info "Qwen/Qwen-7B-Chat" -p modelscope
```

---

### get-readme

获取 README 内容。

```bash
zhuai get-readme <repo_id> [options]

Options:
  -p, --platform      平台 (github/huggingface/modelscope)
  -o, --output        输出文件
```

**示例**：
```bash
# 输出到文件
zhuai get-readme "huggingface/transformers" -p github -o readme.md

# 直接显示
zhuai get-readme "bert-base-uncased" -p huggingface
```

---

## Python API

### GitHub

```python
from zhuai.sources.github import GitHubSource

source = GitHubSource(token="your_github_token")  # token 可选

# 搜索仓库
repos = source.search("transformer", language="python", min_stars=100)

# 获取趋势
trending = source.get_trending(language="python", since="weekly")

# 获取 README
readme = source.get_readme("owner", "repo")

# 获取详情
repo = source.get_repo("owner", "repo")
```

### Hugging Face

```python
from zhuai.sources.huggingface import HuggingFaceSource

source = HuggingFaceSource()

# 搜索模型
models = source.search_models("bert", task="text-generation")

# 搜索数据集
datasets = source.search_datasets("image classification")

# 获取 README
readme = source.get_readme("bert-base-uncased")
```

### ModelScope

```python
from zhuai.sources.modelscope import ModelScopeSource

source = ModelScopeSource()

# 搜索模型
models = source.search_models("qwen", task="text-generation")
```

---

## 新增文件

| 文件 | 说明 |
|------|------|
| `zhuai/models/resource.py` | CodeResource, TrendingItem 数据模型 |
| `zhuai/sources/github.py` | GitHub 数据源 |
| `zhuai/sources/huggingface.py` | Hugging Face 数据源 |
| `zhuai/sources/kaggle.py` | Kaggle 数据源 |
| `zhuai/sources/modelscope.py` | ModelScope 数据源 |

---

## 数据模型

### CodeResource

```python
@dataclass
class CodeResource:
    name: str                    # 资源名称
    full_name: str              # 完整名称 (owner/repo)
    description: str            # 描述
    author: str                 # 作者
    platform: str               # 平台
    resource_type: str          # 类型 (code/model/dataset)
    url: str                    # URL
    stars: int                  # 星标数
    forks: int                  # Fork 数
    downloads: int              # 下载数
    likes: int                  # 点赞数
    language: str               # 编程语言
    topics: List[str]           # 标签
    license: str                # 许可证
    created_at: datetime        # 创建时间
    updated_at: datetime        # 更新时间
    readme: str                 # README 内容
```

---

## 支持的平台功能对比

| 功能 | GitHub | HuggingFace | Kaggle | ModelScope |
|------|--------|-------------|--------|------------|
| 搜索 | ✅ | ✅ | ✅ | ✅ |
| 趋势 | ✅ | ✅ | ❌ | ✅ |
| README | ✅ | ✅ | ❌ | ✅ |
| 文件列表 | ✅ | ✅ | ✅ | ✅ |
| Releases | ✅ | ❌ | ❌ | ❌ |
| Contributors | ✅ | ❌ | ❌ | ❌ |
| 按语言过滤 | ✅ | ✅ | ❌ | ❌ |

---

*报告生成时间: 2026-04-01*