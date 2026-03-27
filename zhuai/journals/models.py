"""Journal information models."""

from dataclasses import dataclass, field
from typing import Optional, List, Dict, Any
from datetime import datetime


@dataclass
class JournalInfo:
    """Comprehensive journal information.
    
    Attributes:
        title: Journal title
        issn: ISSN number
        eissn: E-ISSN number
        publisher: Publisher name
        url: Official website URL
        subject: Subject category
        keywords: Keywords/tags
        
        SCI/JCR information:
        jcr_quartile: JCR Q1/Q2/Q3/Q4
        jcr_if: Journal Impact Factor
        jcr_category: JCR category name
        jcr_rank: Rank in category
        
        CAS information (Chinese Academy of Sciences):
        cas_quartile: CAS 1区/2区/3区/4区
        cas_category: CAS category name
        cas_top: Is top journal
        
        EI information:
        ei_indexed: Is EI indexed
        ei_category: EI category
        
        Submission info:
        submission_url: Submission system URL
        review_time: Average review time (days)
        acceptance_rate: Acceptance rate
        publication_fee: APC/APF
        
        Additional:
        open_access: Is open access
        abstracted_in: Other databases indexing
        notes: Additional notes
    """
    
    title: str
    issn: Optional[str] = None
    eissn: Optional[str] = None
    publisher: Optional[str] = None
    url: Optional[str] = None
    subject: Optional[str] = None
    keywords: List[str] = field(default_factory=list)
    
    jcr_quartile: Optional[str] = None
    jcr_if: Optional[float] = None
    jcr_category: Optional[str] = None
    jcr_rank: Optional[str] = None
    jcr_year: Optional[int] = None
    
    cas_quartile: Optional[str] = None
    cas_category: Optional[str] = None
    cas_top: bool = False
    cas_year: Optional[int] = None
    
    ei_indexed: bool = False
    ei_category: Optional[str] = None
    
    submission_url: Optional[str] = None
    review_time: Optional[int] = None
    acceptance_rate: Optional[float] = None
    publication_fee: Optional[str] = None
    
    open_access: bool = False
    abstracted_in: List[str] = field(default_factory=list)
    notes: Optional[str] = None
    
    source: Optional[str] = None
    last_updated: Optional[datetime] = None
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            "title": self.title,
            "issn": self.issn,
            "eissn": self.eissn,
            "publisher": self.publisher,
            "url": self.url,
            "subject": self.subject,
            "keywords": "; ".join(self.keywords),
            "jcr_quartile": self.jcr_quartile,
            "jcr_if": self.jcr_if,
            "jcr_category": self.jcr_category,
            "jcr_rank": self.jcr_rank,
            "jcr_year": self.jcr_year,
            "cas_quartile": self.cas_quartile,
            "cas_category": self.cas_category,
            "cas_top": self.cas_top,
            "cas_year": self.cas_year,
            "ei_indexed": self.ei_indexed,
            "ei_category": self.ei_category,
            "submission_url": self.submission_url,
            "review_time": self.review_time,
            "acceptance_rate": self.acceptance_rate,
            "publication_fee": self.publication_fee,
            "open_access": self.open_access,
            "abstracted_in": "; ".join(self.abstracted_in),
            "notes": self.notes,
            "source": self.source,
            "last_updated": self.last_updated.isoformat() if self.last_updated else None,
        }
    
    @property
    def is_sci(self) -> bool:
        """Check if journal is SCI indexed."""
        return self.jcr_quartile is not None
    
    @property
    def is_ei(self) -> bool:
        """Check if journal is EI indexed."""
        return self.ei_indexed
    
    @property
    def level(self) -> str:
        """Get overall level (CAS partition)."""
        if self.cas_quartile:
            return self.cas_quartile
        if self.jcr_quartile:
            return f"JCR {self.jcr_quartile}"
        if self.ei_indexed:
            return "EI"
        return "Unknown"


@dataclass
class JournalDatabase:
    """Collection of journals with search capabilities."""
    
    journals: List[JournalInfo] = field(default_factory=list)
    
    def add(self, journal: JournalInfo) -> None:
        """Add a journal."""
        self.journals.append(journal)
    
    def find_by_issn(self, issn: str) -> Optional[JournalInfo]:
        """Find journal by ISSN."""
        for j in self.journals:
            if j.issn == issn or j.eissn == issn:
                return j
        return None
    
    def find_by_title(self, title: str) -> List[JournalInfo]:
        """Find journals by title (fuzzy match)."""
        title_lower = title.lower()
        return [j for j in self.journals if title_lower in j.title.lower()]
    
    def filter_by_quartile(self, quartile: str) -> List[JournalInfo]:
        """Filter by JCR quartile (Q1, Q2, Q3, Q4)."""
        return [j for j in self.journals if j.jcr_quartile == quartile.upper()]
    
    def filter_by_cas_quartile(self, quartile: str) -> List[JournalInfo]:
        """Filter by CAS quartile (1区, 2区, 3区, 4区)."""
        return [j for j in self.journals if j.cas_quartile == quartile]
    
    def filter_ei(self) -> List[JournalInfo]:
        """Get all EI journals."""
        return [j for j in self.journals if j.ei_indexed]
    
    def filter_sci(self) -> List[JournalInfo]:
        """Get all SCI journals."""
        return [j for j in self.journals if j.is_sci]
    
    def to_csv(self, filepath: str) -> None:
        """Export to CSV file."""
        import csv
        from pathlib import Path
        
        Path(filepath).parent.mkdir(parents=True, exist_ok=True)
        
        fieldnames = list(JournalInfo.__dataclass_fields__.keys())
        
        with open(filepath, "w", newline="", encoding="utf-8") as f:
            writer = csv.DictWriter(f, fieldnames=fieldnames, extrasaction="ignore")
            writer.writeheader()
            
            for journal in self.journals:
                row = journal.to_dict()
                writer.writerow(row)
        
        print(f"Exported {len(self.journals)} journals to {filepath}")
    
    def to_json(self, filepath: str) -> None:
        """Export to JSON file."""
        import json
        from pathlib import Path
        
        Path(filepath).parent.mkdir(parents=True, exist_ok=True)
        
        data = {
            "journals": [j.to_dict() for j in self.journals],
            "total": len(self.journals),
            "sci_count": len(self.filter_sci()),
            "ei_count": len(self.filter_ei()),
        }
        
        with open(filepath, "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
        
        print(f"Exported {len(self.journals)} journals to {filepath}")
    
    def statistics(self) -> Dict[str, Any]:
        """Get database statistics."""
        return {
            "total": len(self.journals),
            "sci_journals": len(self.filter_sci()),
            "ei_journals": len(self.filter_ei()),
            "sci_ei_both": len([j for j in self.journals if j.is_sci and j.ei_indexed]),
            "cas_1qu": len(self.filter_by_cas_quartile("1区")),
            "cas_2qu": len(self.filter_by_cas_quartile("2区")),
            "cas_3qu": len(self.filter_by_cas_quartile("3区")),
            "cas_4qu": len(self.filter_by_cas_quartile("4区")),
            "with_url": len([j for j in self.journals if j.url]),
            "with_if": len([j for j in self.journals if j.jcr_if]),
        }