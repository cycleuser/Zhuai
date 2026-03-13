#!/usr/bin/env python3
"""Complete test with improved export functionality.

Tests:
1. Search from all sources
2. Download PDFs (skip duplicates)
3. Export available papers with citations and file paths
4. Export unavailable papers with citations and download links
"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from zhuai import PaperSearcher


def main():
    """Run complete test."""
    print("="*80)
    print("ZHUAI - 完整测试")
    print("="*80)
    
    # Create searcher
    searcher = PaperSearcher(
        sources=["arxiv", "pubmed", "crossref", "semanticscholar"],
        download_dir="./downloads/test"
    )
    
    # Test keywords
    keywords = ["summation effect", "定和效应"]
    
    for keyword in keywords:
        print(f"\n{'='*80}")
        print(f"搜索关键词: {keyword}")
        print("="*80)
        
        # Search
        papers = searcher.search_sync(keyword, max_results=20, show_progress=True)
        print(f"\n找到 {len(papers)} 篇文献")
        
        if not papers:
            continue
        
        # Download
        print("\n下载PDF...")
        download_results = searcher.download_papers_sync(papers, show_progress=True)
        
        successful = sum(1 for r in download_results.values() if r[0])
        print(f"成功下载 {successful} 个PDF")
        
        # Export with citations
        output_dir = f"./output/{keyword.replace(' ', '_')}"
        print(f"\n导出引用和链接...")
        searcher.export_papers_with_citations(
            papers,
            download_results,
            output_dir
        )
        
        # Statistics
        stats = searcher.get_statistics(papers, download_results)
        print(f"\n统计信息:")
        print(f"  总文献数: {stats['total_papers']}")
        print(f"  已下载: {successful}")
        print(f"  未下载: {stats['papers_without_pdf'] + (stats.get('failed_downloads', 0))}")
    
    print("\n" + "="*80)
    print("✓ 测试完成")
    print("="*80)
    print("\n输出文件:")
    print("  - output/*/available_papers.csv - 已下载文献（含引用和本地文件路径）")
    print("  - output/*/available_papers.html - 已下载文献HTML格式")
    print("  - output/*/unavailable_papers.csv - 未下载文献（含引用和下载链接）")
    print("  - output/*/unavailable_papers.html - 未下载文献HTML格式")
    print("  - downloads/test/ - PDF文件")


if __name__ == "__main__":
    main()