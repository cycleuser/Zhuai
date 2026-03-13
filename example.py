#!/usr/bin/env python3
"""
Example usage of Zhuai.
"""

from zhuai import PaperSearcher

# Create searcher instance
searcher = PaperSearcher()

# Search papers (supports both English and Chinese)
papers = searcher.search_sync("summation effect", max_results=10)

# Print results
print(f"Found {len(papers)} papers\n")

for i, paper in enumerate(papers[:5], 1):
    print(f"{i}. {paper.title}")
    print(f"   Authors: {', '.join(paper.authors[:3])}")
    if paper.year:
        print(f"   Year: {paper.year}")
    print()