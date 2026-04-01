"""Code and model resource models."""

from dataclasses import dataclass, field
from datetime import datetime
from typing import List, Optional, Dict, Any
from enum import Enum


class ResourceType(Enum):
    """Type of resource."""
    PAPER = "paper"
    CODE = "code"
    MODEL = "model"
    DATASET = "dataset"
    NOTEBOOK = "notebook"


class Platform(Enum):
    """Platform identifiers."""
    GITHUB = "github"
    HUGGINGFACE = "huggingface"
    KAGGLE = "kaggle"
    MODELSCOPE = "modelscope"
    ARXIV = "arxiv"
    PUBMED = "pubmed"


@dataclass
class CodeResource:
    """Represents a code repository or model.
    
    Attributes:
        name: Resource name
        full_name: Full name (e.g., owner/repo)
        description: Description text
        author: Author/owner name
        platform: Platform identifier
        resource_type: Type of resource
        url: Resource URL
        stars: Star count
        forks: Fork count
        watchers: Watcher count
        language: Programming language
        license: License type
        topics: Tags/topics
        created_at: Creation date
        updated_at: Last update date
        readme: README content
        documentation_url: Documentation URL
        download_url: Download URL
        size: Size in bytes
        open_issues: Open issue count
        contributors: Contributor count
        tags: Version tags
        datasets: Related datasets
        models: Related models
        papers: Related papers
        citations: Citation count
        downloads: Download count
        likes: Like count
        metadata: Additional metadata
    """
    
    name: str
    full_name: str
    description: Optional[str] = None
    author: Optional[str] = None
    platform: str = "github"
    resource_type: str = "code"
    url: Optional[str] = None
    
    stars: int = 0
    forks: int = 0
    watchers: int = 0
    
    language: Optional[str] = None
    license: Optional[str] = None
    topics: List[str] = field(default_factory=list)
    
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None
    
    readme: Optional[str] = None
    readme_url: Optional[str] = None
    documentation_url: Optional[str] = None
    download_url: Optional[str] = None
    
    size: int = 0
    open_issues: int = 0
    contributors: int = 0
    
    tags: List[str] = field(default_factory=list)
    datasets: List[str] = field(default_factory=list)
    models: List[str] = field(default_factory=list)
    papers: List[str] = field(default_factory=list)
    
    citations: int = 0
    downloads: int = 0
    likes: int = 0
    
    metadata: Dict[str, Any] = field(default_factory=dict)
    
    @property
    def popularity_score(self) -> float:
        """Calculate popularity score."""
        return self.stars + (self.forks * 2) + (self.watchers * 0.5) + (self.downloads * 0.1)
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            "name": self.name,
            "full_name": self.full_name,
            "description": self.description,
            "author": self.author,
            "platform": self.platform,
            "resource_type": self.resource_type,
            "url": self.url,
            "stars": self.stars,
            "forks": self.forks,
            "watchers": self.watchers,
            "language": self.language,
            "license": self.license,
            "topics": self.topics,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None,
            "readme_url": self.readme_url,
            "documentation_url": self.documentation_url,
            "download_url": self.download_url,
            "size": self.size,
            "open_issues": self.open_issues,
            "contributors": self.contributors,
            "tags": self.tags,
            "datasets": self.datasets,
            "models": self.models,
            "papers": self.papers,
            "citations": self.citations,
            "downloads": self.downloads,
            "likes": self.likes,
            "popularity_score": self.popularity_score,
        }


@dataclass
class TrendingItem:
    """Trending resource item.
    
    Attributes:
        rank: Ranking position
        resource: Code resource
        trending_score: Trending score
        daily_stars: Stars gained today
        weekly_stars: Stars gained this week
        monthly_stars: Stars gained this month
        trending_since: When it started trending
    """
    
    rank: int
    resource: CodeResource
    trending_score: float = 0.0
    daily_stars: int = 0
    weekly_stars: int = 0
    monthly_stars: int = 0
    trending_since: Optional[datetime] = None
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            "rank": self.rank,
            "resource": self.resource.to_dict(),
            "trending_score": self.trending_score,
            "daily_stars": self.daily_stars,
            "weekly_stars": self.weekly_stars,
            "monthly_stars": self.monthly_stars,
        }


@dataclass
class SearchResult:
    """Combined search result containing papers, code, models, datasets.
    
    Attributes:
        query: Search query
        papers: Paper results
        code: Code repository results
        models: Model results
        datasets: Dataset results
        total_results: Total number of results
        search_time: Time taken for search
    """
    
    query: str
    papers: List[Any] = field(default_factory=list)
    code: List[CodeResource] = field(default_factory=list)
    models: List[CodeResource] = field(default_factory=list)
    datasets: List[CodeResource] = field(default_factory=list)
    total_results: int = 0
    search_time: float = 0.0
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            "query": self.query,
            "papers": [p.to_dict() if hasattr(p, 'to_dict') else str(p) for p in self.papers],
            "code": [c.to_dict() for c in self.code],
            "models": [m.to_dict() for m in self.models],
            "datasets": [d.to_dict() for d in self.datasets],
            "total_results": self.total_results,
            "search_time": self.search_time,
        }