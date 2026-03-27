"""OpenAlex source for journal data - fetches 226,000+ journals for free."""

import asyncio
import aiohttp
import json
from datetime import datetime
from pathlib import Path
from typing import List, Optional, Dict, Any, Set
from dataclasses import dataclass, field, asdict

import sys
sys.path.insert(0, str(Path(__file__).parent.parent.parent))


@dataclass
class OpenAlexJournal:
    """Journal data from OpenAlex API."""
    issn_l: Optional[str] = None
    issn: List[str] = field(default_factory=list)
    display_name: str = ""
    publisher: Optional[str] = None
    homepage_url: Optional[str] = None
    country_code: Optional[str] = None
    works_count: int = 0
    cited_by_count: int = 0
    summary_stats: Optional[Dict] = None
    is_oa: bool = False
    is_in_doaj: bool = False
    type: str = "journal"
    topics: List[Dict] = field(default_factory=list)
    first_year: int = 0
    last_year: int = 0
    
    @property
    def citedness(self) -> float:
        """2-year mean citedness (similar to IF)."""
        if self.summary_stats:
            return self.summary_stats.get("2yr_mean_citedness", 0.0)
        return 0.0
    
    @property
    def h_index(self) -> int:
        if self.summary_stats:
            return self.summary_stats.get("h_index", 0)
        return 0
    
    @property
    def i10_index(self) -> int:
        if self.summary_stats:
            return self.summary_stats.get("i10_index", 0)
        return 0
    
    @property
    def primary_topic(self) -> Optional[str]:
        if self.topics:
            return self.topics[0].get("display_name")
        return None
    
    @property
    def subjects(self) -> List[str]:
        return [t.get("display_name", "") for t in self.topics[:5] if t.get("display_name")]


class OpenAlexFetcher:
    """Fetches journal data from OpenAlex API.
    
    OpenAlex provides free access to 226,000+ journals with:
    - ISSN, title, publisher
    - Citation metrics (2yr_mean_citedness, h_index, i10_index)
    - Open access status
    - Subject classification
    - Works count and citation counts
    """
    
    BASE_URL = "https://api.openalex.org"
    PER_PAGE = 200
    MAX_JOURNALS = 50000
    
    def __init__(self, timeout: int = 60):
        self.timeout = timeout
        self.session: Optional[aiohttp.ClientSession] = None
    
    async def __aenter__(self):
        timeout = aiohttp.ClientTimeout(total=self.timeout)
        self.session = aiohttp.ClientSession(timeout=timeout)
        return self
    
    async def __aexit__(self, *args):
        if self.session:
            await self.session.close()
    
    async def fetch_all_journals(
        self,
        min_works: int = 100,
        progress_callback=None,
        max_journals: int = None
    ) -> List[OpenAlexJournal]:
        """Fetch all journals with at least min_works papers.
        
        Args:
            min_works: Minimum number of works to be included
            progress_callback: Optional callback(current, total) for progress
            max_journals: Maximum number to fetch (None for all)
            
        Returns:
            List of OpenAlexJournal objects
        """
        if max_journals is None:
            max_journals = self.MAX_JOURNALS
        
        all_journals = []
        seen_issns: Set[str] = set()
        
        cursor = "*"
        page = 0
        
        while cursor:
            url = (
                f"{self.BASE_URL}/sources"
                f"?filter=type:journal"
                f"&per_page={self.PER_PAGE}"
                f"&cursor={cursor}"
            )
            
            try:
                async with self.session.get(url) as resp:
                    if resp.status != 200:
                        print(f"Error: {resp.status}")
                        break
                    
                    data = await resp.json()
                    
            except Exception as e:
                print(f"Request error: {e}")
                await asyncio.sleep(5)
                continue
            
            meta = data.get("meta", {})
            total = meta.get("count", 0)
            
            for item in data.get("results", []):
                issn_l = item.get("issn_l")
                
                if issn_l and issn_l in seen_issns:
                    continue
                
                journal = self._parse_journal(item)
                
                if journal.issn_l:
                    seen_issns.add(journal.issn_l)
                
                all_journals.append(journal)
                
                if len(all_journals) >= max_journals:
                    cursor = None
                    break
            
            page += 1
            cursor = data.get("meta", {}).get("next_cursor")
            
            if progress_callback:
                progress_callback(len(all_journals), min(total, max_journals))
            
            if len(all_journals) >= max_journals:
                break
            
            if page % 10 == 0:
                await asyncio.sleep(1)
        
        return all_journals[:max_journals]
    
    def _parse_journal(self, item: Dict) -> OpenAlexJournal:
        """Parse a journal from OpenAlex API response."""
        return OpenAlexJournal(
            issn_l=item.get("issn_l"),
            issn=item.get("issn", []),
            display_name=item.get("display_name", ""),
            publisher=item.get("publisher"),
            homepage_url=item.get("homepage_url"),
            country_code=item.get("country_code"),
            works_count=item.get("works_count", 0),
            cited_by_count=item.get("cited_by_count", 0),
            summary_stats=item.get("summary_stats"),
            is_oa=item.get("is_oa", False),
            is_in_doaj=item.get("is_in_doaj", False),
            type=item.get("type", "journal"),
            topics=item.get("topics", []),
            first_year=item.get("first_publication_year", 0),
            last_year=item.get("last_publication_year", 0),
        )
    
    async def fetch_journals_by_topic(
        self,
        topic_ids: List[str],
        min_works: int = 50
    ) -> List[OpenAlexJournal]:
        """Fetch journals filtered by topics."""
        if not self.session:
            raise RuntimeError("Must be used as context manager")
        
        topic_filter = "|".join(topic_ids)
        url = (
            f"{self.BASE_URL}/sources"
            f"?filter=type:journal,topics.id:{topic_filter},works_count:>{min_works}"
            f"&per_page={self.PER_PAGE}"
        )
        
        async with self.session.get(url) as resp:
            data = await resp.json()
        
        return [self._parse_journal(item) for item in data.get("results", [])]


