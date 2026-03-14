#!/usr/bin/env python3
"""Test script for Zhuai paper sources.

Usage:
    python test_sources.py                    # Test all sources
    python test_sources.py arxiv crossref     # Test specific sources
"""

import asyncio
import sys
from typing import List

from zhuai import PaperSearcher
from zhuai.sources import ALL_SOURCES


async def test_source(source_name: str, query: str = "summation effect") -> None:
    """Test a single source."""
    if source_name not in ALL_SOURCES:
        print(f"Unknown source: {source_name}")
        return
    
    print(f"\n{'='*60}")
    print(f"Testing: {source_name}")
    print(f"{'='*60}")
    
    try:
        searcher = PaperSearcher(sources=[source_name], timeout=30)
        papers = await searcher.search(query, max_results=3, show_progress=False)
        
        print(f"Papers found: {len(papers)}")
        
        for i, paper in enumerate(papers, 1):
            pdf_status = "PDF available" if paper.can_download else "No PDF"
            print(f"  {i}. [{pdf_status}] {paper.title[:60]}...")
        
        await searcher.close()
        print(f"✓ {source_name} works correctly")
        
    except asyncio.TimeoutError:
        print(f"✗ {source_name} timed out (network issue)")
    except Exception as e:
        print(f"✗ {source_name} error: {e}")


async def test_browser_source(source_name: str, query: str = "定和效应") -> None:
    """Test a browser-based source."""
    from zhuai.sources.browser_base import BrowserSource
    
    if source_name not in ALL_SOURCES:
        print(f"Unknown source: {source_name}")
        return
    
    print(f"\n{'='*60}")
    print(f"Testing browser source: {source_name}")
    print(f"{'='*60}")
    
    try:
        source_class = ALL_SOURCES[source_name]
        source = source_class(timeout=60, headless=True)
        
        papers = await source.search(query, max_results=3)
        
        print(f"Papers found: {len(papers)}")
        
        for i, paper in enumerate(papers, 1):
            pdf_status = "PDF available" if paper.can_download else "No PDF"
            print(f"  {i}. [{pdf_status}] {paper.title[:60]}...")
        
        await source.close()
        print(f"✓ {source_name} works correctly")
        
    except asyncio.TimeoutError:
        print(f"✗ {source_name} timed out (network issue)")
    except Exception as e:
        print(f"✗ {source_name} error: {str(e)[:100]}")


async def main(sources_to_test: List[str] = None) -> None:
    """Run all tests."""
    print("Zhuai Source Test Script")
    print("="*60)
    
    api_sources = ["arxiv", "pubmed", "crossref", "semanticscholar"]
    browser_sources = ["cnki", "wanfang", "vip", "baidu", "bing"]
    
    if sources_to_test:
        api_sources = [s for s in sources_to_test if s in api_sources]
        browser_sources = [s for s in sources_to_test if s in browser_sources]
    
    print("\n1. Testing API sources...")
    print("-"*60)
    
    for source_name in api_sources:
        await test_source(source_name)
    
    print("\n2. Testing browser sources (requires Playwright)...")
    print("-"*60)
    print("Note: These sources may require login for full access.")
    print("Use --cookies-path to provide cookies for authenticated access.")
    
    for source_name in browser_sources:
        await test_browser_source(source_name)
    
    print("\n" + "="*60)
    print("Test complete!")
    print("="*60)


if __name__ == "__main__":
    sources = sys.argv[1:] if len(sys.argv) > 1 else None
    asyncio.run(main(sources))