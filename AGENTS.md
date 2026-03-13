# AGENTS.md

This document provides guidelines for AI coding agents working in this codebase.

## Project Overview

**Zhuai (拽)** is a Python package for searching and downloading academic papers from multiple sources (arXiv, PubMed, CrossRef, Semantic Scholar). The project supports both Chinese and English keywords, async and synchronous operations, and generates standard citation formats for unavailable papers.

- **Project Name**: Zhuai (拽)
- **Package Name**: zhuai
- **GitHub**: https://github.com/cycleuser/Zhuai
- **Python Versions**: 3.8, 3.9, 3.10, 3.11, 3.12

## Build/Lint/Test Commands

### Installation
```bash
pip install -e .                    # Install package in development mode
pip install -e ".[dev]"             # Install with dev dependencies
```

### Testing
```bash
pytest                              # Run all tests
pytest -v                           # Verbose output
pytest --cov=zhuai                  # Run with coverage
python test_zhuai.py                # Run comprehensive test suite
python example.py                   # Run quick start example
```

### Linting and Formatting
```bash
black .                             # Format code with black
black --check .                     # Check formatting without changes
isort .                             # Sort imports
isort --check .                     # Check import sorting
flake8 .                            # Lint with flake8
mypy zhuai                          # Type check with mypy
```

### Build
```bash
pip install build
python -m build                     # Build package
```

## Code Style Guidelines

### Line Length and Formatting
- Maximum line length: **100 characters**
- Use black formatter (configured in pyproject.toml)
- Python versions supported: 3.8, 3.9, 3.10, 3.11, 3.12

### Imports
Import order (enforced by isort with black profile):
1. Standard library imports
2. Third-party imports
3. Local imports

Separate each group with a blank line.

```python
# Standard library
import asyncio
import os
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple, Type

# Third-party
import aiohttp
from tqdm import tqdm

# Local
from zhuai.models.paper import Paper
from zhuai.sources.base import BaseSource
```

### Type Hints
- Type hints are **required** for all function signatures (mypy strict mode)
- Use typing module types: `List`, `Dict`, `Optional`, `Any`, `Tuple`, `Type`
- Always specify return types, including `-> None` for functions returning nothing

```python
# Correct
def search(self, query: str, max_results: int = 100) -> List[Paper]:
    ...

async def get_paper_by_id(self, paper_id: str) -> Optional[Paper]:
    ...

# Dataclass with type hints
@dataclass
class Paper:
    title: str
    authors: List[str]
    abstract: Optional[str] = None
    citations: int = 0
```

### Naming Conventions
- **Classes**: PascalCase (e.g., `PaperSearcher`, `BaseSource`, `ArxivSource`)
- **Functions/Methods**: snake_case (e.g., `search_sync`, `get_paper_by_id`)
- **Private methods**: Prefix with underscore (e.g., `_sanitize_filename`, `_deduplicate_papers`)
- **Constants**: UPPER_SNAKE_CASE (e.g., `ALL_SOURCES`, `DEFAULT_SOURCES`)
- **Module variables**: snake_case (e.g., `timeout`, `max_concurrent`)
- **Parameters**: snake_case

### Docstrings
Use triple double quotes for all docstrings. Include Args and Returns sections:

```python
def search(
    self,
    query: str,
    max_results: int = 100,
    **kwargs,
) -> List[Paper]:
    """Search for papers.
    
    Args:
        query: Search query.
        max_results: Maximum number of results.
        **kwargs: Additional source-specific parameters.
        
    Returns:
        List of papers.
    """
    pass
```

### Error Handling
- Use try/except with specific exception types
- Implement retry logic for network operations
- Log or print errors, don't silently swallow them

```python
for source_name in sources_to_search:
    source = self.sources[source_name]
    try:
        papers = await source.search(query, max_results=results_per_source)
        all_papers.extend(papers)
    except Exception as e:
        print(f"Error searching {source_name}: {e}")
    finally:
        if show_progress:
            pbar.update(1)
```

### Async Patterns
- Provide both async and sync versions of methods
- Use `asyncio.run()` for sync wrappers
- Use `asyncio.gather()` for concurrent operations

```python
async def search(self, query: str) -> List[Paper]:
    ...

def search_sync(self, query: str) -> List[Paper]:
    """Synchronous wrapper for search."""
    return asyncio.run(self.search(query))
```

