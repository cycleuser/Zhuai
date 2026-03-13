#!/usr/bin/env python3
"""
最终验证测试 - 只测试已确认可用的数据源
"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from zhuai import PaperSearcher


def main():
    """测试所有可用的数据源."""
    print("\n" + "="*80)
    print("ZHUAI - 最终验证测试")
    print("="*80)
    
    # 测试已确认可用的数据源
    sources = [
        ("arxiv", "quantum computing", "量子计算"),
        ("crossref", "machine learning", "机器学习"),
    ]
    
    results = []
    
    for source_name, keyword_en, keyword_cn in sources:
        print(f"\n{'='*80}")
        print(f"测试数据源: {source_name}")
        print(f"关键词: {keyword_en}")
        print("="*80)
        
        try:
            searcher = PaperSearcher(
                sources=[source_name],
                download_dir=f"./final_test/{source_name}"
            )
            
            # 搜索
            papers = searcher.search_sync(keyword_en, max_results=5)
            print(f"✓ 找到 {len(papers)} 篇文献")
            
            if not papers:
                continue
            
            # 显示文章
            for i, paper in enumerate(papers[:3], 1):
                print(f"\n{i}. {paper.title[:60]}...")
                if paper.pdf_url:
                    print(f"   PDF: {paper.pdf_url[:60]}...")
            
            # 下载
            download_results = searcher.download_papers_sync(papers[:3])
            downloaded = sum(1 for r in download_results.values() if r[0])
            print(f"\n✓ 成功下载 {downloaded} 个PDF")
            
            # 导出
            output_dir = f"./final_output/{source_name}"
            searcher.export_papers_with_citations(papers, download_results, output_dir)
            
            # 检查生成的文件
            files = list(Path(output_dir).glob("*.*"))
            print(f"✓ 生成 {len(files)} 个文件:")
            for f in files:
                print(f"  - {f.name}: {f.stat().st_size} bytes")
            
            results.append((source_name, len(papers), downloaded, True))
            
        except Exception as e:
            print(f"✗ 错误: {e}")
            results.append((source_name, 0, 0, False))
    
    # 总结
    print("\n" + "="*80)
    print("最终验证报告")
    print("="*80)
    
    print("\n已验证可用的数据源:")
    print(f"{'数据源':<15} {'搜索结果':<10} {'下载PDF':<10} {'状态':<10}")
    print("-" * 45)
    
    total_papers = 0
    total_downloads = 0
    success_count = 0
    
    for source_name, papers_count, downloaded, success in results:
        status = "✓ 正常" if success else "✗ 失败"
        print(f"{source_name:<15} {papers_count:<10} {downloaded:<10} {status:<10}")
        total_papers += papers_count
        total_downloads += downloaded
        if success:
            success_count += 1
    
    print("-" * 45)
    print(f"{'总计':<15} {total_papers:<10} {total_downloads:<10}")
    
    print(f"\n✅ {success_count}/{len(sources)} 个数据源验证成功")
    
    print("\n生成的输出文件:")
    for output_dir in Path("./final_output").glob("*"):
        if output_dir.is_dir():
            files = list(output_dir.glob("*.*"))
            print(f"\n{output_dir.name}:")
            for f in files:
                print(f"  ✓ {f.name}")


if __name__ == "__main__":
    main()