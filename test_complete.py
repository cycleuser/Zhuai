#!/usr/bin/env python3
"""
Complete test suite for Zhuai using specified keywords.

Tests all data sources with:
- 定和效应 (summation effect) - Chinese keyword
- 高维度空间距离 - Chinese keyword  
- summation effect - English keyword
- high dimensional space distance - English keyword

Downloads all available PDFs and generates citations for unavailable papers.
"""

import sys
import os
from pathlib import Path
from datetime import datetime

sys.path.insert(0, str(Path(__file__).parent.parent))

from zhuai import PaperSearcher, CitationFormatter


def test_keyword(searcher, keyword, sources, max_results=50, download=True):
    """Test a specific keyword from given sources.
    
    Args:
        searcher: PaperSearcher instance
        keyword: Search keyword
        sources: List of source names
        max_results: Maximum results per source
        download: Whether to download PDFs
    
    Returns:
        Tuple of (papers, download_results)
    """
    print("\n" + "="*80)
    print(f"Testing keyword: '{keyword}'")
    print(f"Sources: {', '.join(sources)}")
    print("="*80)
    
    # Create a temporary searcher with specified sources
    test_searcher = PaperSearcher(
        sources=sources,
        download_dir=f"./downloads/{keyword.replace(' ', '_')}"
    )
    
    # Search papers
    print(f"\nSearching for: {keyword}")
    papers = test_searcher.search_sync(
        keyword,
        max_results=max_results,
        show_progress=True
    )
    
    print(f"\n✓ Found {len(papers)} papers")
    
    if not papers:
        return [], {}
    
    # Show first 10 papers
    print("\nFirst 10 papers:")
    for i, paper in enumerate(papers[:10], 1):
        print(f"\n{i}. {paper.title}")
        print(f"   Authors: {', '.join(paper.authors[:3])}")
        if paper.journal:
            print(f"   Journal: {paper.journal}")
        if paper.year:
            print(f"   Year: {paper.year}")
        print(f"   Source: {paper.source}")
        print(f"   PDF Available: {'Yes' if paper.can_download else 'No'}")
        if paper.doi:
            print(f"   DOI: {paper.doi}")
    
    # Get statistics
    stats = test_searcher.get_statistics(papers)
    print(f"\nStatistics:")
    print(f"  Total papers: {stats['total_papers']}")
    print(f"  With PDF: {stats['papers_with_pdf']}")
    print(f"  Without PDF: {stats['papers_without_pdf']}")
    
    # Download PDFs
    download_results = {}
    if download and stats['papers_with_pdf'] > 0:
        print(f"\nDownloading PDFs...")
        download_results = test_searcher.download_papers_sync(papers, show_progress=True)
        
        successful = sum(1 for r in download_results.values() if r[0])
        print(f"\n✓ Successfully downloaded {successful} PDFs")
        
        if successful > 0:
            print("\nDownloaded files:")
            for title, (success, filepath) in download_results.items():
                if success and filepath:
                    print(f"  ✓ {Path(filepath).name}")
    
    # Export results
    output_dir = Path(f"./test_output/{keyword.replace(' ', '_')}")
    output_dir.mkdir(parents=True, exist_ok=True)
    
    csv_file = output_dir / "results.csv"
    test_searcher.export_to_csv(papers, str(csv_file))
    print(f"\n✓ Exported results to: {csv_file}")
    
    # Export citations for unavailable papers
    if stats['papers_without_pdf'] > 0:
        # Chinese papers use GB/T 7714, English papers use APA
        is_chinese = any('\u4e00' <= c <= '\u9fff' for c in keyword)
        style = "gb_t_7714" if is_chinese else "apa"
        
        citation_file = output_dir / "unavailable_citations.txt"
        test_searcher.export_unavailable_citations(papers, str(citation_file), style=style)
        print(f"✓ Exported citations for {stats['papers_without_pdf']} unavailable papers to: {citation_file}")
    
    return papers, download_results


