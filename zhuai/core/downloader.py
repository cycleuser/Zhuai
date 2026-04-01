"""Download manager for papers."""

import os
import csv
import asyncio
from pathlib import Path
from typing import List, Optional, Dict, Tuple
from tqdm import tqdm

from zhuai.models.paper import Paper
from zhuai.core.validator import PDFValidator


class DownloadManager:
    """Manages paper downloads and CSV export.
    
    Supports downloading:
    - PDF files
    - HTML versions (for arXiv papers)
    - Markdown conversions (from HTML)
    """
    
    def __init__(
        self,
        download_dir: str = "./downloads",
        max_concurrent: int = 5,
        timeout: int = 30,
        retry_attempts: int = 3,
    ):
        """Initialize download manager.
        
        Args:
            download_dir: Directory for downloaded PDFs.
            max_concurrent: Maximum concurrent downloads.
            timeout: Download timeout in seconds.
            retry_attempts: Number of retry attempts for failed downloads.
        """
        self.download_dir = Path(download_dir)
        self.max_concurrent = max_concurrent
        self.timeout = timeout
        self.retry_attempts = retry_attempts
        self.validator = PDFValidator(timeout)
        
        self.download_dir.mkdir(parents=True, exist_ok=True)
    
    def _sanitize_filename(self, title: str) -> str:
        """Sanitize filename from paper title.
        
        Args:
            title: Paper title.
            
        Returns:
            Sanitized filename.
        """
        invalid_chars = '<>:"/\\|?*'
        filename = "".join(c if c not in invalid_chars else "_" for c in title)
        filename = filename[:200].strip()
        return filename or "unnamed_paper"
    
    async def _download_file(
        self,
        session,
        url: str,
        filepath: Path,
        pbar: Optional[tqdm] = None,
    ) -> Tuple[bool, Optional[str]]:
        """Download a file from URL.
        
        Args:
            session: HTTP session
            url: URL to download
            filepath: Path to save file
            pbar: Progress bar
            
        Returns:
            Tuple of (success, filepath or error message)
        """
        for attempt in range(self.retry_attempts):
            try:
                async with session.get(url, timeout=self.timeout) as response:
                    if response.status != 200:
                        if attempt < self.retry_attempts - 1:
                            await asyncio.sleep(1)
                            continue
                        return False, f"HTTP {response.status}"
                    
                    content = await response.read()
                    
                    if filepath.exists():
                        if pbar:
                            pbar.update(1)
                        return True, str(filepath)
                    
                    with open(filepath, "wb") as f:
                        f.write(content)
                    
                    if pbar:
                        pbar.update(1)
                    
                    return True, str(filepath)
                    
            except asyncio.TimeoutError:
                if attempt < self.retry_attempts - 1:
                    await asyncio.sleep(1)
                    continue
                return False, "Timeout"
                
            except Exception as e:
                if attempt < self.retry_attempts - 1:
                    await asyncio.sleep(1)
                    continue
                return False, str(e)
        
        return False, "Max retries exceeded"
    
    async def _download_pdf(
        self,
        session,
        paper: Paper,
        pbar: Optional[tqdm] = None,
    ) -> Tuple[bool, Optional[str]]:
        """Download a single PDF asynchronously.
        
        Args:
            session: HTTP session.
            paper: Paper to download.
            pbar: Progress bar.
            
        Returns:
            Tuple of (success, filepath or error message).
        """
        if not paper.pdf_url:
            return False, "No PDF URL available"
        
        for attempt in range(self.retry_attempts):
            try:
                async with session.get(paper.pdf_url, timeout=self.timeout) as response:
                    if response.status != 200:
                        if attempt < self.retry_attempts - 1:
                            await asyncio.sleep(1)
                            continue
                        return False, f"HTTP {response.status}"
                    
                    content = await response.read()
                    
                    if not self.validator.validate_pdf_content(content):
                        return False, "Invalid PDF content"
                    
                    filename = self._sanitize_filename(paper.title)
                    filepath = self.download_dir / f"{filename}.pdf"
                    
                    if filepath.exists():
                        if pbar:
                            pbar.update(1)
                        return True, str(filepath)
                    
                    with open(filepath, "wb") as f:
                        f.write(content)
                    
                    if pbar:
                        pbar.update(1)
                    
                    return True, str(filepath)
                    
            except asyncio.TimeoutError:
                if attempt < self.retry_attempts - 1:
                    await asyncio.sleep(1)
                    continue
                return False, "Timeout"
                
            except Exception as e:
                if attempt < self.retry_attempts - 1:
                    await asyncio.sleep(1)
                    continue
                return False, str(e)
        
        return False, "Max retries exceeded"
    
    async def _download_html(
        self,
        session,
        paper: Paper,
        pbar: Optional[tqdm] = None,
    ) -> Tuple[bool, Optional[str]]:
        """Download HTML version of a paper.
        
        Args:
            session: HTTP session
            paper: Paper to download
            pbar: Progress bar
            
        Returns:
            Tuple of (success, filepath or error message)
        """
        html_url = paper.html_url
        
        if not html_url and paper.arxiv_id:
            html_url = f"https://arxiv.org/html/{paper.arxiv_id}"
        
        if not html_url:
            return False, "No HTML URL available"
        
        filename = self._sanitize_filename(paper.title)
        filepath = self.download_dir / f"{filename}.html"
        
        result = await self._download_file(session, html_url, filepath, pbar)
        return result
    
    async def _download_markdown(
        self,
        session,
        paper: Paper,
        pbar: Optional[tqdm] = None,
    ) -> Tuple[bool, Optional[str]]:
        """Download and convert paper to Markdown.
        
        Args:
            session: HTTP session
            paper: Paper to download
            pbar: Progress bar
            
        Returns:
            Tuple of (success, filepath or error message)
        """
        html_url = paper.html_url
        
        if not html_url and paper.arxiv_id:
            html_url = f"https://arxiv.org/html/{paper.arxiv_id}"
        
        if not html_url:
            return False, "No HTML URL available"
        
        try:
            async with session.get(html_url, timeout=self.timeout) as response:
                if response.status != 200:
                    return False, f"HTTP {response.status}"
                
                html_content = await response.text()
            
            from zhuai.utils.html_converter import convert_html_to_markdown
            markdown_content = convert_html_to_markdown(html_content, html_url)
            
            filename = self._sanitize_filename(paper.title)
            filepath = self.download_dir / f"{filename}.md"
            
            with open(filepath, "w", encoding="utf-8") as f:
                f.write(markdown_content)
            
            if pbar:
                pbar.update(1)
            
            return True, str(filepath)
            
        except Exception as e:
            return False, str(e)
    
    async def download_papers(
        self,
        papers: List[Paper],
        show_progress: bool = True,
        format: str = "pdf",
    ) -> Dict[str, Tuple[bool, Optional[str]]]:
        """Download multiple papers asynchronously.
        
        Args:
            papers: List of papers to download.
            show_progress: Show progress bar.
            format: Download format - "pdf", "html", "markdown", or "all".
            
        Returns:
            Dictionary mapping paper titles to (success, filepath/error).
        """
        import httpx
        
        results = {}
        
        if format == "pdf":
            downloadable_papers = [p for p in papers if p.pdf_url]
        elif format in ["html", "markdown"]:
            downloadable_papers = [p for p in papers if p.html_url or p.arxiv_id]
        elif format == "all":
            downloadable_papers = [p for p in papers if p.pdf_url or p.html_url or p.arxiv_id]
        else:
            downloadable_papers = [p for p in papers if p.pdf_url]
        
        if not downloadable_papers:
            return results
        
        async with httpx.AsyncClient(timeout=self.timeout) as client:
            pbar = tqdm(total=len(downloadable_papers), desc=f"Downloading {format}") if show_progress else None
            
            tasks = []
            for paper in downloadable_papers:
                if format == "pdf":
                    tasks.append(self._download_pdf(client, paper, pbar))
                elif format == "html":
                    tasks.append(self._download_html(client, paper, pbar))
                elif format == "markdown":
                    tasks.append(self._download_markdown(client, paper, pbar))
                elif format == "all":
                    tasks.append(self._download_all_formats(client, paper, pbar))
            
            download_results = await asyncio.gather(*tasks, return_exceptions=True)
            
            for paper, result in zip(downloadable_papers, download_results):
                if isinstance(result, Exception):
                    results[paper.title] = (False, str(result))
                else:
                    results[paper.title] = result
            
            if pbar:
                pbar.close()
        
        return results
    
    async def _download_all_formats(
        self,
        session,
        paper: Paper,
        pbar: Optional[tqdm] = None,
    ) -> Tuple[bool, Dict[str, str]]:
        """Download all available formats for a paper.
        
        Args:
            session: HTTP session
            paper: Paper to download
            pbar: Progress bar
            
        Returns:
            Tuple of (success, dict of format -> filepath)
        """
        results = {}
        success = False
        
        if paper.pdf_url:
            pdf_result = await self._download_pdf(session, paper, None)
            if pdf_result[0]:
                results["pdf"] = pdf_result[1]
                success = True
        
        if paper.html_url or paper.arxiv_id:
            html_result = await self._download_html(session, paper, None)
            if html_result[0]:
                results["html"] = html_result[1]
                success = True
            
            md_result = await self._download_markdown(session, paper, None)
            if md_result[0]:
                results["markdown"] = md_result[1]
                success = True
        
        if pbar:
            pbar.update(1)
        
        return success, results
    
    def download_papers_sync(
        self,
        papers: List[Paper],
        show_progress: bool = True,
        format: str = "pdf",
    ) -> Dict[str, Tuple[bool, Optional[str]]]:
        """Synchronous wrapper for download_papers.
        
        Args:
            papers: List of papers to download.
            show_progress: Show progress bar.
            format: Download format - "pdf", "html", "markdown", or "all".
            
        Returns:
            Dictionary mapping paper titles to (success, filepath/error).
        """
        return asyncio.run(self.download_papers(papers, show_progress, format))
    
    def export_to_csv(
        self,
        papers: List[Paper],
        filepath: str,
        include_downloaded: bool = True,
    ) -> None:
        """Export papers to CSV file.
        
        Args:
            papers: List of papers to export.
            filepath: Output CSV file path.
            include_downloaded: Include papers that were successfully downloaded.
        """
        fieldnames = [
            "title", "authors", "year", "journal", "doi", "pmid", "arxiv_id",
            "pdf_url", "source_url", "citations", "abstract", "keywords",
            "source", "article_type", "publisher", "language", "can_download",
        ]
        
        Path(filepath).parent.mkdir(parents=True, exist_ok=True)
        
        with open(filepath, "w", newline="", encoding="utf-8") as f:
            writer = csv.DictWriter(f, fieldnames=fieldnames, extrasaction="ignore")
            writer.writeheader()
            
            for paper in papers:
                if not include_downloaded and paper.can_download:
                    continue
                
                row = paper.to_dict()
                row["authors"] = "; ".join(paper.authors)
                row["keywords"] = "; ".join(paper.keywords)
                row["year"] = paper.year or ""
                row["can_download"] = str(paper.can_download)
                
                writer.writerow(row)
    
    def get_download_statistics(
        self,
        papers: List[Paper],
        results: Dict[str, Tuple[bool, Optional[str]]],
    ) -> Dict[str, int]:
        """Get download statistics.
        
        Args:
            papers: List of papers.
            results: Download results.
            
        Returns:
            Dictionary with statistics.
        """
        total = len(papers)
        with_pdf = sum(1 for p in papers if p.can_download)
        successful = sum(1 for r in results.values() if r[0])
        failed = with_pdf - successful
        
        return {
            "total_papers": total,
            "papers_with_pdf": with_pdf,
            "successful_downloads": successful,
            "failed_downloads": failed,
            "papers_without_pdf": total - with_pdf,
        }