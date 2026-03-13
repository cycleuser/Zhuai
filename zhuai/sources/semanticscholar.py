"""Semantic Scholar paper source with improved error handling."""

import asyncio
from datetime import datetime
from typing import List, Optional, Dict, Any
import aiohttp
from zhuai.models.paper import Paper
from zhuai.sources.base import BaseSource


class SemanticScholarSource(BaseSource):
    """Semantic Scholar paper source."""
    
    BASE_URL = "https://api.semanticscholar.org/graph/v1"
    
    def __init__(self, api_key: Optional[str] = None, timeout: int = 30):
        """Initialize Semantic Scholar source."""
        super().__init__(timeout)
        self.api_key = api_key
        self.session: Optional[aiohttp.ClientSession] = None
    
    @property
    def name(self) -> str:
        """Get source name."""
        return "Semantic Scholar"
    
    @property
    def supports_pdf(self) -> bool:
        """Check if source supports PDF download."""
        return True
    
    async def _get_session(self) -> aiohttp.ClientSession:
        """Get or create aiohttp session."""
        if self.session is None or self.session.closed:
            headers = {"User-Agent": "Zhuai/2.0"}
            if self.api_key:
                headers["x-api-key"] = self.api_key
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
        """Make request to Semantic Scholar API."""
        session = await self._get_session()
        url = f"{self.BASE_URL}/{endpoint}"
        
        async with session.get(url, params=params) as response:
            if response.status == 429:  # Rate limit
                await asyncio.sleep(1)
                return await self._make_request(endpoint, params)
            
            response.raise_for_status()
            return await response.json()
    
    def _parse_paper(self, item: Dict[str, Any]) -> Paper:
        """Parse paper from API response."""
        title = item.get("title", "")
        
        authors = []
        for author in item.get("authors", []):
            name = author.get("name", "")
            if name:
                authors.append(name)
        
        abstract = item.get("abstract")
        
        publication_date = None
        if item.get("year"):
            try:
                publication_date = datetime(int(item["year"]), 1, 1)
            except (ValueError, TypeError):
                pass
        
        journal = item.get("venue")
        doi = item.get("doi")
        pmid = item.get("pmid")
        arxiv_id = item.get("arxivId")
        
        citations = item.get("citationCount", 0)
        
        fields = item.get("fieldsOfStudy", [])
        keywords = fields if isinstance(fields, list) else []
        
        publication_types = item.get("publicationTypes", [])
        article_type = publication_types[0] if publication_types else None
        
        publication_venue = item.get("publicationVenue", {})
        issn = publication_venue.get("issn")
        publisher = publication_venue.get("publisher")
        
        pdf_url = None
        open_access = item.get("openAccessPdf", {})
        if open_access:
            pdf_url = open_access.get("url")
        
        source_url = f"https://www.semanticscholar.org/paper/{item.get('paperId', '')}"
        
        return Paper(
            title=title,
            authors=authors,
            abstract=abstract,
            publication_date=publication_date,
            journal=journal,
            doi=doi,
            pmid=pmid,
            arxiv_id=arxiv_id,
            pdf_url=pdf_url,
            source_url=source_url,
            citations=citations,
            keywords=keywords,
            source=self.name,
            article_type=article_type,
            issn=issn,
            publisher=publisher,
        )
    
    async def search(
        self,
        query: str,
        max_results: int = 100,
        **kwargs,
    ) -> List[Paper]:
        """Search Semantic Scholar for papers."""
        params = {
            "query": query,
            "limit": min(max_results, 100),  # API limit
            "fields": "paperId,title,authors,abstract,year,venue,doi,pmid,arxivId,citationCount,fieldsOfStudy,publicationTypes,publicationVenue,openAccessPdf",
        }
        
        if kwargs.get("year"):
            params["year"] = kwargs["year"]
        
        try:
            data = await self._make_request("paper/search", params)
            items = data.get("data", [])
            
            papers = []
            for item in items:
                try:
                    paper = self._parse_paper(item)
                    papers.append(paper)
                except Exception:
                    continue
            
            return papers
            
        except Exception as e:
            print(f"Error searching Semantic Scholar: {e}")
            return []
    
    async def get_paper_by_id(self, paper_id: str) -> Optional[Paper]:
        """Get a paper by Semantic Scholar ID, DOI, or other ID."""
        params = {
            "fields": "paperId,title,authors,abstract,year,venue,doi,pmid,arxivId,citationCount,fieldsOfStudy,publicationTypes,publicationVenue,openAccessPdf",
        }
        
        try:
            data = await self._make_request(f"paper/{paper_id}", params)
            return self._parse_paper(data)
        except Exception:
            return None
    
    async def close(self) -> None:
        """Close aiohttp session."""
        if self.session and not self.session.closed:
            await self.session.close()