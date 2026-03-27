"""Journal data sources for fetching SCI/EI information."""

import asyncio
import json
import re
from abc import ABC, abstractmethod
from typing import List, Optional, Dict, Any
from datetime import datetime
from pathlib import Path
from zhuai.journals.models import JournalInfo, JournalDatabase


class JournalSource(ABC):
    """Base class for journal data sources."""
    
    @property
    @abstractmethod
    def name(self) -> str:
        """Source name."""
        pass
    
    @abstractmethod
    async def fetch_journals(self, **kwargs) -> List[JournalInfo]:
        """Fetch journals from source."""
        pass


class LetPubSource(JournalSource):
    """LetPub journal database source.
    
    URL: https://www.letpub.com.cn/
    Contains SCI journal information, impact factors, CAS partitions.
    """
    
    BASE_URL = "https://www.letpub.com.cn"
    SEARCH_URL = "https://www.letpub.com.cn/index.php?page=journalapp&searchfield=name"
    
    def __init__(self, timeout: int = 30):
        self.timeout = timeout
    
    @property
    def name(self) -> str:
        return "LetPub"
    
    async def fetch_journals(self, keyword: str = "", max_results: int = 100) -> List[JournalInfo]:
        """Fetch journals from LetPub.
        
        Note: This requires browser automation due to anti-scraping measures.
        Use the static data file instead for offline access.
        """
        try:
            from playwright.async_api import async_playwright
            from playwright_stealth import Stealth
            
            journals = []
            
            async with async_playwright() as p:
                browser = await p.chromium.launch(headless=True)
                page = await browser.new_page()
                await Stealth().apply_stealth_async(page)
                
                url = f"{self.SEARCH_URL}&searchword={keyword}" if keyword else self.SEARCH_URL
                await page.goto(url, timeout=self.timeout * 1000)
                await asyncio.sleep(3)
                
                content = await page.content()
                journals = self._parse_search_results(content)
                
                await browser.close()
            
            return journals[:max_results]
            
        except Exception as e:
            print(f"LetPub fetch error: {e}")
            return []
    
    def _parse_search_results(self, html: str) -> List[JournalInfo]:
        """Parse LetPub search results."""
        from bs4 import BeautifulSoup
        
        journals = []
        soup = BeautifulSoup(html, "lxml")
        
        rows = soup.select("table tr")
        for row in rows[1:]:
            try:
                cells = row.select("td")
                if len(cells) >= 8:
                    title = cells[0].get_text(strip=True)
                    issn = cells[1].get_text(strip=True)
                    if_line = cells[2].get_text(strip=True)
                    cas_partition = cells[3].get_text(strip=True)
                    jcr_partition = cells[4].get_text(strip=True)
                    
                    journal = JournalInfo(
                        title=title,
                        issn=issn if "-" in issn else None,
                        jcr_if=float(if_line) if if_line and if_line.replace(".", "").isdigit() else None,
                        cas_quartile=cas_partition if "区" in cas_partition else None,
                        jcr_quartile=jcr_partition if "Q" in jcr_partition else None,
                        source=self.name,
                        last_updated=datetime.now(),
                    )
                    journals.append(journal)
            except Exception:
                continue
        
        return journals


class CASPartitionSource(JournalSource):
    """CAS (Chinese Academy of Sciences) journal partition source.
    
    The official CAS partition table is published annually.
    Data source: https://www.fenqubiao.com/
    """
    
    def __init__(self, data_file: Optional[str] = None):
        self.data_file = data_file
    
    @property
    def name(self) -> str:
        return "CAS Partition"
    
    async def fetch_journals(self, **kwargs) -> List[JournalInfo]:
        """Fetch CAS partition data.
        
        For offline use, load from JSON data file.
        """
        if self.data_file and Path(self.data_file).exists():
            return self._load_from_file(self.data_file)
        return []
    
    def _load_from_file(self, filepath: str) -> List[JournalInfo]:
        """Load CAS partition data from JSON file."""
        journals = []
        
        with open(filepath, "r", encoding="utf-8") as f:
            data = json.load(f)
            
        for item in data.get("journals", []):
            journal = JournalInfo(
                title=item.get("title"),
                issn=item.get("issn"),
                publisher=item.get("publisher"),
                cas_quartile=item.get("cas_quartile"),
                cas_category=item.get("cas_category"),
                cas_top=item.get("cas_top", False),
                cas_year=item.get("year", 2023),
                source="CAS Partition",
                last_updated=datetime.now(),
            )
            journals.append(journal)
        
        return journals


class JCRSource(JournalSource):
    """JCR (Journal Citation Reports) source.
    
    JCR provides impact factors and quartile rankings.
    Official: https://jcr.clarivate.com/
    """
    
    def __init__(self, data_file: Optional[str] = None):
        self.data_file = data_file
    
    @property
    def name(self) -> str:
        return "JCR"
    
    async def fetch_journals(self, **kwargs) -> List[JournalInfo]:
        """Fetch JCR data."""
        if self.data_file and Path(self.data_file).exists():
            return self._load_from_file(self.data_file)
        return []
    
    def _load_from_file(self, filepath: str) -> List[JournalInfo]:
        """Load JCR data from JSON file."""
        journals = []
        
        with open(filepath, "r", encoding="utf-8") as f:
            data = json.load(f)
            
        for item in data.get("journals", []):
            quartile = item.get("jcr_quartile", "")
            if quartile in ["Q1", "Q2", "Q3", "Q4"]:
                journal = JournalInfo(
                    title=item.get("title"),
                    issn=item.get("issn"),
                    eissn=item.get("eissn"),
                    publisher=item.get("publisher"),
                    url=item.get("url"),
                    jcr_quartile=quartile,
                    jcr_if=item.get("impact_factor"),
                    jcr_category=item.get("category"),
                    jcr_rank=item.get("rank"),
                    jcr_year=item.get("year", 2023),
                    source="JCR",
                    last_updated=datetime.now(),
                )
                journals.append(journal)
        
        return journals


