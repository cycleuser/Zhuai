"""PubMed paper source with PMC open access support."""

import asyncio
import json
import time
from datetime import datetime
from typing import List, Optional, Dict, Any
from xml.etree import ElementTree
import requests
from zhuai.models.paper import Paper
from zhuai.sources.base import BaseSource


class PubMedSource(BaseSource):
    """PubMed paper source with PMC open access."""
    
    BASE_URL = "https://eutils.ncbi.nlm.nih.gov/entrez/eutils"
    PMC_URL = "https://www.ncbi.nlm.nih.gov/pmc/utils/oa/oa_fcgi.fcgi"
    RATE_LIMIT_DELAY = 0.4
    
    def __init__(self, api_key: Optional[str] = None, timeout: int = 30):
        """Initialize PubMed source."""
        super().__init__(timeout)
        self.api_key = api_key
        self._last_request_time: float = 0
    
    @property
    def name(self) -> str:
        """Get source name."""
        return "PubMed"
    
    @property
    def supports_pdf(self) -> bool:
        """Check if source supports PDF download."""
        return True
    
    def _make_request(
        self,
        endpoint: str,
        params: Dict[str, Any],
    ) -> str:
        """Make request to NCBI API."""
        if self.api_key:
            params["api_key"] = self.api_key
        
        url = f"{self.BASE_URL}/{endpoint}"
        
        elapsed = time.time() - self._last_request_time
        if elapsed < self.RATE_LIMIT_DELAY:
            time.sleep(self.RATE_LIMIT_DELAY - elapsed)
        
        self._last_request_time = time.time()
        response = requests.get(url, params=params, timeout=self.timeout)
        response.raise_for_status()
        return response.text
    
    def _get_pmc_pdf_url(self, pmcid: str) -> Optional[str]:
        """Get PDF URL from PMC for open access articles.
        
        Args:
            pmcid: PMC ID (e.g., PMC1234567).
            
        Returns:
            PDF URL if available, None otherwise.
        """
        if not pmcid:
            return None
        
        try:
            params = {"id": pmcid}
            response = requests.get(self.PMC_URL, params=params, timeout=self.timeout)
            
            if response.status_code == 200:
                root = ElementTree.fromstring(response.text)
                
                for record in root.findall(".//record"):
                    for link in record.findall("link"):
                        if link.get("format") == "pdf":
                            return link.get("href")
        except Exception:
            pass
        
        return None
    
    def _parse_paper(self, article: ElementTree.Element) -> Optional[Paper]:
        """Parse paper from XML element."""
        title_elem = article.find(".//ArticleTitle")
        title = title_elem.text if title_elem is not None else ""
        
        if not title:
            return None
        
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
            arxiv_id=pmcid,
            pdf_url=None,
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
        def _search() -> List[Paper]:
            search_params = {
                "db": "pubmed",
                "term": f"{query} AND open access[filter]",
                "retmax": max_results,
                "retmode": "json",
                "usehistory": "y",
            }
            
            try:
                search_response = self._make_request("esearch.fcgi", search_params)
                search_data = json.loads(search_response)
                
                id_list = search_data.get("esearchresult", {}).get("idlist", [])
                
                if not id_list:
                    search_params["term"] = query
                    search_response = self._make_request("esearch.fcgi", search_params)
                    search_data = json.loads(search_response)
                    id_list = search_data.get("esearchresult", {}).get("idlist", [])
                
                if not id_list:
                    return []
                
                fetch_params = {
                    "db": "pubmed",
                    "id": ",".join(id_list[:max_results]),
                    "retmode": "xml",
                }
                
                fetch_response = self._make_request("efetch.fcgi", fetch_params)
                
                root = ElementTree.fromstring(fetch_response)
                papers = []
                pmcids_to_check = []
                
                for article in root.findall(".//PubmedArticle"):
                    try:
                        paper = self._parse_paper(article)
                        if paper:
                            papers.append(paper)
                            
                            if paper.arxiv_id:
                                pmcids_to_check.append((paper, paper.arxiv_id))
                    except Exception:
                        continue
                
                for paper, pmcid in pmcids_to_check:
                    pdf_url = self._get_pmc_pdf_url(pmcid)
                    if pdf_url:
                        paper.pdf_url = pdf_url
                
                return papers
                
            except Exception as e:
                print(f"Error searching PubMed: {e}")
                return []
        
        loop = asyncio.get_event_loop()
        return await loop.run_in_executor(None, _search)
    
    async def get_paper_by_id(self, paper_id: str) -> Optional[Paper]:
        """Get a paper by PMID."""
        def _get() -> Optional[Paper]:
            fetch_params = {
                "db": "pubmed",
                "id": paper_id,
                "retmode": "xml",
            }
            
            try:
                fetch_response = self._make_request("efetch.fcgi", fetch_params)
                root = ElementTree.fromstring(fetch_response)
                article = root.find(".//PubmedArticle")
                
                if article:
                    paper = self._parse_paper(article)
                    
                    if paper and paper.arxiv_id:
                        paper.pdf_url = self._get_pmc_pdf_url(paper.arxiv_id)
                    
                    return paper
            except Exception:
                pass
            
            return None
        
        loop = asyncio.get_event_loop()
        return await loop.run_in_executor(None, _get)
    
    async def close(self) -> None:
        """Close resources."""
        pass