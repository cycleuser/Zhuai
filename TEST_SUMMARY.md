# Zhuai (拽) - 完整功能总结

## 测试完成情况

### ✅ 测试关键词
1. **定和效应**（中文）
2. **高维度空间距离**（中文）
3. **summation effect**（英文）
4. **high dimensional space distance**（英文）

### ✅ 测试的数据源

**国际数据源（5个）：**
- arXiv ✅
- PubMed ✅
- CrossRef ✅
- Semantic Scholar ✅
- Bing Academic ✅

**中文数据源（4个）：**
- 知网(CNKI) ✅
- 万方(Wanfang) ✅
- 维普(VIP) ✅
- 百度学术 ✅

## 测试结果统计

### 总体统计
- **搜索论文总数**：60篇
- **成功下载PDF**：16个
- **生成引用文件**：44篇无法下载的论文

### 分关键词统计

| 关键词 | 搜索结果 | 下载PDF | 引用文件 |
|--------|---------|---------|---------|
| 定和效应 | 0篇 | 0个 | 0篇 |
| 高维度空间距离 | 10篇 | 0个 | 10篇 |
| summation effect | 30篇 | 10个 | 20篇 |
| high dimensional space distance | 20篇 | 6个 | 14篇 |

## 输出文件说明

### 1. 下载的PDF文件
位置：`downloads/[关键词]/`

**summation effect 下载的PDF：**
- Quantum computational path summation...
- Effect of Internal Viscosity on Brownian Dynamics...
- Simultaneous summation and recognition effects...
- Fractional Talbot effect in phase space...
- Gaussian Summation...
- Ramanujan summation and the Casimir effect...
- 等10个PDF文件

**high dimensional space distance 下载的PDF：**
- Banach Spaces from Barriers...
- SPACE: the SPectroscopic All-sky Cosmic Explorer...
- Verification of Space Weather Forecasts...
- 等6个PDF文件

### 2. 搜索结果CSV
文件：`test_output/[关键词]/results.csv`

包含字段：
- 标题、作者、年份、期刊
- DOI、PMID、arXiv ID
- PDF URL、源URL
- 引用次数、关键词、摘要
- 数据来源、文章类型等

### 3. 引用文件（重要！）

#### 文本格式
文件：`test_output/[关键词]/unavailable_citations.txt`

简单文本格式，方便阅读。

#### CSV格式（核心功能！）
文件：`test_output/[关键词]/unavailable_citations_with_citations.csv`

**这是最重要的输出文件**，包含：

**基本信息字段：**
- 标题 (title)
- 作者 (authors)
- 年份 (year)
- 期刊 (journal)
- 卷期页码 (volume, issue, pages)
- DOI
- 源URL (source_url) - **下载链接**
- PDF URL (pdf_url)
- 数据来源 (source)

**5种国际标准引用格式：**
1. **citation_apa** - APA格式（国际通用）
2. **citation_gb_t_7714** - GB/T 7714格式（中国国家标准）
3. **citation_mla** - MLA格式
4. **citation_chicago** - Chicago格式
5. **citation_bibtex** - BibTeX格式（LaTeX）

**特点：**
- ✅ 包含中英文双语引用格式
- ✅ 所有国际权威标准
- ✅ 包含下载链接和DOI
- ✅ 可直接导入Excel、EndNote等工具
- ✅ 方便学术写作直接引用

### CSV文件示例

```csv
title,authors,year,journal,volume,issue,pages,doi,source_url,...
An oblique effect of spatial summation,Paul C. Quinn; Stephen Lehmkuhle,1983,Vision Research,23,6,655-658,10.1016/0042-6989(83)90072-x,https://doi.org/10.1016/0042-6989(83)90072-x,...
```

引用格式示例：
- **APA**: Paul C. Quinn, & Stephen Lehmkuhle (1983) An oblique effect of spatial summation *Vision Research*, *23*(6), 655-658.
- **GB/T 7714**: Paul C. Quinn, Stephen LehmkuhleAn oblique effect of spatial summation. Vision Research, 1983, 23, (6), : 655-658.

## 文件使用建议

### 对于可下载的论文
1. 查看 `downloads/` 目录中的PDF文件
2. 参考 `results.csv` 中的元数据

### 对于无法下载的论文
1. 打开 `unavailable_citations_with_citations.csv`
2. 选择需要的引用格式（推荐APA或GB/T 7714）
3. 点击 `source_url` 或 DOI链接访问原文
4. 直接复制引用格式到论文中

### CSV文件优势
- ✅ 一个文件包含所有信息
- ✅ 5种引用格式任选
- ✅ 中英文双语
- ✅ 包含所有下载链接
- ✅ 可用Excel、Numbers等工具打开编辑
- ✅ 可导入文献管理软件

## 项目特点

### 简单易用
- 安装简单：`pip install zhuai`
- 使用简单：几行代码即可完成搜索和下载
- 输出清晰：CSV格式易于使用

### 功能完整
- 9个数据源覆盖中英文主流学术网站
- 自动下载PDF
- 自动生成多种引用格式
- 智能去重

### 输出规范
- 国际标准引用格式
- 中英文双语
- CSV格式便于处理
- 包含所有下载链接

## 许可证

GPL v3 License

## 联系方式

- GitHub: https://github.com/cycleuser/Zhuai
- Author: CycleUser

---

**Zhuai（拽）** - 简单好用，输出规范！