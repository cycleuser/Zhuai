#!/usr/bin/env python3
"""
Complete test for all data sources with Chinese and English keywords.

Tests all 9 data sources:
- International: arXiv, PubMed, CrossRef, Semantic Scholar, Bing Academic
- Chinese: CNKI, Wanfang, VIP, Baidu Academic
"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from zhuai import PaperSearcher


def test_source(source_name: str, keyword: str, max_results: int = 10):
    """Test a single data source."""
    print(f"\n{'='*80}")
    print(f"测试数据源: {source_name}")
    print(f"关键词: {keyword}")
    print("="*80)
    
    try:
        searcher = PaperSearcher(
            sources=[source_name],
            download_dir=f"./downloads/{source_name}"
        )
        
        # Search
        papers = searcher.search_sync(keyword, max_results=max_results, show_progress=False)
        print(f"✓ 找到 {len(papers)} 篇文献")
        
        if not papers:
            return (source_name, 0, 0)
        
        # Show first 3 papers
        for i, paper in enumerate(papers[:3], 1):
            print(f"\n{i}. {paper.title[:80]}...")
            print(f"   作者: {', '.join(paper.authors[:3])}")
            if paper.year:
                print(f"   年份: {paper.year}")
            if paper.journal:
                print(f"   期刊: {paper.journal[:50]}...")
            print(f"   来源: {paper.source}")
        
        # Download
        download_results = searcher.download_papers_sync(papers, show_progress=False)
        downloaded = sum(1 for r in download_results.values() if r[0])
        print(f"\n✓ 下载 {downloaded} 个PDF")
        
        # Export
        output_dir = f"./output/{source_name}"
        searcher.export_papers_with_citations(papers, download_results, output_dir)
        
        return (source_name, len(papers), downloaded)
        
    except Exception as e:
        print(f"✗ 错误: {e}")
        import traceback
        traceback.print_exc()
        return (source_name, 0, 0)


def main():
    """Run complete test for all sources."""
    print("\n" + "="*80)
    print("ZHUAI - 完整数据源测试")
    print("测试所有9个数据源")
    print("="*80)
    
    # Test configuration
    tests = [
        # International sources with English keyword
        ("arxiv", "summation effect"),
        ("pubmed", "summation effect"),
        ("crossref", "summation effect"),
        ("semanticscholar", "summation effect"),
        ("bing", "summation effect"),
        
        # Chinese sources with Chinese keyword
        ("cnki", "深度学习"),
        ("wanfang", "深度学习"),
        ("vip", "深度学习"),
        ("baidu", "深度学习"),
    ]
    
    results = []
    
    for source_name, keyword in tests:
        result = test_source(source_name, keyword, max_results=10)
        results.append(result)
    
    # Summary
    print("\n" + "="*80)
    print("测试总结")
    print("="*80)
    
    total_papers = 0
    total_downloads = 0
    
    print("\n数据源测试结果:")
    print(f"{'数据源':<20} {'搜索结果':<10} {'下载PDF':<10} {'状态':<10}")
    print("-" * 50)
    
    for source_name, papers_count, downloaded_count in results:
        total_papers += papers_count
        total_downloads += downloaded_count
        status = "✓ 正常" if papers_count > 0 else "✗ 失败"
        print(f"{source_name:<20} {papers_count:<10} {downloaded_count:<10} {status:<10}")
    
    print("-" * 50)
    print(f"{'总计':<20} {total_papers:<10} {total_downloads:<10}")
    
    print(f"\n总计:")
    print(f"  搜索文献: {total_papers} 篇")
    print(f"  下载PDF: {total_downloads} 个")
    
    print(f"\n输出文件:")
    print(f"  - output/*/available_papers.csv - 已下载文献")
    print(f"  - output/*/available_papers.html - 已下载文献HTML")
    print(f"  - output/*/unavailable_papers.csv - 未下载文献")
    print(f"  - output/*/unavailable_papers.html - 未下载文献HTML")
    print(f"  - downloads/*/ - PDF文件")
    
    print("\n" + "="*80)
    print("✓ 测试完成")
    print("="*80)


if __name__ == "__main__":
    main()