async def fetch_comprehensive_journal_database(
    output_path: Path,
    min_works: int = 500,
    target_count: int = 5000,
    timeout: int = 120
) -> Dict[str, Any]:
    """Fetch a comprehensive journal database from OpenAlex.
    
    Args:
        output_path: Where to save the JSON file
        min_works: Minimum papers to be included
        target_count: Target number of journals to fetch
        timeout: Request timeout in seconds
        
    Returns:
        Statistics about the fetched database
    """
    print(f"Fetching up to {target_count} journals from OpenAlex...")
    print(f"Minimum works required: {min_works}")
    print()
    
    journals = []
    seen_issns: Set[str] = set()
    
    async with OpenAlexFetcher(timeout=timeout) as fetcher:
        cursor = "*"
        page = 0
        
        while len(journals) < target_count and cursor:
            url = (
                f"https://api.openalex.org/sources"
                f"?filter=type:journal,works_count:>{min_works}"
                f"&per_page=200"
                f"&cursor={cursor}"
                f"&select=id,issn_l,issn,display_name,publisher,homepage_url,"
                f"country_code,works_count,cited_by_count,summary_stats,"
                f"is_oa,is_in_doaj,type,topics,first_publication_year,"
                f"last_publication_year"
            )
            
            try:
                async with fetcher.session.get(url) as resp:
                    if resp.status != 200:
                        print(f"Error: {resp.status}, retrying...")
                        await asyncio.sleep(5)
                        continue
                    
                    data = await resp.json()
                    
            except Exception as e:
                print(f"Request error: {e}")
                await asyncio.sleep(5)
                continue
            
            for item in data.get("results", []):
                issn_l = item.get("issn_l")
                
                if not issn_l or issn_l in seen_issns:
                    continue
                
                seen_issns.add(issn_l)
                
                summary = item.get("summary_stats") or {}
                
                journal = {
                    "openalex_id": item.get("id", "").replace("https://openalex.org/", ""),
                    "title": item.get("display_name", ""),
                    "issn_l": issn_l,
                    "issn": item.get("issn", []),
                    "publisher": item.get("publisher"),
                    "url": item.get("homepage_url"),
                    "country_code": item.get("country_code"),
                    "works_count": item.get("works_count", 0),
                    "cited_by_count": item.get("cited_by_count", 0),
                    "citedness": summary.get("2yr_mean_citedness", 0.0),
                    "h_index": summary.get("h_index", 0),
                    "i10_index": summary.get("i10_index", 0),
                    "is_oa": item.get("is_oa", False),
                    "is_in_doaj": item.get("is_in_doaj", False),
                    "subjects": [t.get("display_name") for t in item.get("topics", [])[:5]],
                    "first_year": item.get("first_publication_year", 0),
                    "last_year": item.get("last_publication_year", 0),
                }
                
                journals.append(journal)
            
            page += 1
            cursor = data.get("meta", {}).get("next_cursor")
            
            if page % 5 == 0:
                print(f"  Fetched {len(journals)} journals so far...")
                await asyncio.sleep(0.5)
    
    print(f"\nTotal journals fetched: {len(journals)}")
    
    journals.sort(key=lambda x: x.get("citedness", 0), reverse=True)
    
    output_path.parent.mkdir(parents=True, exist_ok=True)
    
    db_data = {
        "description": f"Comprehensive journal database from OpenAlex ({len(journals)} journals)",
        "source": "OpenAlex API",
        "version": datetime.now().strftime("%Y.%m"),
        "total_journals": len(journals),
        "min_works_filter": min_works,
        "generated_at": datetime.now().isoformat(),
        "journals": journals,
    }
    
    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(db_data, f, indent=2, ensure_ascii=False)
    
    print(f"Saved to {output_path}")
    
    stats = compute_statistics(journals)
    return stats


def compute_statistics(journals: List[Dict]) -> Dict[str, Any]:
    """Compute statistics for journal database."""
    if not journals:
        return {}
    
    citedness_values = [j.get("citedness", 0) for j in journals]
    works_values = [j.get("works_count", 0) for j in journals]
    h_indexes = [j.get("h_index", 0) for j in journals]
    
    return {
        "total_journals": len(journals),
        "oa_journals": sum(1 for j in journals if j.get("is_oa")),
        "doaj_journals": sum(1 for j in journals if j.get("is_in_doaj")),
        "avg_citedness": sum(citedness_values) / len(citedness_values),
        "max_citedness": max(citedness_values),
        "min_citedness": min(citedness_values),
        "total_works": sum(works_values),
        "total_citations": sum(j.get("cited_by_count", 0) for j in journals),
        "top_10_journals": journals[:10],
    }


async def main():
    """Main entry point for fetching journal database."""
    output_dir = Path(__file__).parent / "data"
    output_dir.mkdir(parents=True, exist_ok=True)
    
    output_path = output_dir / "openalex_journals.json"
    
    stats = await fetch_comprehensive_journal_database(
        output_path=output_path,
        min_works=500,
        target_count=5000,
        timeout=120
    )
    
    print("\n=== Database Statistics ===")
    print(f"Total journals: {stats.get('total_journals', 0)}")
    print(f"Open Access: {stats.get('oa_journals', 0)}")
    print(f"DOAJ indexed: {stats.get('doaj_journals', 0)}")
    print(f"Average citedness: {stats.get('avg_citedness', 0):.3f}")
    print(f"Max citedness: {stats.get('max_citedness', 0):.3f}")


if __name__ == "__main__":
    asyncio.run(main())