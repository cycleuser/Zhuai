"""Main paper searcher module."""

import asyncio
from typing import List, Optional, Dict, Type
from pathlib import Path
from tqdm import tqdm

from zhuai.models.paper import Paper
from zhuai.core.downloader import DownloadManager
from zhuai.core.citation import CitationFormatter
from zhuai.sources.base import BaseSource
from zhuai.sources import ALL_SOURCES


class PaperSearcher:
    """Main paper searcher class with comprehensive source support."""
    
    DEFAULT_SOURCES: Dict[str, Type[BaseSource]] = ALL_SOURCES
    
    def __init__(
        self,
        sources: Optional[List[str]] = None,
        timeout: int = 30,
        max_concurrent: int = 5,
        download_dir: str = "./downloads",
        **source_configs,
    ):
        """Initialize paper searcher.
        
        Args:
            sources: List of source names. None = all sources.
            timeout: Request timeout in seconds.
            max_concurrent: Maximum concurrent requests.
            download_dir: Directory for downloaded PDFs.
            **source_configs: Configuration for specific sources.
        """
        self.timeout = timeout
        self.max_concurrent = max_concurrent
        
        if sources is None:
            sources = list(self.DEFAULT_SOURCES.keys())
        
        self.sources: Dict[str, BaseSource] = {}
        for source_name in sources:
            if source_name in self.DEFAULT_SOURCES:
                source_class = self.DEFAULT_SOURCES[source_name]
                config = source_configs.get(source_name, {})
                config["timeout"] = timeout
                self.sources[source_name] = source_class(**config)
        
        self.download_manager = DownloadManager(
            download_dir=download_dir,
            max_concurrent=max_concurrent,
            timeout=timeout,
        )
        self.citation_formatter = CitationFormatter()
    
    async def search(
        self,
        query: str,
        max_results: int = 100,
        sources: Optional[List[str]] = None,
        show_progress: bool = True,
    ) -> List[Paper]:
        """Search for papers across multiple sources.
        
        Args:
            query: Search query (supports Chinese and English).
            max_results: Maximum total results.
            sources: List of sources to search. None = all configured.
            show_progress: Show progress bar.
            
        Returns:
            List of papers matching the query.
        """
        if sources is None:
            sources_to_search = list(self.sources.keys())
        else:
            sources_to_search = [s for s in sources if s in self.sources]
        
        if not sources_to_search:
            return []
        
        results_per_source = max(10, max_results // len(sources_to_search))
        
        all_papers: List[Paper] = []
        
        pbar = None
        if show_progress:
            pbar = tqdm(total=len(sources_to_search), desc="Searching sources")
        
        for source_name in sources_to_search:
            source = self.sources[source_name]
            try:
                papers = await source.search(query, max_results=results_per_source)
                all_papers.extend(papers)
            except Exception as e:
                print(f"Error searching {source_name}: {e}")
            finally:
                if pbar:
                    pbar.update(1)
        
        if pbar:
            pbar.close()
        
        unique_papers = self._deduplicate_papers(all_papers)
        
        unique_papers.sort(key=lambda p: p.citations, reverse=True)
        
        return unique_papers[:max_results]
    
    def search_sync(
        self,
        query: str,
        max_results: int = 100,
        sources: Optional[List[str]] = None,
        show_progress: bool = True,
    ) -> List[Paper]:
        """Synchronous wrapper for search."""
        return asyncio.run(self.search(
            query=query,
            max_results=max_results,
            sources=sources,
            show_progress=show_progress,
        ))
    
    async def download_papers(
        self,
        papers: List[Paper],
        show_progress: bool = True,
    ) -> Dict[str, tuple]:
        """Download papers with available PDFs."""
        return await self.download_manager.download_papers(papers, show_progress)
    
    def download_papers_sync(
        self,
        papers: List[Paper],
        show_progress: bool = True,
    ) -> Dict[str, tuple]:
        """Synchronous wrapper for download_papers."""
        return asyncio.run(self.download_papers(papers, show_progress))
    
    def export_to_csv(
        self,
        papers: List[Paper],
        filepath: str,
    ) -> None:
        """Export papers to CSV."""
        self.download_manager.export_to_csv(papers, filepath)
    
    def export_unavailable_citations(
        self,
        papers: List[Paper],
        filepath: str,
        style: str = "apa",
    ) -> None:
        """Export citations for papers without PDFs.
        
        Args:
            papers: List of papers.
            filepath: Output file path.
            style: Citation style (apa, mla, chicago, gb_t_7714, bibtex).
        """
        unavailable = [p for p in papers if not p.can_download]
        
        if not unavailable:
            return
        
        # Export text file
        with open(filepath, "w", encoding="utf-8") as f:
            for i, paper in enumerate(unavailable, 1):
                citation = self.citation_formatter.format(paper, style)
                f.write(f"{i}. {citation}\n\n")
                
                if paper.source_url:
                    f.write(f"   URL: {paper.source_url}\n")
                if paper.doi:
                    f.write(f"   DOI: https://doi.org/{paper.doi}\n")
                f.write("\n")
        
        # Export CSV with bilingual citations and download links
        csv_filepath = filepath.replace(".txt", "_with_citations.csv")
        self._export_unavailable_csv(unavailable, csv_filepath)
        
        # Export HTML with formatted citations and links
        html_filepath = filepath.replace(".txt", "_with_citations.html")
        self._export_unavailable_html(unavailable, html_filepath)
    
    def _export_unavailable_csv(self, papers: List[Paper], filepath: str) -> None:
        """Export unavailable papers to CSV with bilingual citations.
        
        Args:
            papers: List of unavailable papers.
            filepath: Output CSV file path.
        """
        import csv
        
        fieldnames = [
            "title",
            "authors",
            "year",
            "journal",
            "volume",
            "issue",
            "pages",
            "doi",
            "source_url",
            "pdf_url",
            "source",
            "citation_apa",
            "citation_gb_t_7714",
            "citation_mla",
            "citation_chicago",
            "citation_bibtex",
        ]
        
        with open(filepath, "w", newline="", encoding="utf-8") as f:
            writer = csv.DictWriter(f, fieldnames=fieldnames)
            writer.writeheader()
            
            for paper in papers:
                row = {
                    "title": paper.title,
                    "authors": "; ".join(paper.authors),
                    "year": paper.year or "",
                    "journal": paper.journal or "",
                    "volume": paper.volume or "",
                    "issue": paper.issue or "",
                    "pages": paper.pages or "",
                    "doi": paper.doi or "",
                    "source_url": paper.source_url or "",
                    "pdf_url": paper.pdf_url or "",
                    "source": paper.source or "",
                    "citation_apa": self.citation_formatter.format(paper, "apa"),
                    "citation_gb_t_7714": self.citation_formatter.format(paper, "gb_t_7714"),
                    "citation_mla": self.citation_formatter.format(paper, "mla"),
                    "citation_chicago": self.citation_formatter.format(paper, "chicago"),
                    "citation_bibtex": self.citation_formatter.format(paper, "bibtex"),
                }
                writer.writerow(row)
    
def _export_unavailable_html(self, papers: List[Paper], filepath: str) -> None:
        """Export unavailable papers to formatted HTML with links.
        
        Args:
            papers: List of unavailable papers.
            filepath: Output HTML file path.
        """
        # Build HTML content
        html_parts = []
        
        # HTML header
        html_parts.append("""<!DOCTYPE html>
<html lang="zh-CN">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>无法下载的文献列表 - Unavailable Papers</title>
    <style>
        body {
            font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, "Helvetica Neue", Arial, sans-serif;
            line-height: 1.6;
            max-width: 1200px;
            margin: 0 auto;
            padding: 20px;
            background-color: #f5f5f5;
        }
        h1 {
            color: #333;
            border-bottom: 3px solid #4CAF50;
            padding-bottom: 10px;
        }
        h2 {
            color: #555;
            margin-top: 30px;
        }
        .paper {
            background: white;
            border-radius: 8px;
            padding: 20px;
            margin-bottom: 20px;
            box-shadow: 0 2px 4px rgba(0,0,0,0.1);
        }
        .paper-title {
            font-size: 1.2em;
            font-weight: bold;
            color: #2196F3;
            margin-bottom: 10px;
        }
        .paper-info {
            color: #666;
            margin-bottom: 15px;
        }
        .paper-info span {
            margin-right: 15px;
        }
        .citation-section {
            margin-top: 15px;
            padding-top: 15px;
            border-top: 1px solid #eee;
        }
        .citation-format {
            margin-bottom: 10px;
        }
        .citation-label {
            font-weight: bold;
            color: #4CAF50;
            display: inline-block;
            width: 120px;
        }
        .citation-text {
            color: #333;
            font-style: italic;
        }
        .links {
            margin-top: 15px;
            padding-top: 15px;
            border-top: 1px solid #eee;
        }
        .links a {
            display: inline-block;
            margin-right: 15px;
            padding: 8px 16px;
            background-color: #2196F3;
            color: white;
            text-decoration: none;
            border-radius: 4px;
            transition: background-color 0.3s;
        }
        .links a:hover {
            background-color: #1976D2;
        }
        .links a.doi {
            background-color: #FF9800;
        }
        .links a.doi:hover {
            background-color: #F57C00;
        }
        .summary {
            background: #E3F2FD;
            border-left: 4px solid #2196F3;
            padding: 15px;
            margin-bottom: 20px;
        }
    </style>
</head>
<body>
    <h1>无法下载的文献列表 / Unavailable Papers</h1>""")
        
        # Summary section
        sources_list = list(set(p.source or "Unknown" for p in papers))
        html_parts.append(f"""
    <div class="summary">
        <strong>统计 / Statistics:</strong><br>
        总数 / Total: {len(papers)} 篇文献<br>
        数据来源 / Sources: {', '.join(sources_list)}
    </div>
    
    <h2>文献列表 / Paper List</h2>""")
        
        # Paper entries
        for i, paper in enumerate(papers, 1):
            # Authors
            authors = ", ".join(paper.authors[:5])
            if len(paper.authors) > 5:
                authors += f" et al. ({len(paper.authors)} authors)"
            
            # Escape HTML special characters
            title = paper.title.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")
            authors = authors.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")
            
            # Citation formats
            citation_apa = self.citation_formatter.format(paper, "apa").replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")
            citation_gbt = self.citation_formatter.format(paper, "gb_t_7714").replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")
            
            # Build paper HTML
            paper_html = f"""
    <div class="paper">
        <div class="paper-title">{i}. {title}</div>
        <div class="paper-info">
            <span><strong>作者/Authors:</strong> {authors}</span>
            <span><strong>年份/Year:</strong> {paper.year or 'N/A'}</span>
            <span><strong>期刊/Journal:</strong> {paper.journal or 'N/A'}</span>
            <span><strong>来源/Source:</strong> {paper.source or 'N/A'}</span>
        </div>
        <div class="citation-section">
            <div class="citation-format">
                <span class="citation-label">APA格式:</span>
                <span class="citation-text">{citation_apa}</span>
            </div>
            <div class="citation-format">
                <span class="citation-label">GB/T 7714:</span>
                <span class="citation-text">{citation_gbt}</span>
            </div>
        </div>
        <div class="links">"""
            
            if paper.source_url:
                paper_html += f"""
            <a href="{paper.source_url}" target="_blank">查看原文/View Paper</a>"""
            
            if paper.doi:
                paper_html += f"""
            <a href="https://doi.org/{paper.doi}" class="doi" target="_blank">DOI: {paper.doi}</a>"""
            
            paper_html += """
        </div>
    </div>"""
            
            html_parts.append(paper_html)
        
        # HTML footer
        html_parts.append("""
</body>
</html>""")
        
        # Write HTML file
        with open(filepath, "w", encoding="utf-8") as f:
            f.write("\n".join(html_parts))
    
    def get_statistics(
        self,
        papers: List[Paper],
        download_results: Optional[Dict[str, tuple]] = None,
    ) -> Dict[str, int]:
        """Get statistics about search and download results."""
        stats = {
            "total_papers": len(papers),
            "papers_with_pdf": sum(1 for p in papers if p.can_download),
            "papers_without_pdf": sum(1 for p in papers if not p.can_download),
            "unique_sources": len(set(p.source for p in papers if p.source)),
        }
        
        if download_results:
            stats.update(self.download_manager.get_download_statistics(papers, download_results))
        
        return stats
    
    async def get_paper_by_id(
        self,
        paper_id: str,
        source: Optional[str] = None,
    ) -> Optional[Paper]:
        """Get a paper by its ID."""
        if source and source in self.sources:
            return await self.sources[source].get_paper_by_id(paper_id)
        
        for source_name, source_obj in self.sources.items():
            try:
                paper = await source_obj.get_paper_by_id(paper_id)
                if paper:
                    return paper
            except Exception:
                continue
        
        return None
    
    def _deduplicate_papers(self, papers: List[Paper]) -> List[Paper]:
        """Remove duplicate papers."""
        seen = set()
        unique = []
        
        for paper in papers:
            key = None
            if paper.doi:
                key = f"doi:{paper.doi}"
            elif paper.pmid:
                key = f"pmid:{paper.pmid}"
            elif paper.arxiv_id:
                key = f"arxiv:{paper.arxiv_id}"
            else:
                key = f"title:{paper.title.lower()}"
            
            if key not in seen:
                seen.add(key)
                unique.append(paper)
        
        return unique
    
    async def close(self) -> None:
        """Close all source connections."""
        for source in self.sources.values():
            if hasattr(source, "close"):
                await source.close()
    
    @staticmethod
    def list_all_sources() -> List[str]:
        """List all available sources."""
        return list(ALL_SOURCES.keys())