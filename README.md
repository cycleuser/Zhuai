# Zhuai (拽)

<div align="center">

[![Python](https://img.shields.io/badge/Python-3.8%2B-blue.svg)](https://www.python.org/)
[![License](https://img.shields.io/badge/License-GPL%20v3-green.svg)](LICENSE)
[![GitHub](https://img.shields.io/badge/GitHub-cycleuser%2FZhuai-blue.svg)](https://github.com/cycleuser/Zhuai)

**Zhuai** - A Simple Tool for Finding Academic Papers with Vision AI

[中文](README_CN.md) | [English](README_EN.md)

</div>

---

## What is this?

Zhuai is a simple tool that helps you search and download academic papers from various sources. It uses Vision AI to automatically handle CAPTCHAs and parse pages, making the entire process fully automated without any human intervention.

## Key Features

- **Fully Automated**: Vision AI handles CAPTCHAs and page parsing automatically
- **Multi-source Search**: arXiv, PubMed, CNKI, Wanfang, VIP, CrossRef, etc.
- **PDF Download**: Automatic PDF downloading with duplicate detection
- **Bilingual Citations**: APA + GB/T 7714 formats for Chinese and English
- **CSV/HTML Export**: Complete metadata with clickable links

## Supported Sources

**International (API-based, no CAPTCHA):**
- arXiv - Preprints
- PubMed - Biomedical literature
- CrossRef - DOI database
- Semantic Scholar - Academic search

**Chinese (Vision AI powered):**
- CNKI (知网) - with automatic CAPTCHA solving
- Wanfang Data (万方) - with automatic CAPTCHA solving
- VIP (维普) - with automatic CAPTCHA solving

## Installation

```bash
# Install the tool
pip install zhuai

# Install browser for Chinese sources
playwright install chromium

# Install Ollama for Vision AI (required for Chinese sources)
# macOS/Linux:
curl -fsSL https://ollama.com/install.sh | sh

# Download vision model
ollama pull gemma3:4b
```

Or install from source:

```bash
git clone https://github.com/cycleuser/Zhuai.git
cd Zhuai
pip install -e .
playwright install chromium
```

## Usage

### Basic Search

```bash
# International sources (fast, no CAPTCHA)
zhuai search "deep learning" -s arxiv -s pubmed --download

# Chinese sources (Vision AI handles CAPTCHA automatically)
zhuai search "定和效应" -s cnki --max-results 10

# Multiple sources
zhuai search "artificial intelligence" -s arxiv -s cnki -s pubmed
```

### Advanced Options

```bash
# Specify vision model
zhuai search "高维度空间距离" -s cnki --vision-model gemma3:4b

# Import browser cookies for login
zhuai search "定和效应" -s cnki --import-browser firefox

# Adjust number of results
zhuai search "machine learning" -s arxiv --max-results 50 --download

# List available sources
zhuai sources
```

### Python API

```python
from zhuai import PaperSearcher

# Create searcher with vision model
searcher = PaperSearcher(
    sources=["arxiv", "cnki", "pubmed"],
    vision_model="gemma3:4b"
)

# Search papers
papers = searcher.search_sync("summation effect", max_results=50)

# Download PDFs
results = searcher.download_papers_sync(papers)

# Save results
searcher.export_to_csv(papers, "results.csv")

# Export citations
searcher.export_unavailable_citations(papers, "citations.txt", style="apa")
```

## Vision AI Features

Zhuai uses local Ollama vision models to achieve full automation:

1. **Automatic CAPTCHA Detection**: Screenshots pages and analyzes for CAPTCHAs
2. **CAPTCHA Solving**:
   - Slider CAPTCHA: Calculates drag distance and simulates mouse movement
   - Click CAPTCHA: Identifies click positions
   - Text CAPTCHA: OCR recognition and input
3. **Page Parsing**: When CSS selectors fail, Vision AI extracts paper info from screenshots

### Supported Vision Models

- `gemma3:4b` (default, recommended)
- `gemma3:1b` (faster, less accurate)
- Any Ollama-compatible vision model

## Citation Formats

- **APA** - American Psychological Association
- **MLA** - Modern Language Association
- **Chicago** - Chicago Manual of Style
- **GB/T 7714** - Chinese National Standard
- **BibTeX** - LaTeX format

## Output

### CSV File
Contains: title, authors, year, journal, DOI, PDF URL, source, language

### Citation Files
For papers without PDF access:
- `unavailable.txt` - Text format citations
- `results.csv` - Complete metadata with citations

## Technical Details

- **Async Operations**: Concurrent searches for efficiency
- **Playwright Stealth**: Hides automation traces
- **Vision AI**: Ollama-based local vision models
- **Type Hints**: Complete type annotations

## Requirements

- Python 3.8+
- Ollama with vision model (for Chinese sources)
- Chromium browser (auto-installed by Playwright)

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

**Zhuai** - Simple, automated, no human intervention needed