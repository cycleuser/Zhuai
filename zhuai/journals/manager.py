"""Journal database manager - combines multiple sources."""

import asyncio
import json
from datetime import datetime
from pathlib import Path
from typing import List, Optional, Dict, Any

from zhuai.journals.models import JournalInfo, JournalDatabase
from zhuai.journals.sources import (
    JournalSource,
    LetPubSource,
    CASPartitionSource,
    JCRSource,
    EISource,
    DOAJSource,
    CrossrefJournalSource,
)


class JournalManager:
    """Manager for fetching and combining journal data from multiple sources.
    
    Features:
    - Fetch from multiple sources in parallel
    - Deduplicate by ISSN
    - Merge information from different sources
    - Export to CSV/JSON
    - Search and filter functionality
    """
    
    DEFAULT_DATA_DIR = Path(__file__).parent / "data"
    
    def __init__(
        self,
        data_dir: Optional[str] = None,
        timeout: int = 30,
    ):
        self.data_dir = Path(data_dir) if data_dir else self.DEFAULT_DATA_DIR
        self.data_dir.mkdir(parents=True, exist_ok=True)
        self.timeout = timeout
        self.database = JournalDatabase()
        
        self.sources: Dict[str, JournalSource] = {
            "letpub": LetPubSource(timeout=timeout),
            "cas": CASPartitionSource(),
            "jcr": JCRSource(),
            "ei": EISource(),
            "doaj": DOAJSource(timeout=timeout),
            "crossref": CrossrefJournalSource(timeout=timeout),
        }
    
    async def fetch_all(self, **kwargs) -> JournalDatabase:
        """Fetch journals from all available sources."""
        tasks = []
        
        for name, source in self.sources.items():
            if name in ["letpub", "doaj", "crossref"]:
                tasks.append(self._fetch_source(name, source, **kwargs))
        
        results = await asyncio.gather(*tasks, return_exceptions=True)
        
        for result in results:
            if isinstance(result, list):
                for journal in result:
                    self._merge_journal(journal)
        
        self.database.journals.sort(key=lambda j: j.title)
        return self.database
    
    async def _fetch_source(self, name: str, source: JournalSource, **kwargs) -> List[JournalInfo]:
        """Fetch from a single source."""
        try:
            print(f"Fetching from {name}...")
            journals = await source.fetch_journals(**kwargs)
            print(f"  {name}: {len(journals)} journals")
            return journals
        except Exception as e:
            print(f"  {name}: Error - {e}")
            return []
    
    def _merge_journal(self, new_journal: JournalInfo) -> None:
        """Merge journal into database, combining info if exists."""
        existing = None
        
        if new_journal.issn:
            existing = self.database.find_by_issn(new_journal.issn)
        
        if not existing:
            for j in self.database.journals:
                if j.title.lower() == new_journal.title.lower():
                    existing = j
                    break
        
        if existing:
            if new_journal.jcr_quartile and not existing.jcr_quartile:
                existing.jcr_quartile = new_journal.jcr_quartile
            if new_journal.jcr_if and not existing.jcr_if:
                existing.jcr_if = new_journal.jcr_if
            if new_journal.cas_quartile and not existing.cas_quartile:
                existing.cas_quartile = new_journal.cas_quartile
            if new_journal.ei_indexed:
                existing.ei_indexed = True
            if new_journal.url and not existing.url:
                existing.url = new_journal.url
            if new_journal.publisher and not existing.publisher:
                existing.publisher = new_journal.publisher
        else:
            self.database.add(new_journal)
    
    def load_from_files(self) -> int:
        """Load journal data from local files."""
        total = 0
        
        for filename in ["cas_partition.json", "jcr.json", "ei.json", "journals.json", "comprehensive_journals.json", "openalex_journals.json"]:
            filepath = self.data_dir / filename
            if filepath.exists():
                try:
                    with open(filepath, "r", encoding="utf-8") as f:
                        data = json.load(f)
                    
                    journals_data = data.get("journals", [data] if "title" in data else [])
                    
                    for item in journals_data:
                        title = item.get("title") or item.get("display_name", "")
                        if not title:
                            continue
                        
                        issn = item.get("issn") or item.get("issn_l") or item.get("ISSN")
                        if isinstance(issn, list):
                            issn = issn[0] if issn else None
                        
                        eissn = item.get("eissn") or (item.get("issn")[1] if isinstance(item.get("issn"), list) and len(item.get("issn", [])) > 1 else None)
                        
                        citedness = item.get("citedness", 0)
                        jcr_if = item.get("jcr_if") or (citedness if citedness > 0 else None)
                        
                        journal = JournalInfo(
                            title=title,
                            issn=issn,
                            eissn=eissn,
                            publisher=item.get("publisher"),
                            url=item.get("url") or item.get("homepage_url"),
                            subject=", ".join(item.get("subjects", [])[:3]) if item.get("subjects") else item.get("jcr_category"),
                            jcr_quartile=item.get("jcr_quartile"),
                            jcr_if=jcr_if,
                            cas_quartile=item.get("cas_quartile"),
                            cas_top=item.get("cas_top", False),
                            ei_indexed=item.get("ei_indexed", False),
                            open_access=item.get("is_oa", item.get("open_access", False)),
                            source=item.get("source") or data.get("source", "OpenAlex"),
                            last_updated=datetime.now(),
                        )
                        self._merge_journal(journal)
                        total += 1
                        
                except Exception as e:
                    print(f"Error loading {filename}: {e}")
        
        print(f"Loaded {total} journals from files")
        return total
    
    def save_database(self, filename: str = "journal_database.json") -> None:
        """Save the current database to file."""
        filepath = self.data_dir / filename
        self.database.to_json(str(filepath))
    
    def search(
        self,
        keyword: str,
        quartile: Optional[str] = None,
        cas_quartile: Optional[str] = None,
        sci_only: bool = False,
        ei_only: bool = False,
    ) -> List[JournalInfo]:
        """Search journals with filters."""
        results = self.database.find_by_title(keyword)
        
        if quartile:
            results = [j for j in results if j.jcr_quartile == quartile.upper()]
        
        if cas_quartile:
            results = [j for j in results if j.cas_quartile == cas_quartile]
        
        if sci_only:
            results = [j for j in results if j.is_sci]
        
        if ei_only:
            results = [j for j in results if j.ei_indexed]
        
        return results
    
    def get_statistics(self) -> Dict[str, Any]:
        """Get database statistics."""
        return self.database.statistics()
    
    def get_quartile_summary(self) -> Dict[str, Dict[str, int]]:
        """Get summary by quartile."""
        return {
            "JCR": {
                "Q1": len(self.database.filter_by_quartile("Q1")),
                "Q2": len(self.database.filter_by_quartile("Q2")),
                "Q3": len(self.database.filter_by_quartile("Q3")),
                "Q4": len(self.database.filter_by_quartile("Q4")),
            },
            "CAS": {
                "1区": len(self.database.filter_by_cas_quartile("1区")),
                "2区": len(self.database.filter_by_cas_quartile("2区")),
                "3区": len(self.database.filter_by_cas_quartile("3区")),
                "4区": len(self.database.filter_by_cas_quartile("4区")),
            },
        }