def main():
    """Run complete test suite."""
    print("\n" + "="*80)
    print("ZHUAI - COMPLETE TEST SUITE")
    print(f"Date: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("="*80)
    
    print("\nTest Keywords:")
    print("  1. 定和效应 (Chinese) - summation effect")
    print("  2. 高维度空间距离 (Chinese) - high dimensional space distance")
    print("  3. summation effect (English)")
    print("  4. high dimensional space distance (English)")
    
    print("\nData Sources to Test:")
    print("  International: arXiv, PubMed, CrossRef, Semantic Scholar, Bing Academic")
    print("  Chinese: CNKI, Wanfang, VIP, Baidu Academic")
    
    all_results = {}
    
    try:
        # Initialize searcher
        print("\n" + "="*80)
        print("Initializing Zhuai...")
        print("="*80)
        
        searcher = PaperSearcher()
        
        # Test 1: 定和效应 - Chinese sources
        print("\n" + "="*80)
        print("TEST 1: 定和效应 from Chinese sources")
        print("="*80)
        
        chinese_sources = ["cnki", "wanfang", "vip", "baidu"]
        papers1, downloads1 = test_keyword(
            searcher,
            "定和效应",
            chinese_sources,
            max_results=30
        )
        all_results["定和效应"] = {"papers": papers1, "downloads": downloads1}
        
        # Test 2: 高维度空间距离 - All sources
        print("\n" + "="*80)
        print("TEST 2: 高维度空间距离 from all sources")
        print("="*80)
        
        all_sources = list(PaperSearcher.list_all_sources())
        papers2, downloads2 = test_keyword(
            searcher,
            "高维度空间距离",
            all_sources,
            max_results=50
        )
        all_results["高维度空间距离"] = {"papers": papers2, "downloads": downloads2}
        
        # Test 3: summation effect - International sources
        print("\n" + "="*80)
        print("TEST 3: summation effect from international sources")
        print("="*80)
        
        international_sources = ["arxiv", "pubmed", "crossref", "semanticscholar", "bing"]
        papers3, downloads3 = test_keyword(
            searcher,
            "summation effect",
            international_sources,
            max_results=50
        )
        all_results["summation effect"] = {"papers": papers3, "downloads": downloads3}
        
        # Test 4: high dimensional space distance - All sources
        print("\n" + "="*80)
        print("TEST 4: high dimensional space distance from all sources")
        print("="*80)
        
        papers4, downloads4 = test_keyword(
            searcher,
            "high dimensional space distance",
            all_sources,
            max_results=50
        )
        all_results["high dimensional space distance"] = {"papers": papers4, "downloads": downloads4}
        
        # Summary
        print("\n" + "="*80)
        print("TEST SUMMARY")
        print("="*80)
        
        total_papers = sum(len(r["papers"]) for r in all_results.values())
        total_downloads = sum(
            sum(1 for d in r["downloads"].values() if d[0])
            for r in all_results.values()
        )
        
        print(f"\nTotal papers found: {total_papers}")
        print(f"Total PDFs downloaded: {total_downloads}")
        
        print("\nResults by keyword:")
        for keyword, result in all_results.items():
            papers_count = len(result["papers"])
            downloads_count = sum(1 for d in result["downloads"].values() if d[0])
            print(f"  {keyword}: {papers_count} papers, {downloads_count} PDFs")
        
        print("\nOutput files:")
        print("  - ./downloads/ : Downloaded PDF files")
        print("  - ./test_output/*/results.csv : Search results")
        print("  - ./test_output/*/unavailable_citations.txt : Citations for unavailable papers")
        
        print("\n" + "="*80)
        print("✓ ALL TESTS COMPLETED SUCCESSFULLY")
        print("="*80)
        
    except Exception as e:
        print(f"\n✗ Error during testing: {e}")
        import traceback
        traceback.print_exc()
        return 1
    
    return 0


if __name__ == "__main__":
    sys.exit(main())