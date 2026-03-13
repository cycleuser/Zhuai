"""Semantic Scholar paper source with improved error handling."""

import asyncio
import time
from datetime import datetime
from typing import List, Optional, Dict, Any
import requests
from zhuai.models.paper import Paper
from zhuai.sources.base import BaseSource


class SemanticScholarSource(BaseSource):
    """Semantic Scholar paper source."""
    
    BASE_URL = "https://api.semanticscholar.org/graph/v1"
    RATE_LIMIT_DELAY = 1.0
    
    def __init__(self, api_key: Optional[str] = None, timeout: int = 30):
        """Initialize Semantic Scholar source."""
        super().__init__(timeout)
        self.api_key = api_key
        self._last_request_time: float = 0
    
    @property
    def name(self) -> str:
        """Get source name."""
        return "Semantic Scholar"
    
    @property
    def supports_pdf(self) -> bool:
        """Check if source supports PDF download."""
        return True
    
    def _make_request(
        self,
        endpoint: str,
        params: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:
        """Make request to Semantic Scholar API."""
        url = f"{self.BASE_URL}/{endpoint}"
        
        headers = {"User-Agent": "Zhuai/2.0"}
        if self.api_key:
            headers["x-api-key"] = self.api_key
        
        elapsed = time.time() - self._last_request_time
        if elapsed < self.RATE_LIMIT_DELAY:
            time.sleep(self.RATE_LIMIT_DELAY - elapsed)
        
        self._last_request_time = time.time()
        
        response = requests.get(url, params=params, headers=headers, timeout=self.timeout)
        
        if response.status_code == 429:
            retry_after = int(response.headers.get("Retry-After", 5))
            time.sleep(retry_after)
            return self._make_request(endpoint, params)
        
        response.raise_for_status()
        return response.json()
    
    def _parse_paper(self, item: Dict[str, Any]) -> Optional[Paper]:
        """Parse paper from API response."""
        title = item.get("title", "")
        
        if not title:
            return None
        
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
        def _search() -> List[Paper]:
            params = {
                "query": query,
                "limit": min(max_results, 100),
                "fields": "paperId,title,authors,abstract,year,venue,doi,pmid,arxivId,citationCount,fieldsOfStudy,publicationTypes,publicationVenue,openAccessPdf",
            }
            
            if kwargs.get("year"):
                params["year"] = kwargs["year"]
            
            try:
                data = self._make_request("paper/search", params)
                items = data.get("data", [])
                
                papers = []
                for item in items:
                    try:
                        paper = self._parse_paper(item)
                        if paper:
                            papers.append(paper)
                    except Exception:
                        continue
                
                return papers
                
            except Exception as e:
                print(f"Error searching Semantic Scholar: {e}")
                return []
        
        loop = asyncio.get_event_loop()
        return await loop.run_in_executor(None, _search)
    
    async def get_paper_by_id(self, paper_id: str) -> Optional[Paper]:
        """Get a paper by Semantic Scholar ID, DOI, or other ID."""
        def _get() -> Optional[Paper]:
            params = {
                "fields": "paperId,title,authors,abstract,year,venue,doi,pmid,arxivId,citationCount,fieldsOfStudy,publicationTypes,publicationVenue,openAccessPdf",
            }
            
            try:
                data = self._make_request(f"paper/{paper_id}", params)
                return self._parse_paper(data)
            except Exception:
                return None
        
        loop = asyncio.get_event_loop()
        return await loop.run_in_executor(None, _get)
    
    async def close(self) -> None:
        """Close resources."""
        pass