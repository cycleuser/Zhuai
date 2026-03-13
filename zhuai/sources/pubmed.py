"""PubMed paper source with PMC open access support."""

import asyncio
import json
from datetime import datetime
from typing import List, Optional, Dict, Any
from xml.etree import ElementTree
import aiohttp
from zhuai.models.paper import Paper
from zhuai.sources.base import BaseSource


class PubMedSource(BaseSource):
    """PubMed paper source with PMC open access."""
    
    BASE_URL = "https://eutils.ncbi.nlm.nih.gov/entrez/eutils"
    PMC_URL = "https://www.ncbi.nlm.nih.gov/pmc/utils/oa/oa_fcgi.fcgi"
    
    def __init__(self, api_key: Optional[str] = None, timeout: int = 30):
        """Initialize PubMed source."""
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
        return True
    
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
        """Make request to NCBI API."""
        if self.api_key:
            params["api_key"] = self.api_key
        
        session = await self._get_session()
        url = f"{self.BASE_URL}/{endpoint}"
        
        async with session.get(url, params=params) as response:
            response.raise_for_status()
            return await response.text()
    
    async def _get_pmc_pdf_url(self, pmcid: str) -> Optional[str]:
        """Get PDF URL from PMC for open access articles.
        
        Args:
            pmcid: PMC ID (e.g., PMC1234567).
            
        Returns:
            PDF URL if available, None otherwise.
        """
        if not pmcid:
            return None
        
        try:
            session = await self._get_session()
            params = {"id": pmcid}
            
            async with session.get(self.PMC_URL, params=params) as response:
                if response.status == 200:
                    text = await response.text()
                    root = ElementTree.fromstring(text)
                    
                    for record in root.findall(".//record"):
                        for link in record.findall("link"):
                            if link.get("format") == "pdf":
                                return link.get("href")
        except Exception:
            pass
        
        return None
    
    def _parse_paper(self, article: ElementTree.Element) -> Paper:
        """Parse paper from XML element."""
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
        pmid = None
        pmcid = None
        
        for article_id in article.findall(".//ArticleId"):
            id_type = article_id.get("IdType")
            if id_type == "doi":
                doi = article_id.text
            elif id_type == "pmid":
                pmid = article_id.text
            elif id_type == "pmc":
                pmcid = article_id.text
        
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
        
        source_url = f"https://pubmed.ncbi.nlm.nih.gov/{pmid}/" if pmid else None
        
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
            arxiv_id=pmcid,  # Store PMCID temporarily
            pdf_url=None,  # Will be filled later
            source_url=source_url,
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
        """Search PubMed for papers."""
        # Search for articles
        search_params = {
            "db": "pubmed",
            "term": f"{query} AND open access[filter]",
            "retmax": max_results,
            "retmode": "json",
            "usehistory": "y",
        }
        
        try:
            search_response = await self._make_request("esearch.fcgi", search_params)
            search_data = json.loads(search_response)
            
            id_list = search_data.get("esearchresult", {}).get("idlist", [])
            
            if not id_list:
                # Try without open access filter
                search_params["term"] = query
                search_response = await self._make_request("esearch.fcgi", search_params)
                search_data = json.loads(search_response)
                id_list = search_data.get("esearchresult", {}).get("idlist", [])
            
            if not id_list:
                return []
            
            # Fetch article details
            fetch_params = {
                "db": "pubmed",
                "id": ",".join(id_list[:max_results]),
                "retmode": "xml",
            }
            
            fetch_response = await self._make_request("efetch.fcgi", fetch_params)
            
            root = ElementTree.fromstring(fetch_response)
            papers = []
            pmcids_to_check = []
            
            for article in root.findall(".//PubmedArticle"):
                try:
                    paper = self._parse_paper(article)
                    papers.append(paper)
                    
                    # Collect PMCID for PDF check
                    if paper.arxiv_id:  # PMCID stored here
                        pmcids_to_check.append((paper, paper.arxiv_id))
                except Exception:
                    continue
            
            # Get PMC PDF URLs in parallel
            if pmcids_to_check:
                tasks = [self._get_pmc_pdf_url(pmcid) for _, pmcid in pmcids_to_check]
                pdf_urls = await asyncio.gather(*tasks)
                
                for (paper, _), pdf_url in zip(pmcids_to_check, pdf_urls):
                    if pdf_url:
                        paper.pdf_url = pdf_url
            
            # Clean up PMCID from arxiv_id field
            for paper in papers:
                if paper.arxiv_id and paper.arxiv_id.startswith("PMC"):
                    # Move PMCID to proper field if needed
                    pass
            
            return papers
            
        except Exception as e:
            print(f"Error searching PubMed: {e}")
            return []
    
    async def get_paper_by_id(self, paper_id: str) -> Optional[Paper]:
        """Get a paper by PMID."""
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
                paper = self._parse_paper(article)
                
                # Get PMC PDF if available
                if paper.arxiv_id:  # PMCID
                    paper.pdf_url = await self._get_pmc_pdf_url(paper.arxiv_id)
                
                return paper
        except Exception:
            pass
        
        return None
    
    async def close(self) -> None:
        """Close aiohttp session."""
        if self.session and not self.session.closed:
            await self.session.close()