class EISource(JournalSource):
    """EI (Engineering Index) source.
    
    EI Compendex journal list.
    """
    
    def __init__(self, data_file: Optional[str] = None):
        self.data_file = data_file
    
    @property
    def name(self) -> str:
        return "EI"
    
    async def fetch_journals(self, **kwargs) -> List[JournalInfo]:
        """Fetch EI journal data."""
        if self.data_file and Path(self.data_file).exists():
            return self._load_from_file(self.data_file)
        return []
    
    def _load_from_file(self, filepath: str) -> List[JournalInfo]:
        """Load EI data from JSON file."""
        journals = []
        
        with open(filepath, "r", encoding="utf-8") as f:
            data = json.load(f)
            
        for item in data.get("journals", []):
            journal = JournalInfo(
                title=item.get("title"),
                issn=item.get("issn"),
                publisher=item.get("publisher"),
                url=item.get("url"),
                ei_indexed=True,
                ei_category=item.get("category"),
                subject=item.get("subject"),
                source="EI",
                last_updated=datetime.now(),
            )
            journals.append(journal)
        
        return journals


class DOAJSource(JournalSource):
    """DOAJ (Directory of Open Access Journals) source.
    
    Provides open access journal information with official URLs.
    API: https://doaj.org/api/docs
    """
    
    API_URL = "https://doaj.org/api/search/journals"
    
    def __init__(self, timeout: int = 30):
        self.timeout = timeout
    
    @property
    def name(self) -> str:
        return "DOAJ"
    
    async def fetch_journals(self, keyword: str = "", max_results: int = 100) -> List[JournalInfo]:
        """Fetch journals from DOAJ API."""
        journals = []
        
        try:
            import httpx
            
            params = {
                "q": keyword or "*",
                "page": 1,
                "pageSize": min(max_results, 100),
            }
            
            async with httpx.AsyncClient(timeout=self.timeout) as client:
                response = await client.get(self.API_URL, params=params)
                response.raise_for_status()
                data = response.json()
            
            for item in data.get("results", []):
                bibjson = item.get("bibjson", {})
                journal = JournalInfo(
                    title=bibjson.get("title"),
                    issn=bibjson.get("identifier", {}).get("issn"),
                    eissn=bibjson.get("identifier", {}).get("eissn"),
                    publisher=bibjson.get("publisher"),
                    url=bibjson.get("link", [{}])[0].get("url") if bibjson.get("link") else None,
                    subject=bibjson.get("subject", [{}])[0].get("term") if bibjson.get("subject") else None,
                    open_access=True,
                    source="DOAJ",
                    last_updated=datetime.now(),
                )
                journals.append(journal)
                
        except Exception as e:
            print(f"DOAJ fetch error: {e}")
        
        return journals


class CrossrefJournalSource(JournalSource):
    """Crossref journal metadata source.
    
    API: https://api.crossref.org/works
    """
    
    API_URL = "https://api.crossref.org/journals"
    
    def __init__(self, timeout: int = 30):
        self.timeout = timeout
    
    @property
    def name(self) -> str:
        return "Crossref"
    
    async def fetch_journals(self, issn: str = "", max_results: int = 100) -> List[JournalInfo]:
        """Fetch journal info from Crossref."""
        journals = []
        
        try:
            import httpx
            
            headers = {"User-Agent": "Zhuai/2.0 (mailto:cycleuser@gmail.com)"}
            
            async with httpx.AsyncClient(timeout=self.timeout) as client:
                if issn:
                    url = f"{self.API_URL}/{issn}"
                    response = await client.get(url, headers=headers)
                    response.raise_for_status()
                    data = response.json()
                    
                    item = data.get("message", {})
                    journal = JournalInfo(
                        title=item.get("title"),
                        issn=item.get("ISSN", [None])[0],
                        publisher=item.get("publisher"),
                        subject=item.get("subject"),
                        source="Crossref",
                        last_updated=datetime.now(),
                    )
                    journals.append(journal)
                else:
                    params = {"rows": max_results}
                    response = await client.get(self.API_URL, params=params, headers=headers)
                    response.raise_for_status()
                    data = response.json()
                    
                    for item in data.get("message", {}).get("items", []):
                        journal = JournalInfo(
                            title=item.get("title"),
                            issn=item.get("ISSN", [None])[0],
                            publisher=item.get("publisher"),
                            subject=item.get("subject"),
                            source="Crossref",
                            last_updated=datetime.now(),
                        )
                        journals.append(journal)
                        
        except Exception as e:
            print(f"Crossref fetch error: {e}")
        
        return journals