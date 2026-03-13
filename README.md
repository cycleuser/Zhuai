# Zhuai (拽)

<div align="center">

[![Python](https://img.shields.io/badge/Python-3.8%2B-blue.svg)](https://www.python.org/)
[![License](https://img.shields.io/badge/License-GPL%20v3-green.svg)](LICENSE)
[![GitHub](https://img.shields.io/badge/GitHub-cycleuser%2FZhuai-blue.svg)](https://github.com/cycleuser/Zhuai)

**Zhuai** - A Simple Tool for Finding Academic Papers

[中文](README_CN.md) | [English](README_EN.md)

</div>

---

## What is this?

Zhuai is a simple tool that helps you search and download academic papers from various sources. Clean design, easy to use.

## What can it do?

- Search papers from multiple sources (arXiv, PubMed, CNKI, Wanfang, etc.)
- Automatically download PDF files
- Export search results to CSV
- Generate citation formats

## Supported Sources

**International:**
- arXiv - Preprints
- PubMed - Biomedical literature
- CrossRef - DOI database
- Semantic Scholar - Academic search
- Bing Academic - Microsoft Academic

**Chinese:**
- CNKI (知网)
- Wanfang Data (万方)
- VIP (维普)
- Baidu Academic (百度学术)

## Installation

```bash
# Install the tool
pip install zhuai

# For Chinese sources, also install the browser
playwright install chromium
```

Or install from source:

```bash
git clone https://github.com/cycleuser/Zhuai.git
cd Zhuai
pip install -e .
playwright install chromium
```

## Usage

### Command Line

```bash
# Search papers
zhuai search "deep learning"

# Search from specific sources
zhuai search "artificial intelligence" --sources arxiv semanticscholar

# Search and download
zhuai search "summation effect" --download

# List available sources
zhuai sources
```

### Python API

```python
from zhuai import PaperSearcher

# Create searcher
searcher = PaperSearcher()

# Search papers
papers = searcher.search_sync("summation effect", max_results=50)

# Download PDFs
searcher.download_papers_sync(papers)

# Save results
searcher.export_to_csv(papers, "results.csv")

# Export citations for unavailable papers
searcher.export_unavailable_citations(papers, "citations.txt")
```

### Choose Specific Sources

```python
# Use only Chinese sources
searcher = PaperSearcher(sources=["cnki", "wanfang", "baidu"])

# Use only API sources (faster)
searcher = PaperSearcher(sources=["arxiv", "pubmed", "semanticscholar"])

# Custom combination
searcher = PaperSearcher(sources=["arxiv", "cnki", "pubmed"])
```

## Citation Formats

Supports common citation formats:

- **APA** - American Psychological Association
- **MLA** - Modern Language Association
- **Chicago** - Chicago Manual of Style
- **GB/T 7714** - Chinese National Standard
- **BibTeX** - LaTeX format
- **Simple** - Simple format

## Output

### CSV File
Contains paper details: title, authors, year, journal, DOI, abstract, etc.

### Citation Files
For papers without PDF access, two files are generated:

1. **Text file** (unavailable_citations.txt): Simple text format
2. **CSV file** (unavailable_citations_with_citations.csv): Contains:
   - Paper basic info (title, authors, year, journal, etc.)
   - Download links and DOI
   - 5 international standard citation formats (APA, GB/T 7714, MLA, Chicago, BibTeX)

This CSV file includes bilingual standard citation formats for easy use.

## Technical Details

- Async concurrent operations for efficiency
- Browser automation for interactive websites
- Smart deduplication
- Complete type hints

## Development

```bash
# Install dev dependencies
pip install -e ".[dev]"

# Run tests
pytest

# Format code
black . && isort .
```

## License

GPL v3 License

## Questions?

- Issues: https://github.com/cycleuser/Zhuai/issues
- Code: https://github.com/cycleuser/Zhuai

---

**Zhuai** - Simple and easy, that's it