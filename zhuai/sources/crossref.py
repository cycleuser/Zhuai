"""CrossRef paper source with Unpaywall support for open access PDFs."""

import asyncio
from datetime import datetime
from typing import List, Optional, Dict, Any
import aiohttp
from zhuai.models.paper import Paper
from zhuai.sources.base import BaseSource


class CrossRefSource(BaseSource):
    """CrossRef paper source with Unpaywall integration."""
    
    BASE_URL = "https://api.crossref.org"
    UNPAYWALL_URL = "https://api.unpaywall.org/v2"
    
    def __init__(self, email: Optional[str] = None, timeout: int = 30):
        """Initialize CrossRef source."""
        super().__init__(timeout)
        self.email = email or "test@example.com"
        self.session: Optional[aiohttp.ClientSession] = None
    
    @property
    def name(self) -> str:
        """Get source name."""
        return "CrossRef"
    
    @property
    def supports_pdf(self) -> bool:
        """Check if source supports PDF download."""
        return True
    
    async def _get_session(self) -> aiohttp.ClientSession:
        """Get or create aiohttp session."""
        if self.session is None or self.session.closed:
            headers = {
                "User-Agent": f"Zhuai/2.0 (mailto:{self.email})"
            }
            self.session = aiohttp.ClientSession(
                timeout=aiohttp.ClientTimeout(total=self.timeout),
                headers=headers,
            )
        return self.session
    
    async def _get_unpaywall_pdf(self, doi: str) -> Optional[str]:
        """Get open access PDF URL from Unpaywall.
        
        Args:
            doi: DOI of the paper.
            
        Returns:
            PDF URL if available, None otherwise.
        """
        if not doi:
            return None
        
        try:
            session = await self._get_session()
            url = f"{self.UNPAYWALL_URL}/{doi}"
            params = {"email": self.email}
            
            async with session.get(url, params=params) as response:
                if response.status == 200:
                    data = await response.json()
                    
                    # Check for open access PDF
                    if data.get("is_oa"):
                        best_oa = data.get("best_oa_location") or {}
                        return best_oa.get("url_for_pdf") or best_oa.get("url")
                    
        except Exception:
            pass
        
        return None
    
    async def _make_request(
        self,
        endpoint: str,
        params: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:
        """Make request to CrossRef API."""
        session = await self._get_session()
        url = f"{self.BASE_URL}/{endpoint}"
        
        async with session.get(url, params=params) as response:
            response.raise_for_status()
            return await response.json()
    
    def _parse_paper(self, item: Dict[str, Any]) -> Paper:
        """Parse paper from API response."""
        title = item.get("title", [""])[0] if item.get("title") else ""
        
        authors = []
        for author in item.get("author", []):
            given = author.get("given", "")
            family = author.get("family", "")
            if family:
                authors.append(f"{given} {family}".strip())
        
        abstract = item.get("abstract")
        
        publication_date = None
        if "published" in item:
            date_parts = item["published"].get("date-parts", [[None]])
            if date_parts and date_parts[0]:
                parts = date_parts[0]
                try:
                    year = parts[0] if len(parts) > 0 else None
                    month = parts[1] if len(parts) > 1 else 1
                    day = parts[2] if len(parts) > 2 else 1
                    if year:
                        publication_date = datetime(int(year), int(month), int(day))
                except (ValueError, TypeError):
                    if year:
                        try:
                            publication_date = datetime(int(year), 1, 1)
                        except ValueError:
                            pass
        
        journal = None
        if "container-title" in item and item["container-title"]:
            journal = item["container-title"][0]
        
        volume = item.get("volume")
        issue = item.get("issue")
        pages = item.get("page")
        doi = item.get("DOI")
        
        citations = item.get("is-referenced-by-count", 0)
        
        keywords = []
        if "subject" in item:
            keywords = item["subject"] if isinstance(item["subject"], list) else [item["subject"]]
        
        article_type = item.get("type")
        issn = item.get("ISSN", [None])[0] if item.get("ISSN") else None
        publisher = item.get("publisher")
        language = item.get("language")
        
        pdf_url = None
        if "link" in item:
            for link in item["link"]:
                if link.get("content-type") == "application/pdf":
                    pdf_url = link.get("URL")
                    break
        
        source_url = None
        if doi:
            source_url = f"https://doi.org/{doi}"
        
        return Paper(
            title=title,
            authors=authors,
            abstract=abstract,
            publication_date=publication_date,
            journal=journal,
            volume=volume,
            issue=issue,
            pages=pages,
            doi=doi,
            pdf_url=pdf_url,
            source_url=source_url,
            citations=citations,
            keywords=keywords,
            source=self.name,
            article_type=article_type,
            issn=issn,
            publisher=publisher,
            language=language,
        )
    
    async def search(
        self,
        query: str,
        max_results: int = 100,
        **kwargs,
    ) -> List[Paper]:
        """Search CrossRef for papers and get open access PDFs."""
        params = {
            "query": query,
            "rows": max_results,
            "filter": "type:journal-article",  # Only journal articles
        }
        
        if kwargs.get("filter"):
            params["filter"] = kwargs["filter"]
        
        try:
            data = await self._make_request("works", params)
            items = data.get("message", {}).get("items", [])
            
            papers = []
            tasks = []
            
            for item in items:
                try:
                    paper = self._parse_paper(item)
                    
                    # Try to get open access PDF via Unpaywall if no direct PDF link
                    if not paper.pdf_url and paper.doi:
                        tasks.append(self._get_unpaywall_pdf(paper.doi))
                    else:
                        tasks.append(asyncio.sleep(0, result=paper.pdf_url))
                    
                    papers.append(paper)
                except Exception:
                    continue
            
            # Get PDF URLs in parallel
            if tasks:
                pdf_urls = await asyncio.gather(*tasks)
                
                for paper, pdf_url in zip(papers, pdf_urls):
                    if pdf_url and not paper.pdf_url:
                        paper.pdf_url = pdf_url
            
            return papers
            
        except Exception as e:
            print(f"Error searching CrossRef: {e}")
            return []
    
    async def get_paper_by_id(self, paper_id: str) -> Optional[Paper]:
        """Get a paper by DOI."""
        try:
            data = await self._make_request(f"works/{paper_id}")
            item = data.get("message", {})
            paper = self._parse_paper(item)
            
            # Try to get open access PDF
            if not paper.pdf_url and paper.doi:
                paper.pdf_url = await self._get_unpaywall_pdf(paper.doi)
            
            return paper
        except Exception:
            return None
    
    async def close(self) -> None:
        """Close aiohttp session."""
        if self.session and not self.session.closed:
            await self.session.close()