def create_sample_database() -> JournalDatabase:
    """Create a sample journal database with common journals.
    
    This provides offline data for demonstration and basic use.
    """
    db = JournalDatabase()
    
    sample_journals = [
        JournalInfo(
            title="Nature",
            issn="0028-0836",
            eissn="1476-4687",
            publisher="Nature Publishing Group",
            url="https://www.nature.com/",
            jcr_quartile="Q1",
            jcr_if=64.8,
            jcr_category="Multidisciplinary Sciences",
            cas_quartile="1区",
            cas_top=True,
            ei_indexed=True,
            open_access=False,
            source="Sample Data",
            last_updated=datetime.now(),
        ),
        JournalInfo(
            title="Science",
            issn="0036-8075",
            eissn="1095-9203",
            publisher="American Association for the Advancement of Science",
            url="https://www.science.org/",
            jcr_quartile="Q1",
            jcr_if=56.9,
            jcr_category="Multidisciplinary Sciences",
            cas_quartile="1区",
            cas_top=True,
            ei_indexed=True,
            open_access=False,
            source="Sample Data",
            last_updated=datetime.now(),
        ),
        JournalInfo(
            title="Cell",
            issn="0092-8674",
            eissn="1097-4172",
            publisher="Cell Press",
            url="https://www.cell.com/",
            jcr_quartile="Q1",
            jcr_if=66.85,
            jcr_category="Biochemistry & Molecular Biology",
            cas_quartile="1区",
            cas_top=True,
            ei_indexed=False,
            open_access=False,
            source="Sample Data",
            last_updated=datetime.now(),
        ),
        JournalInfo(
            title="IEEE Transactions on Pattern Analysis and Machine Intelligence",
            issn="0162-8828",
            eissn="1939-3539",
            publisher="IEEE",
            url="https://ieeexplore.ieee.org/xpl/RecentIssue.jsp?punumber=34",
            jcr_quartile="Q1",
            jcr_if=24.314,
            jcr_category="Computer Science, Artificial Intelligence",
            cas_quartile="1区",
            cas_top=True,
            ei_indexed=True,
            subject="Computer Science",
            open_access=False,
            source="Sample Data",
            last_updated=datetime.now(),
        ),
        JournalInfo(
            title="Journal of the American Chemical Society",
            issn="0002-7863",
            eissn="1520-5126",
            publisher="American Chemical Society",
            url="https://pubs.acs.org/journal/jacsat",
            jcr_quartile="Q1",
            jcr_if=16.383,
            jcr_category="Chemistry, Multidisciplinary",
            cas_quartile="1区",
            cas_top=True,
            ei_indexed=True,
            subject="Chemistry",
            open_access=False,
            source="Sample Data",
            last_updated=datetime.now(),
        ),
        JournalInfo(
            title="Physical Review Letters",
            issn="0031-9007",
            eissn="1079-7114",
            publisher="American Physical Society",
            url="https://journals.aps.org/prl/",
            jcr_quartile="Q1",
            jcr_if=9.185,
            jcr_category="Physics, Multidisciplinary",
            cas_quartile="1区",
            cas_top=True,
            ei_indexed=True,
            subject="Physics",
            open_access=False,
            source="Sample Data",
            last_updated=datetime.now(),
        ),
        JournalInfo(
            title="The Lancet",
            issn="0140-6736",
            eissn="1474-547X",
            publisher="Elsevier",
            url="https://www.thelancet.com/",
            jcr_quartile="Q1",
            jcr_if=168.9,
            jcr_category="Medicine, General & Internal",
            cas_quartile="1区",
            cas_top=True,
            ei_indexed=False,
            subject="Medicine",
            open_access=False,
            source="Sample Data",
            last_updated=datetime.now(),
        ),
        JournalInfo(
            title="New England Journal of Medicine",
            issn="0028-4793",
            eissn="1533-4406",
            publisher="Massachusetts Medical Society",
            url="https://www.nejm.org/",
            jcr_quartile="Q1",
            jcr_if=158.5,
            jcr_category="Medicine, General & Internal",
            cas_quartile="1区",
            cas_top=True,
            ei_indexed=False,
            subject="Medicine",
            open_access=False,
            source="Sample Data",
            last_updated=datetime.now(),
        ),
        JournalInfo(
            title="Nature Machine Intelligence",
            issn="2522-5839",
            publisher="Nature Publishing Group",
            url="https://www.nature.com/natmachintell/",
            jcr_quartile="Q1",
            jcr_if=23.8,
            jcr_category="Computer Science, Artificial Intelligence",
            cas_quartile="1区",
            cas_top=False,
            ei_indexed=False,
            subject="Computer Science",
            open_access=True,
            source="Sample Data",
            last_updated=datetime.now(),
        ),
        JournalInfo(
            title="ACM Computing Surveys",
            issn="0360-0300",
            eissn="1557-7341",
            publisher="ACM",
            url="https://dl.acm.org/journal/csur",
            jcr_quartile="Q1",
            jcr_if=16.6,
            jcr_category="Computer Science, Theory & Methods",
            cas_quartile="2区",
            cas_top=False,
            ei_indexed=True,
            subject="Computer Science",
            open_access=False,
            source="Sample Data",
            last_updated=datetime.now(),
        ),
    ]
    
    for journal in sample_journals:
        db.add(journal)
    
    return db