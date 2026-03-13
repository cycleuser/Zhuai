"""CNKI (China National Knowledge Infrastructure) source."""

import asyncio
import re
from datetime import datetime
from typing import List, Optional
from bs4 import BeautifulSoup
from zhuai.models.paper import Paper
from zhuai.sources.browser_base import BrowserSource


class CNKISource(BrowserSource):
    """CNKI academic source with browser automation."""
    
    BASE_URL = "https://www.cnki.net"
    SEARCH_URL = "https://www.cnki.net/search"
    
    @property
    def name(self) -> str:
        """Get source name."""
        return "CNKI"
    
    @property
    def supports_pdf(self) -> bool:
        """Check if source supports PDF download."""
        return True
    
    async def search(
        self,
        query: str,
        max_results: int = 100,
        **kwargs,
    ) -> List[Paper]:
        """Search CNKI for papers.
        
        Args:
            query: Search query.
            max_results: Maximum number of results.
            **kwargs: Additional parameters.
            
        Returns:
            List of papers.
        """
        await self._init_browser()
        
        search_url = f"{self.BASE_URL}/search?q={query}"
        await self._navigate(search_url)
        
        await asyncio.sleep(3)
        
        papers = []
        
        try:
            content = await self.page.content()
            soup = BeautifulSoup(content, "lxml")
            
            items = soup.find_all("div", class_="result")[:max_results]
            
            for item in items:
                try:
                    paper = self._parse_result(item)
                    if paper:
                        papers.append(paper)
                except Exception:
                    continue
                    
        except Exception as e:
            print(f"Error searching CNKI: {e}")
        
        return papers
    
    def _parse_result(self, item) -> Optional[Paper]:
        """Parse a single search result.
        
        Args:
            item: BeautifulSoup element.
            
        Returns:
            Paper object or None.
        """
        title_elem = item.find("a", class_="title")
        if not title_elem:
            return None
        
        title = title_elem.get_text(strip=True)
        
        authors = []
        author_elem = item.find("div", class_="author")
        if author_elem:
            authors = [a.strip() for a in author_elem.get_text(strip=True).split(";") if a.strip()]
        
        journal = None
        source_elem = item.find("div", class_="source")
        if source_elem:
            journal = source_elem.get_text(strip=True)
        
        year = None
        date_elem = item.find("div", class_="date")
        if date_elem:
            date_text = date_elem.get_text(strip=True)
            year_match = re.search(r"\d{4}", date_text)
            if year_match:
                year = int(year_match.group())
        
        abstract = None
        abstract_elem = item.find("div", class_="abstract")
        if abstract_elem:
            abstract = abstract_elem.get_text(strip=True)
        
        pdf_url = None
        pdf_elem = item.find("a", class_="download")
        if pdf_elem and pdf_elem.get("href"):
            pdf_url = pdf_elem["href"]
            if not pdf_url.startswith("http"):
                pdf_url = self.BASE_URL + pdf_url
        
        source_url = None
        if title_elem and title_elem.get("href"):
            source_url = title_elem["href"]
            if not source_url.startswith("http"):
                source_url = self.BASE_URL + source_url
        
        publication_date = datetime(year, 1, 1) if year else None
        
        return Paper(
            title=title,
            authors=authors,
            abstract=abstract,
            publication_date=publication_date,
            journal=journal,
            pdf_url=pdf_url,
            source_url=source_url,
            citations=0,
            source=self.name,
            language="zh",
        )
    
    async def get_paper_by_id(self, paper_id: str) -> Optional[Paper]:
        """Get paper by ID.
        
        Args:
            paper_id: Paper identifier.
            
        Returns:
            Paper if found, None otherwise.
        """
        return None