"""Paper data model."""

from dataclasses import dataclass, field
from datetime import datetime
from typing import List, Optional, Dict, Any


@dataclass
class Paper:
    """Represents an academic paper with metadata."""
    
    title: str
    authors: List[str]
    abstract: Optional[str] = None
    publication_date: Optional[datetime] = None
    journal: Optional[str] = None
    volume: Optional[str] = None
    issue: Optional[str] = None
    pages: Optional[str] = None
    doi: Optional[str] = None
    pmid: Optional[str] = None
    arxiv_id: Optional[str] = None
    pdf_url: Optional[str] = None
    html_url: Optional[str] = None
    source_url: Optional[str] = None
    citations: int = 0
    keywords: List[str] = field(default_factory=list)
    source: Optional[str] = None
    article_type: Optional[str] = None
    issn: Optional[str] = None
    publisher: Optional[str] = None
    language: Optional[str] = None
    has_html: bool = False
    
    @property
    def year(self) -> Optional[int]:
        """Get publication year."""
        return self.publication_date.year if self.publication_date else None
    
    @property
    def can_download(self) -> bool:
        """Check if PDF can be downloaded."""
        return self.pdf_url is not None
    
    @property
    def can_download_html(self) -> bool:
        """Check if HTML version is available."""
        return self.html_url is not None or self.has_html
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert paper to dictionary."""
        return {
            "title": self.title,
            "authors": "; ".join(self.authors),
            "abstract": self.abstract,
            "publication_date": self.publication_date.isoformat() if self.publication_date else None,
            "journal": self.journal,
            "volume": self.volume,
            "issue": self.issue,
            "pages": self.pages,
            "doi": self.doi,
            "pmid": self.pmid,
            "arxiv_id": self.arxiv_id,
            "pdf_url": self.pdf_url,
            "html_url": self.html_url,
            "source_url": self.source_url,
            "citations": self.citations,
            "keywords": "; ".join(self.keywords),
            "source": self.source,
            "article_type": self.article_type,
            "issn": self.issn,
            "publisher": self.publisher,
            "language": self.language,
            "year": self.year,
            "can_download": self.can_download,
            "has_html": self.has_html,
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "Paper":
        """Create paper from dictionary."""
        if isinstance(data.get("authors"), str):
            data["authors"] = [a.strip() for a in data["authors"].split(";")]
        
        if isinstance(data.get("keywords"), str):
            data["keywords"] = [k.strip() for k in data["keywords"].split(";")]
        
        if isinstance(data.get("publication_date"), str):
            data["publication_date"] = datetime.fromisoformat(data["publication_date"])
        
        return cls(**{k: v for k, v in data.items() if k in cls.__dataclass_fields__})
    
    def __str__(self) -> str:
        """String representation."""
        authors_str = ", ".join(self.authors[:3])
        if len(self.authors) > 3:
            authors_str += " et al."
        
        year_str = f" ({self.year})" if self.year else ""
        journal_str = f" - {self.journal}" if self.journal else ""
        
        return f"{self.title}{year_str}{journal_str} [{authors_str}]"