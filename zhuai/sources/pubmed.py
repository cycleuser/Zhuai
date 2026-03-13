"""PubMed paper source."""

import asyncio
import json
from datetime import datetime
from typing import List, Optional, Dict, Any
from xml.etree import ElementTree
import aiohttp
from zhuai.models.paper import Paper
from zhuai.sources.base import BaseSource


class PubMedSource(BaseSource):
    """PubMed paper source."""
    
    BASE_URL = "https://eutils.ncbi.nlm.nih.gov/entrez/eutils"
    
    def __init__(self, api_key: Optional[str] = None, timeout: int = 30):
        """Initialize PubMed source.
        
        Args:
            api_key: NCBI API key for higher rate limits.
            timeout: Request timeout in seconds.
        """
        super().__init__(timeout)
        self.api_key = api_key
        self.session: Optional[aiohttp.ClientSession] = None
    
    @property
    def name(self) -> str:
        """Get source name."""
        return "PubMed"
    
    @property
    def supports_pdf(self) -> bool:
        """Check if source supports PDF download."""
        return False
    
    async def _get_session(self) -> aiohttp.ClientSession:
        """Get or create aiohttp session."""
        if self.session is None or self.session.closed:
            self.session = aiohttp.ClientSession(
                timeout=aiohttp.ClientTimeout(total=self.timeout),
                headers={"User-Agent": "Zhuai/2.0"},
            )
        return self.session
    
    async def _make_request(
        self,
        endpoint: str,
        params: Dict[str, Any],
    ) -> str:
        """Make request to NCBI API.
        
        Args:
            endpoint: API endpoint.
            params: Request parameters.
            
        Returns:
            Response text.
        """
        if self.api_key:
            params["api_key"] = self.api_key
        
        session = await self._get_session()
        url = f"{self.BASE_URL}/{endpoint}"
        
        async with session.get(url, params=params) as response:
            response.raise_for_status()
            return await response.text()
    
    def _parse_paper(self, article: ElementTree.Element) -> Paper:
        """Parse paper from XML element.
        
        Args:
            article: XML element.
            
        Returns:
            Paper object.
        """
        title_elem = article.find(".//ArticleTitle")
        title = title_elem.text if title_elem is not None else ""
        
        authors = []
        for author in article.findall(".//Author"):
            lastname = author.findtext("LastName", "")
            forename = author.findtext("ForeName", "")
            if lastname or forename:
                authors.append(f"{forename} {lastname}".strip())
        
        abstract_parts = []
        for abstract_text in article.findall(".//Abstract/AbstractText"):
            if abstract_text.text:
                label = abstract_text.get("Label", "")
                text = f"{label}: {abstract_text.text}" if label else abstract_text.text
                abstract_parts.append(text)
        abstract = "\n".join(abstract_parts) if abstract_parts else None
        
        journal_elem = article.find(".//Journal/Title")
        journal = journal_elem.text if journal_elem is not None else None
        
        pub_date_elem = article.find(".//PubDate")
        publication_date = None
        if pub_date_elem is not None:
            year = pub_date_elem.findtext("Year", "")
            month = pub_date_elem.findtext("Month", "01")
            day = pub_date_elem.findtext("Day", "01")
            
            month_map = {
                "Jan": "01", "Feb": "02", "Mar": "03", "Apr": "04",
                "May": "05", "Jun": "06", "Jul": "07", "Aug": "08",
                "Sep": "09", "Oct": "10", "Nov": "11", "Dec": "12",
            }
            month = month_map.get(month, month)
            
            try:
                publication_date = datetime.strptime(f"{year}-{month}-{day}", "%Y-%m-%d")
            except ValueError:
                if year:
                    try:
                        publication_date = datetime(int(year), 1, 1)
                    except ValueError:
                        pass
        
        doi = None
        for article_id in article.findall(".//ArticleId"):
            if article_id.get("IdType") == "doi":
                doi = article_id.text
                break
        
        pmid = article.findtext(".//PMID")
        
        volume = article.findtext(".//Journal/JournalIssue/Volume")
        issue = article.findtext(".//Journal/JournalIssue/Issue")
        pages = article.findtext(".//Pagination/MedlinePgn")
        
        keywords = []
        for keyword in article.findall(".//Keyword"):
            if keyword.text:
                keywords.append(keyword.text)
        
        article_type = None
        pub_types = article.findall(".//PublicationType")
        if pub_types:
            article_type = pub_types[0].text
        
        issn = article.findtext(".//ISSN")
        language = article.findtext(".//Language")
        
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
            pmid=pmid,
            pdf_url=None,
            source_url=f"https://pubmed.ncbi.nlm.nih.gov/{pmid}/" if pmid else None,
            citations=0,
            keywords=keywords,
            source=self.name,
            article_type=article_type,
            issn=issn,
            language=language,
        )
    
    async def search(
        self,
        query: str,
        max_results: int = 100,
        **kwargs,
    ) -> List[Paper]:
        """Search PubMed for papers.
        
        Args:
            query: Search query.
            max_results: Maximum number of results.
            **kwargs: Additional parameters.
            
        Returns:
            List of papers.
        """
        search_params = {
            "db": "pubmed",
            "term": query,
            "retmax": max_results,
            "retmode": "json",
            "usehistory": "y",
        }
        
        search_response = await self._make_request("esearch.fcgi", search_params)
        search_data = json.loads(search_response)
        
        id_list = search_data.get("esearchresult", {}).get("idlist", [])
        
        if not id_list:
            return []
        
        fetch_params = {
            "db": "pubmed",
            "id": ",".join(id_list),
            "retmode": "xml",
        }
        
        fetch_response = await self._make_request("efetch.fcgi", fetch_params)
        
        root = ElementTree.fromstring(fetch_response)
        papers = []
        
        for article in root.findall(".//PubmedArticle"):
            try:
                paper = self._parse_paper(article)
                papers.append(paper)
            except Exception:
                continue
        
        return papers
    
    async def get_paper_by_id(self, paper_id: str) -> Optional[Paper]:
        """Get a paper by PMID.
        
        Args:
            paper_id: PMID.
            
        Returns:
            Paper if found, None otherwise.
        """
        fetch_params = {
            "db": "pubmed",
            "id": paper_id,
            "retmode": "xml",
        }
        
        try:
            fetch_response = await self._make_request("efetch.fcgi", fetch_params)
            root = ElementTree.fromstring(fetch_response)
            article = root.find(".//PubmedArticle")
            
            if article:
                return self._parse_paper(article)
        except Exception:
            pass
        
        return None
    
    async def close(self) -> None:
        """Close aiohttp session."""
        if self.session and not self.session.closed:
            await self.session.close()