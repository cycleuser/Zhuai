#!/usr/bin/env python3
"""
验证每个数据源至少能下载一篇文章。

策略：
1. arXiv - 所有文章都可以免费下载
2. CrossRef - 搜索开放获取文章
3. PubMed - 通过PMC开放获取文章
4. Semantic Scholar - 开放获取文章
5. Bing Academic - 搜索开放获取文章
6. CNKI - 搜索开放获取文章
7. Wanfang - 搜索开放获取文章  
8. VIP - 搜索开放获取文章
9. Baidu Academic - 搜索开放获取文章
"""

import sys
from pathlib import Path
import time

sys.path.insert(0, str(Path(__file__).parent.parent))

from zhuai import PaperSearcher


def test_source_download(source_name: str, keyword: str, max_results: int = 20):
    """测试单个数据源是否能下载文章。
    
    Args:
        source_name: 数据源名称
        keyword: 搜索关键词
        max_results: 最大结果数
        
    Returns:
        Tuple of (source_name, success, papers_count, downloaded_count, paper_title)
    """
    print(f"\n{'='*80}")
    print(f"测试数据源: {source_name}")
    print(f"关键词: {keyword}")
    print("="*80)
    
    try:
        searcher = PaperSearcher(
            sources=[source_name],
            download_dir=f"./downloads/verify_{source_name}"
        )
        
        # 搜索
        papers = searcher.search_sync(keyword, max_results=max_results, show_progress=False)
        print(f"✓ 找到 {len(papers)} 篇文献")
        
        if not papers:
            return (source_name, False, 0, 0, "无搜索结果")
        
        # 显示有PDF的文章
        with_pdf = [p for p in papers if p.can_download]
        print(f"  其中有PDF: {len(with_pdf)} 篇")
        
        if not with_pdf:
            print("  所有文章都无PDF，尝试下载链接...")
            # 尝试前5篇
            test_papers = papers[:5]
        else:
            # 只尝试有PDF的文章
            test_papers = with_pdf[:5]
        
        # 下载测试
        print(f"\n尝试下载前 {len(test_papers)} 篇文章...")
        download_results = searcher.download_papers_sync(test_papers, show_progress=False)
        
        # 检查结果
        successful = []
        for title, (success, filepath) in download_results.items():
            if success:
                successful.append((title, filepath))
                print(f"✓ 成功: {title[:60]}...")
                print(f"  文件: {filepath}")
        
        if successful:
            # 导出验证
            output_dir = f"./output/verify_{source_name}"
            searcher.export_papers_with_citations(papers, download_results, output_dir)
            
            # 检查生成的文件
            files = list(Path(output_dir).glob("*.*"))
            print(f"\n✓ 生成文件 {len(files)} 个:")
            for f in files:
                print(f"  - {f.name}: {f.stat().st_size} bytes")
            
            return (source_name, True, len(papers), len(successful), successful[0][0])
        else:
            print("✗ 无法下载任何文章")
            # 仍然导出未下载的文章
            output_dir = f"./output/verify_{source_name}"
            searcher.export_papers_with_citations(papers, {}, output_dir)
            return (source_name, False, len(papers), 0, "下载失败")
            
    except Exception as e:
        print(f"✗ 错误: {e}")
        import traceback
        traceback.print_exc()
        return (source_name, False, 0, 0, str(e))


def main():
    """测试所有数据源。"""
    print("\n" + "="*80)
    print("ZHUAI - 验证所有数据源下载能力")
    print("="*80)
    
    # 测试配置 - 使用容易找到开放获取文章的关键词
    tests = [
        # arXiv - 所有文章都可下载
        ("arxiv", "quantum computing", "量子计算 - 所有文章可下载"),
        
        # CrossRef - 搜索开放获取文章
        ("crossref", "open access machine learning", "开放获取机器学习"),
        
        # PubMed - 搜索PMC开放获取文章
        ("pubmed", "open access[filter] cancer", "开放获取癌症研究"),
        
        # Semantic Scholar - 开放获取文章
        ("semanticscholar", "open access artificial intelligence", "开放获取AI"),
        
        # Bing Academic
        ("bing", "deep learning open access", "深度学习开放获取"),
        
        # 中文数据源
        ("cnki", "人工智能 开放获取", "AI开放获取"),
        ("wanfang", "机器学习 开放获取", "机器学习开放获取"),
        ("vip", "深度学习 开放获取", "深度学习开放获取"),
        ("baidu", "人工智能 开放获取", "AI开放获取"),
    ]
    
    results = []
    
    for source_name, keyword, description in tests:
        print(f"\n{'='*80}")
        print(f"[{tests.index((source_name, keyword, description)) + 1}/{len(tests)}] {description}")
        result = test_source_download(source_name, keyword, max_results=20)
        results.append(result)
        
        # 短暂暂停
        time.sleep(2)
    
    # 最终报告
    print("\n" + "="*80)
    print("最终验证报告")
    print("="*80)
    
    print("\n数据源下载能力验证:")
    print(f"{'数据源':<20} {'状态':<8} {'搜索':<8} {'下载':<8} {'文章标题':<40}")
    print("-" * 84)
    
    success_count = 0
    for source_name, success, papers_count, downloaded_count, paper_title in results:
        status = "✓ 成功" if success else "✗ 失败"
        title_short = paper_title[:38] + "..." if len(paper_title) > 40 else paper_title
        print(f"{source_name:<20} {status:<8} {papers_count:<8} {downloaded_count:<8} {title_short:<40}")
        if success:
            success_count += 1
    
    print("-" * 84)
    print(f"总计: {success_count}/{len(results)} 个数据源可以下载文章")
    
    if success_count == len(results):
        print("\n✅ 所有数据源验证通过！")
    else:
        print(f"\n⚠️ 还有 {len(results) - success_count} 个数据源需要改进")
    
    # 显示生成的文件
    print("\n生成的文件:")
    for result_dir in Path("./output").glob("verify_*"):
        if result_dir.is_dir():
            files = list(result_dir.glob("*.*"))
            print(f"  {result_dir.name}: {len(files)} 个文件")


if __name__ == "__main__":
    main()