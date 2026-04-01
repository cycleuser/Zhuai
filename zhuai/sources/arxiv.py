"""arXiv paper source using HTTP API."""

import asyncio
import time
import re
from datetime import datetime
from typing import List, Optional, Dict, Any
from xml.etree import ElementTree
import requests
from zhuai.models.paper import Paper
from zhuai.sources.base import BaseSource


class ArxivSource(BaseSource):
    """arXiv paper source using HTTP API."""
    
    BASE_URL = "http://export.arxiv.org/api/query"
    HTML_BASE_URL = "https://arxiv.org/html"
    RATE_LIMIT_DELAY = 3.0
    
    def __init__(self, timeout: int = 30, check_html: bool = True):
        """Initialize arXiv source.
        
        Args:
            timeout: Request timeout in seconds
            check_html: Whether to check for HTML version availability
        """
        super().__init__(timeout)
        self._last_request_time: float = 0
        self.check_html = check_html
    
    @property
    def name(self) -> str:
        """Get source name."""
        return "arXiv"
    
    @property
    def supports_pdf(self) -> bool:
        """Check if source supports PDF download."""
        return True
    
    @property
    def supports_html(self) -> bool:
        """Check if source supports HTML version."""
        return True
    
    def _make_request(self, params: Dict[str, Any]) -> str:
        """Make request to arXiv API with rate limiting."""
        elapsed = time.time() - self._last_request_time
        if elapsed < self.RATE_LIMIT_DELAY:
            time.sleep(self.RATE_LIMIT_DELAY - elapsed)
        
        self._last_request_time = time.time()
        
        response = requests.get(self.BASE_URL, params=params, timeout=self.timeout)
        response.raise_for_status()
        return response.text
    
    def _check_html_available(self, arxiv_id: str) -> bool:
        """Check if HTML version is available for an arXiv paper.
        
        arXiv HTML versions are only available for papers where authors
        have uploaded LaTeX source that can be converted to HTML.
        
        Args:
            arxiv_id: arXiv paper ID
            
        Returns:
            True if HTML version exists
        """
        html_url = f"{self.HTML_BASE_URL}/{arxiv_id}"
        try:
            response = requests.get(html_url, timeout=10, allow_redirects=True)
            if response.status_code == 200:
                # Check for "No HTML" message
                if "No HTML" in response.text or "HTML is not available" in response.text:
                    return False
                # Check if there's actual content
                if 'arXiv' in response.text and len(response.text) > 15000:
                    return True
            return False
        except Exception:
            return False
    
    def _parse_entry(self, entry: ElementTree.Element, check_html: bool = True) -> Optional[Paper]:
        """Parse a single arXiv entry."""
        ns = {"atom": "http://www.w3.org/2005/Atom"}
        
        title_elem = entry.find("atom:title", ns)
        title = title_elem.text.strip() if title_elem is not None and title_elem.text else ""
        
        if not title:
            return None
        
        authors = []
        for author in entry.findall("atom:author", ns):
            name_elem = author.find("atom:name", ns)
            if name_elem is not None and name_elem.text:
                authors.append(name_elem.text.strip())
        
        abstract = None
        summary_elem = entry.find("atom:summary", ns)
        if summary_elem is not None and summary_elem.text:
            abstract = summary_elem.text.strip()
        
        publication_date = None
        published_elem = entry.find("atom:published", ns)
        if published_elem is not None and published_elem.text:
            try:
                publication_date = datetime.fromisoformat(published_elem.text.replace("Z", "+00:00"))
            except ValueError:
                pass
        
        arxiv_id = None
        doi = None
        journal = None
        
        id_elem = entry.find("atom:id", ns)
        if id_elem is not None and id_elem.text:
            arxiv_id = id_elem.text.split("/")[-1]
        
        for link in entry.findall("atom:link", ns):
            href = link.get("href", "")
            rel = link.get("rel", "")
            if rel == "alternate" and "arxiv.org/abs" in href:
                arxiv_id = href.split("/")[-1]
        
        journal_elem = entry.find("atom:journal_ref", ns)
        if journal_elem is not None and journal_elem.text:
            journal = journal_elem.text.strip()
        
        for elem in entry.iter():
            if elem.text and "doi:" in elem.text.lower():
                doi_match = re.search(r'10\.\d{4,}/[^\s]+', elem.text)
                if doi_match:
                    doi = doi_match.group()
                    break
        
        pdf_url = f"https://arxiv.org/pdf/{arxiv_id}" if arxiv_id else None
        source_url = f"https://arxiv.org/abs/{arxiv_id}" if arxiv_id else None
        html_url = f"{self.HTML_BASE_URL}/{arxiv_id}" if arxiv_id else None
        
        has_html = False
        if check_html and arxiv_id:
            has_html = self._check_html_available(arxiv_id)
        
        keywords = []
        for cat in entry.findall("atom:category", ns):
            term = cat.get("term", "")
            if term:
                keywords.append(term)
        
        return Paper(
            title=title,
            authors=authors,
            abstract=abstract,
            publication_date=publication_date,
            journal=journal,
            doi=doi,
            arxiv_id=arxiv_id,
            pdf_url=pdf_url,
            html_url=html_url,
            source_url=source_url,
            citations=0,
            keywords=keywords,
            source=self.name,
            article_type="preprint",
            has_html=has_html,
        )
    
    async def search(
        self,
        query: str,
        max_results: int = 100,
        check_html: Optional[bool] = None,
        **kwargs,
    ) -> List[Paper]:
        """Search arXiv for papers.
        
        Args:
            query: Search query
            max_results: Maximum number of results
            check_html: Whether to check HTML availability (overrides instance setting)
            **kwargs: Additional parameters
            
        Returns:
            List of papers
        """
        if check_html is None:
            check_html = self.check_html
        
        def _search() -> List[Paper]:
            params = {
                "search_query": f"all:{query}",
                "start": 0,
                "max_results": max_results,
                "sortBy": "relevance",
                "sortOrder": "descending",
            }
            
            try:
                response_text = self._make_request(params)
                root = ElementTree.fromstring(response_text)
                
                ns = {"atom": "http://www.w3.org/2005/Atom"}
                entries = root.findall("atom:entry", ns)
                
                papers = []
                for entry in entries:
                    try:
                        paper = self._parse_entry(entry, check_html=check_html)
                        if paper:
                            papers.append(paper)
                    except Exception:
                        continue
                
                return papers
                
            except Exception as e:
                print(f"Error searching arXiv: {e}")
                return []
        
        loop = asyncio.get_event_loop()
        return await loop.run_in_executor(None, _search)
    
    async def get_paper_by_id(self, paper_id: str, check_html: bool = True) -> Optional[Paper]:
        """Get a paper by arXiv ID.
        
        Args:
            paper_id: arXiv paper ID
            check_html: Whether to check HTML availability
            
        Returns:
            Paper if found
        """
        def _get() -> Optional[Paper]:
            params = {
                "id_list": paper_id,
            }
            
            try:
                response_text = self._make_request(params)
                root = ElementTree.fromstring(response_text)
                
                ns = {"atom": "http://www.w3.org/2005/Atom"}
                entry = root.find("atom:entry", ns)
                
                if entry is not None:
                    return self._parse_entry(entry, check_html=check_html)
                
            except Exception as e:
                print(f"Error getting arXiv paper {paper_id}: {e}")
            
            return None
        
        loop = asyncio.get_event_loop()
        return await loop.run_in_executor(None, _get)
    
    async def check_html_versions(self, papers: List[Paper]) -> Dict[str, bool]:
        """Check HTML availability for multiple papers.
        
        Args:
            papers: List of papers to check
            
        Returns:
            Dict mapping arxiv_id to HTML availability
        """
        results = {}
        
        def _check_all():
            for paper in papers:
                if paper.arxiv_id:
                    results[paper.arxiv_id] = self._check_html_available(paper.arxiv_id)
        
        loop = asyncio.get_event_loop()
        await loop.run_in_executor(None, _check_all)
        return results
    
    async def close(self) -> None:
        """Close resources."""
        pass