### Data Classes
Use `@dataclass` for data models:

```python
from dataclasses import dataclass, field
from typing import List, Optional

@dataclass
class FilterCriteria:
    journals: Optional[List[str]] = None
    from_year: Optional[int] = None
    keywords: List[str] = field(default_factory=list)
```

### Properties
Use `@property` for computed attributes:

```python
@property
def name(self) -> str:
    """Get source name."""
    return "arXiv"

@property
def can_download(self) -> bool:
    """Check if PDF can be downloaded."""
    return self.pdf_url is not None
```

## Testing Guidelines

### Test Structure
```python
class TestClassName:
    """Tests for ClassName."""
    
    def test_method_name(self):
        """Test description."""
        ...
```

### Test Organization
- Place tests in `tests/` directory
- Name test files `test_*.py`
- Name test classes `Test*`
- Name test methods `test_*`

### Test Patterns
```python
import pytest
from paper_search_downloader import PaperSearcher, Paper, FilterCriteria

class TestFilterCriteria:
    def test_matches_journal(self):
        paper = Paper(title="Test", authors=["Author"])
        filters = FilterCriteria(journals=["Nature"])
        assert filters.matches(paper) is False
```

## Project Structure

```
Zhuai/
├── zhuai/                      # Main package
│   ├── __init__.py             # Public API exports
│   ├── cli.py                  # Command-line interface
│   ├── core/
│   │   ├── __init__.py
│   │   ├── searcher.py         # Main PaperSearcher class
│   │   ├── downloader.py       # Download management
│   │   ├── citation.py         # Citation formatting
│   │   └── validator.py        # PDF validation
│   ├── models/
│   │   ├── __init__.py
│   │   └── paper.py            # Paper dataclass
│   ├── sources/
│   │   ├── __init__.py         # ALL_SOURCES registry
│   │   ├── base.py             # BaseSource ABC
│   │   ├── arxiv.py            # ArxivSource
│   │   ├── pubmed.py           # PubMedSource
│   │   ├── crossref.py         # CrossRefSource
│   │   └── semanticscholar.py  # SemanticScholarSource
│   └── utils/
│       └── __init__.py
├── test_zhuai.py               # Comprehensive test suite
├── example.py                  # Quick start example
├── pyproject.toml              # Package configuration
├── requirements.txt            # Dependencies
├── requirements-dev.txt        # Development dependencies
├── README.md                   # Project documentation
└── LICENSE                     # GPL v3 License
```

## Key Features

1. **Multi-source Search**: arXiv, PubMed, CrossRef, Semantic Scholar
2. **Bilingual Support**: Chinese and English keywords
3. **PDF Download**: Automatic download of available PDFs
4. **Citation Generation**: Standard formats (APA, MLA, Chicago, GB/T 7714, BibTeX)
5. **CSV Export**: Export search results with full metadata
6. **Async/Sync**: Both async and synchronous API methods

## Key Patterns

### Adding a New Source
1. Create new file in `zhuai/sources/`
2. Inherit from `BaseSource`
3. Implement `name`, `supports_pdf`, `search()`, `get_paper_by_id()`
4. Register in `zhuai/sources/__init__.py` in `ALL_SOURCES` dict
5. Add tests in `test_zhuai.py`

### Citation Formats
The `CitationFormatter` class supports multiple formats:
- `apa`: APA style
- `mla`: MLA style
- `chicago`: Chicago style
- `gb_t_7714`: Chinese national standard GB/T 7714-2015
- `bibtex`: BibTeX format
- `simple`: Simple format

### Sync/Async Pattern
Every async method should have a sync wrapper:

```python
async def search(self, query: str) -> List[Paper]:
    ...

def search_sync(self, query: str) -> List[Paper]:
    """Synchronous wrapper for search."""
    return asyncio.run(self.search(query))
```

## Pre-Commit Checklist
Before committing, run:
```bash
black . && isort . && flake8 . && mypy zhuai
```

## Usage Examples

### Command Line
```bash
# Search papers
zhuai search "summation effect" --max-results 50

# Search and download
zhuai search "定和效应" --download --output results.csv

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
results = searcher.download_papers_sync(papers)

# Export results
searcher.export_to_csv(papers, "results.csv")

# Export citations for unavailable papers
searcher.export_unavailable_citations(papers, "citations.txt", style="apa")
```