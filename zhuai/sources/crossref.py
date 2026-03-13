"""CrossRef paper source."""

import asyncio
from datetime import datetime
from typing import List, Optional, Dict, Any
import aiohttp
from zhuai.models.paper import Paper
from zhuai.sources.base import BaseSource


class CrossRefSource(BaseSource):
    """CrossRef paper source."""
    
    BASE_URL = "https://api.crossref.org"
    
    def __init__(self, email: Optional[str] = None, timeout: int = 30):
        """Initialize CrossRef source.
        
        Args:
            email: Email for polite API access.
            timeout: Request timeout in seconds.
        """
        super().__init__(timeout)
        self.email = email
        self.session: Optional[aiohttp.ClientSession] = None
    
    @property
    def name(self) -> str:
        """Get source name."""
        return "CrossRef"
    
    @property
    def supports_pdf(self) -> bool:
        """Check if source supports PDF download."""
        return False
    
    async def _get_session(self) -> aiohttp.ClientSession:
        """Get or create aiohttp session."""
        if self.session is None or self.session.closed:
            headers = {
                "User-Agent": f"Zhuai/2.0 (mailto:{self.email})" if self.email else "Zhuai/2.0"
            }
            self.session = aiohttp.ClientSession(
                timeout=aiohttp.ClientTimeout(total=self.timeout),
                headers=headers,
            )
        return self.session
    
    async def _make_request(
        self,
        endpoint: str,
        params: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:
        """Make request to CrossRef API.
        
        Args:
            endpoint: API endpoint.
            params: Request parameters.
            
        Returns:
            Response JSON.
        """
        session = await self._get_session()
        url = f"{self.BASE_URL}/{endpoint}"
        
        async with session.get(url, params=params) as response:
            response.raise_for_status()
            return await response.json()
    
    def _parse_paper(self, item: Dict[str, Any]) -> Paper:
        """Parse paper from API response.
        
        Args:
            item: API response item.
            
        Returns:
            Paper object.
        """
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
        """Search CrossRef for papers.
        
        Args:
            query: Search query.
            max_results: Maximum number of results.
            **kwargs: Additional parameters.
            
        Returns:
            List of papers.
        """
        params = {
            "query": query,
            "rows": max_results,
        }
        
        if kwargs.get("filter"):
            params["filter"] = kwargs["filter"]
        
        try:
            data = await self._make_request("works", params)
            items = data.get("message", {}).get("items", [])
            
            papers = []
            for item in items:
                try:
                    paper = self._parse_paper(item)
                    papers.append(paper)
                except Exception:
                    continue
            
            return papers
            
        except Exception:
            return []
    
    async def get_paper_by_id(self, paper_id: str) -> Optional[Paper]:
        """Get a paper by DOI.
        
        Args:
            paper_id: DOI.
            
        Returns:
            Paper if found, None otherwise.
        """
        try:
            data = await self._make_request(f"works/{paper_id}")
            item = data.get("message", {})
            return self._parse_paper(item)
        except Exception:
            return None
    
    async def close(self) -> None:
        """Close aiohttp session."""
        if self.session and not self.session.closed:
            await self.session.close()