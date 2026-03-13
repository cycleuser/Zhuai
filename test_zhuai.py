#!/usr/bin/env python3
"""
Test script for Zhuai with new browser-based sources.

Tests searching from CNKI, Wanfang, VIP, Baidu Academic, and Bing Academic
using browser automation.
"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from zhuai import PaperSearcher


def test_chinese_sources():
    """Test searching Chinese academic sources."""
    print("\n" + "="*80)
    print("Testing Chinese Academic Sources")
    print("="*80)
    
    searcher = PaperSearcher(
        sources=["cnki", "wanfang", "baidu"],
        download_dir="./downloads"
    )
    
    print("\nSearching for '深度学习' from Chinese sources...")
    papers = searcher.search_sync(
        "深度学习",
        max_results=10,
        show_progress=True
    )
    
    print(f"\nFound {len(papers)} papers")
    
    if papers:
        print("\nFirst 5 papers:")
        for i, paper in enumerate(papers[:5], 1):
            print(f"\n{i}. {paper.title}")
            print(f"   Authors: {', '.join(paper.authors[:3])}")
            if paper.journal:
                print(f"   Journal: {paper.journal}")
            if paper.year:
                print(f"   Year: {paper.year}")
            print(f"   Source: {paper.source}")
    
    return papers


def test_api_sources():
    """Test searching API-based sources."""
    print("\n" + "="*80)
    print("Testing API-based Sources")
    print("="*80)
    
    searcher = PaperSearcher(
        sources=["arxiv", "semanticscholar", "crossref"]
    )
    
    print("\nSearching for 'summation effect'...")
    papers = searcher.search_sync(
        "summation effect",
        max_results=15,
        show_progress=True
    )
    
    print(f"\nFound {len(papers)} papers")
    
    if papers:
        print("\nFirst 5 papers:")
        for i, paper in enumerate(papers[:5], 1):
            print(f"\n{i}. {paper.title}")
            print(f"   Authors: {', '.join(paper.authors[:3])}")
            if paper.year:
                print(f"   Year: {paper.year}")
            print(f"   Source: {paper.source}")
    
    return papers


def test_all_sources():
    """Test searching from all sources."""
    print("\n" + "="*80)
    print("Testing All Sources")
    print("="*80)
    
    searcher = PaperSearcher()
    
    print("\nSearching from all available sources...")
    papers = searcher.search_sync(
        "人工智能",
        max_results=20,
        show_progress=True
    )
    
    print(f"\nFound {len(papers)} papers total")
    
    # Group by source
    from collections import defaultdict
    by_source = defaultdict(list)
    for paper in papers:
        if paper.source:
            by_source[paper.source].append(paper)
    
    print("\nPapers by source:")
    for source, source_papers in by_source.items():
        print(f"  {source}: {len(source_papers)} papers")
    
    return papers


def main():
    """Run all tests."""
    print("\n" + "="*80)
    print("ZHUAI - Extended Source Test Suite")
    print("="*80)
    
    try:
        # Test API sources
        api_papers = test_api_sources()
        
        # Test Chinese sources (requires browser)
        print("\n" + "="*80)
        print("Note: Chinese sources require browser automation.")
        print("Make sure you have run: playwright install chromium")
        print("="*80)
        
        try:
            chinese_papers = test_chinese_sources()
        except Exception as e:
            print(f"\nNote: Chinese sources test skipped: {e}")
            print("This is expected if browser automation is not set up.")
            chinese_papers = []
        
        # Test all sources
        all_papers = test_all_sources()
        
        print("\n" + "="*80)
        print("✓ TESTS COMPLETED")
        print("="*80)
        
        # Summary
        print(f"\nSummary:")
        print(f"  API sources: {len(api_papers)} papers")
        print(f"  Chinese sources: {len(chinese_papers)} papers")
        print(f"  All sources: {len(all_papers)} papers")
        
    except Exception as e:
        print(f"\nError during testing: {e}")
        import traceback
        traceback.print_exc()
        return 1
    
    return 0


if __name__ == "__main__":
    sys.exit(main())