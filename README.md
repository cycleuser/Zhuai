# Zhuai (拽)

<div align="center">

[![Python](https://img.shields.io/badge/Python-3.8%2B-blue.svg)](https://www.python.org/)
[![License](https://img.shields.io/badge/License-GPL%20v3-green.svg)](LICENSE)
[![GitHub](https://img.shields.io/badge/GitHub-cycleuser%2FZhuai-blue.svg)](https://github.com/cycleuser/Zhuai)

**Zhuai** - Academic Paper Search, Download and Citation Tool

[中文](README_CN.md)

</div>

---

## Features

- **Multi-source Search**: arXiv, PubMed, CrossRef, Semantic Scholar, CNKI, Wanfang, VIP
- **Advanced Filtering**: Filter by author, title, journal, year, quartile, citations
- **Multi-format Download**: PDF, HTML, Markdown (for arXiv papers)
- **Citation Generation**: APA, MLA, Chicago, GB/T 7714, BibTeX formats
- **Web Interface**: Browser-based search with advanced filters
- **Journal Database**: 10,000+ journals with JCR/CAS partition info
- **Multiple Export Formats**: CSV, JSON, HTML

## Installation

```bash
pip install zhuai
```

Or install from source:

```bash
git clone https://github.com/cycleuser/Zhuai.git
cd Zhuai
pip install -e .
```

## Usage

### Command Line

```bash
# Basic search
zhuai search "deep learning" -s arxiv -s pubmed --download

# Download PDF (default)
zhuai search "transformer" -s arxiv --download

# Download HTML version (arXiv papers with HTML)
zhuai search "neural network" -s arxiv --download --download-format html

# Download Markdown version (converted from HTML)
zhuai search "machine learning" -s arxiv --download --download-format markdown

# Download all formats
zhuai search "deep learning" -s arxiv --download --download-format all

# Advanced filtering
zhuai search "machine learning" --author "Hinton" --year 2020-2024

# Filter by quartile
zhuai search "transformer" --quartile Q1 --min-citations 100

# Field-specific search
zhuai search "title:neural network author:LeCun"

# Web interface
zhuai web --port 5000
```

### Python API

```python
from zhuai import PaperSearcher

# Create searcher
searcher = PaperSearcher(sources=["arxiv", "pubmed", "crossref"])

# Search papers
papers = searcher.search_sync("deep learning", max_results=50)

# Download PDFs
results = searcher.download_papers_sync(papers, format="pdf")

# Download HTML versions
results = searcher.download_papers_sync(papers, format="html")

# Download Markdown versions
results = searcher.download_papers_sync(papers, format="markdown")

# Download all formats
results = searcher.download_papers_sync(papers, format="all")

# Export results
searcher.export_to_csv(papers, "results.csv")

# Generate citations
searcher.export_unavailable_citations(papers, "citations.txt", style="apa")
```

### Advanced Search with Filters

```python
from zhuai import PaperSearcher
from zhuai.core.query_parser import SearchFilter

searcher = PaperSearcher()

# Create filter
search_filter = SearchFilter(
    authors=["Hinton", "LeCun"],
    year_from=2020,
    year_to=2024,
    jcr_quartile="Q1",
    min_citations=100
)

# Search with filter
papers = searcher.search_advanced_sync(
    query="neural networks",
    search_filter=search_filter,
    max_results=50
)
```

## Supported Sources

| Source | Type | PDF |
|--------|------|-----|
| arXiv | API | ✅ |
| PubMed | API | ✅ |
| CrossRef | API | ✅ |
| Semantic Scholar | API | ✅ |
| CNKI | Browser | ✅ |
| Wanfang | Browser | ✅ |
| VIP | Browser | ✅ |

## CLI Commands

| Command | Description |
|---------|-------------|
| `zhuai search` | Search papers |
| `zhuai web` | Start web interface |
| `zhuai journals` | Search journals |
| `zhuai journal-info` | Get journal details |
| `zhuai sources` | List available sources |

## CLI Options

| Option | Description |
|--------|-------------|
| `-s, --sources` | Data sources to search |
| `-n, --max-results` | Maximum results |
| `-d, --download` | Download PDFs |
| `-a, --author` | Filter by author |
| `-j, --journal` | Filter by journal |
| `--year` | Filter by year (e.g., 2020-2024) |
| `-q, --quartile` | JCR quartile (Q1/Q2/Q3/Q4) |
| `--min-citations` | Minimum citations |
| `--has-pdf` | Only papers with PDF |
| `-f, --format` | Output format (csv/json/html/all) |

## Web Interface

Start the web server:

```bash
zhuai web
# Visit http://localhost:5000
```

Web features:
- Multi-source search
- Advanced filtering panel
- Batch download
- Multiple citation formats
- CSV/JSON export

## Citation Formats

- **APA** - American Psychological Association
- **MLA** - Modern Language Association
- **Chicago** - Chicago Manual of Style
- **GB/T 7714** - Chinese National Standard
- **BibTeX** - LaTeX format

## Journal Database

10,000+ journals with:
- ISSN, publisher, official URL
- JCR quartile, impact factor
- CAS partition (1区/2区/3区/4区)
- EI indexing status

```bash
# Search journals
zhuai journals "nature"

# Filter by quartile
zhuai journals "computer" --quartile Q1 --sci

# Get journal details
zhuai journal-info 0028-0836
```

## Requirements

- Python 3.8+
- Chromium browser (auto-installed by Playwright for some sources)

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

## Links

- Issues: https://github.com/cycleuser/Zhuai/issues
- Code: https://github.com/cycleuser/Zhuai

---

**Zhuai** - Simple and powerful academic paper search tool