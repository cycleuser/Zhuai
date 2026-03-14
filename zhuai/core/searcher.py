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
    BROWSER_SOURCES = {"cnki", "wanfang", "vip", "baidu", "bing"}
    
    def __init__(
        self,
        sources: Optional[List[str]] = None,
        timeout: int = 30,
        max_concurrent: int = 5,
        download_dir: str = "./downloads",
        cookies_path: Optional[str] = None,
        headless: bool = True,
        **source_configs,
    ):
        """Initialize paper searcher.
        
        Args:
            sources: List of source names to use. Default: all sources.
            timeout: Request timeout in seconds.
            max_concurrent: Maximum concurrent downloads.
            download_dir: Directory for downloaded files.
            cookies_path: Path to cookies JSON file for browser sources.
            headless: Run browser in headless mode.
            **source_configs: Source-specific configurations.
        """
        self.timeout = timeout
        self.max_concurrent = max_concurrent
        self.cookies_path = cookies_path
        self.headless = headless
        
        if sources is None:
            sources = list(self.DEFAULT_SOURCES.keys())
        
        self.sources: Dict[str, BaseSource] = {}
        for source_name in sources:
            if source_name in self.DEFAULT_SOURCES:
                source_class = self.DEFAULT_SOURCES[source_name]
                config = source_configs.get(source_name, {})
                config["timeout"] = timeout
                
                if source_name in self.BROWSER_SOURCES:
                    config["cookies_path"] = cookies_path
                    config["headless"] = headless
                
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
        """Search for papers across multiple sources."""
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
        """Export papers to CSV file."""
        self.download_manager.export_to_csv(papers, filepath)
    
    def export_papers_with_citations(
        self,
        papers: List[Paper],
        download_results: Optional[Dict[str, tuple]] = None,
        output_dir: str = "./output",
    ) -> None:
        """Export papers with citations and links to CSV and HTML.
        
        Available papers: citations + local file path
        Unavailable papers: citations + download links
        """
        output_path = Path(output_dir)
        output_path.mkdir(parents=True, exist_ok=True)
        
        available_papers = []
        unavailable_papers = []
        
        for paper in papers:
            if download_results and paper.title in download_results:
                success, filepath = download_results[paper.title]
                if success and filepath:
                    available_papers.append((paper, filepath))
                else:
                    unavailable_papers.append(paper)
            elif paper.can_download:
                unavailable_papers.append(paper)
            else:
                unavailable_papers.append(paper)
        
        if available_papers:
            self._export_available_papers(available_papers, output_path)
        
        if unavailable_papers:
            self._export_unavailable_papers(unavailable_papers, output_path)
    
    def _export_available_papers(self, papers_with_paths: List[tuple], output_dir: Path) -> None:
        """Export available papers with citations and file paths."""
        import csv
        
        # CSV export
        csv_file = output_dir / "available_papers.csv"
        with open(csv_file, "w", newline="", encoding="utf-8") as f:
            fieldnames = [
                "title", "authors", "year", "journal", "doi",
                "citation_apa", "citation_gb_t_7714",
                "local_file_path", "source"
            ]
            writer = csv.DictWriter(f, fieldnames=fieldnames)
            writer.writeheader()
            
            for paper, filepath in papers_with_paths:
                writer.writerow({
                    "title": paper.title,
                    "authors": "; ".join(paper.authors),
                    "year": paper.year or "",
                    "journal": paper.journal or "",
                    "doi": paper.doi or "",
                    "citation_apa": self.citation_formatter.format(paper, "apa"),
                    "citation_gb_t_7714": self.citation_formatter.format(paper, "gb_t_7714"),
                    "local_file_path": filepath,
                    "source": paper.source or "",
                })
        
        # HTML export
        html_file = output_dir / "available_papers.html"
        self._generate_html_available(papers_with_paths, html_file)
        
        print(f"✓ Exported {len(papers_with_paths)} available papers to {output_dir}/")
    
    def _export_unavailable_papers(self, papers: List[Paper], output_dir: Path) -> None:
        """Export unavailable papers with citations and download links."""
        import csv
        
        # CSV export
        csv_file = output_dir / "unavailable_papers.csv"
        with open(csv_file, "w", newline="", encoding="utf-8") as f:
            fieldnames = [
                "title", "authors", "year", "journal", "doi",
                "citation_apa", "citation_gb_t_7714",
                "source_url", "source"
            ]
            writer = csv.DictWriter(f, fieldnames=fieldnames)
            writer.writeheader()
            
            for paper in papers:
                writer.writerow({
                    "title": paper.title,
                    "authors": "; ".join(paper.authors),
                    "year": paper.year or "",
                    "journal": paper.journal or "",
                    "doi": paper.doi or "",
                    "citation_apa": self.citation_formatter.format(paper, "apa"),
                    "citation_gb_t_7714": self.citation_formatter.format(paper, "gb_t_7714"),
                    "source_url": paper.source_url or "",
                    "source": paper.source or "",
                })
        
        # HTML export
        html_file = output_dir / "unavailable_papers.html"
        self._generate_html_unavailable(papers, html_file)
        
        print(f"✓ Exported {len(papers)} unavailable papers to {output_dir}/")
    
    def _generate_html_available(self, papers_with_paths: List[tuple], filepath: Path) -> None:
        """Generate HTML for available papers."""
        html_parts = []
        html_parts.append("""<!DOCTYPE html>
<html lang="zh-CN">
<head><meta charset="UTF-8"><title>已下载文献 - Downloaded Papers</title>
<style>body{font-family:sans-serif;max-width:1200px;margin:0 auto;padding:20px;}
h1{color:#4CAF50;}.paper{background:white;padding:20px;margin:15px 0;border-radius:8px;box-shadow:0 2px 4px rgba(0,0,0,0.1);}
.title{font-size:1.2em;font-weight:bold;color:#2196F3;margin-bottom:10px;}
.info{color:#666;margin:10px 0;}.citation{background:#f5f5f5;padding:10px;margin:10px 0;border-radius:4px;}
.label{font-weight:bold;color:#4CAF50;}.file-link{display:inline-block;margin-top:10px;padding:8px 16px;background:#4CAF50;color:white;text-decoration:none;border-radius:4px;}</style></head>
<body><h1>已下载文献 / Downloaded Papers</h1>""")
        
        for i, (paper, local_path) in enumerate(papers_with_paths, 1):
            title = paper.title.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")
            authors = ", ".join(paper.authors[:5]).replace("&", "&amp;")
            apa = self.citation_formatter.format(paper, "apa").replace("&", "&amp;")
            gbt = self.citation_formatter.format(paper, "gb_t_7714").replace("&", "&amp;")
            
            html_parts.append(f"""<div class="paper">
<div class="title">{i}. {title}</div>
<div class="info"><strong>作者:</strong> {authors} | <strong>年份:</strong> {paper.year or 'N/A'} | <strong>期刊:</strong> {paper.journal or 'N/A'}</div>
<div class="citation"><span class="label">APA格式:</span> {apa}</div>
<div class="citation"><span class="label">GB/T 7714:</span> {gbt}</div>
<a href="file://{local_path}" class="file-link">打开本地文件</a>
</div>""")
        
        html_parts.append("</body></html>")
        
        with open(filepath, "w", encoding="utf-8") as f:
            f.write("\n".join(html_parts))
    
    def _generate_html_unavailable(self, papers: List[Paper], filepath: Path) -> None:
        """Generate HTML for unavailable papers."""
        html_parts = []
        html_parts.append("""<!DOCTYPE html>
<html lang="zh-CN">
<head><meta charset="UTF-8"><title>未下载文献 - Unavailable Papers</title>
<style>body{font-family:sans-serif;max-width:1200px;margin:0 auto;padding:20px;}
h1{color:#FF9800;}.paper{background:white;padding:20px;margin:15px 0;border-radius:8px;box-shadow:0 2px 4px rgba(0,0,0,0.1);}
.title{font-size:1.2em;font-weight:bold;color:#2196F3;margin-bottom:10px;}
.info{color:#666;margin:10px 0;}.citation{background:#f5f5f5;padding:10px;margin:10px 0;border-radius:4px;}
.label{font-weight:bold;color:#FF9800;}.link-btn{display:inline-block;margin-top:10px;margin-right:10px;padding:8px 16px;background:#2196F3;color:white;text-decoration:none;border-radius:4px;}
.link-btn.doi{background:#FF9800;}</style></head>
<body><h1>未下载文献 / Unavailable Papers</h1>""")
        
        for i, paper in enumerate(papers, 1):
            title = paper.title.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")
            authors = ", ".join(paper.authors[:5]).replace("&", "&amp;")
            apa = self.citation_formatter.format(paper, "apa").replace("&", "&amp;")
            gbt = self.citation_formatter.format(paper, "gb_t_7714").replace("&", "&amp;")
            
            paper_html = f"""<div class="paper">
<div class="title">{i}. {title}</div>
<div class="info"><strong>作者:</strong> {authors} | <strong>年份:</strong> {paper.year or 'N/A'} | <strong>期刊:</strong> {paper.journal or 'N/A'}</div>
<div class="citation"><span class="label">APA格式:</span> {apa}</div>
<div class="citation"><span class="label">GB/T 7714:</span> {gbt}</div>"""
            
            if paper.source_url:
                paper_html += f"""<a href="{paper.source_url}" class="link-btn" target="_blank">查看原文</a>"""
            if paper.doi:
                paper_html += f"""<a href="https://doi.org/{paper.doi}" class="link-btn doi" target="_blank">DOI: {paper.doi}</a>"""
            
            paper_html += "</div>"
            html_parts.append(paper_html)
        
        html_parts.append("</body></html>")
        
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
    
    def export_unavailable_citations(
        self,
        papers: List[Paper],
        filepath: str,
        style: str = "apa",
    ) -> None:
        """Export citations for papers without PDFs to a text file.
        
        Args:
            papers: List of papers.
            filepath: Output file path.
            style: Citation style (apa, mla, chicago, gb_t_7714, bibtex).
        """
        unavailable = [p for p in papers if not p.can_download]
        
        with open(filepath, "w", encoding="utf-8") as f:
            for i, paper in enumerate(unavailable, 1):
                citation = self.citation_formatter.format(paper, style)
                f.write(f"[{i}] {citation}\n")
                
                if paper.source_url:
                    f.write(f"    URL: {paper.source_url}\n")
                if paper.doi:
                    f.write(f"    DOI: https://doi.org/{paper.doi}\n")
                f.write("\n")
        
        print(f"Exported {len(unavailable)} citations to {filepath}")
    
    async def close(self) -> None:
        """Close all source connections."""
        for source in self.sources.values():
            if hasattr(source, "close"):
                await source.close()
    
    @staticmethod
    def list_all_sources() -> List[str]:
        """List all available sources."""
        return list(ALL_SOURCES.keys())