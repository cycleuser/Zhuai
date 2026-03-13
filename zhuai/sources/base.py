"""Base class for paper sources."""

from abc import ABC, abstractmethod
from typing import List, Optional
from zhuai.models.paper import Paper


class BaseSource(ABC):
    """Abstract base class for paper data sources."""
    
    def __init__(self, timeout: int = 30):
        """Initialize source.
        
        Args:
            timeout: Request timeout in seconds.
        """
        self.timeout = timeout
    
    @property
    @abstractmethod
    def name(self) -> str:
        """Get source name."""
        pass
    
    @property
    @abstractmethod
    def supports_pdf(self) -> bool:
        """Check if source supports direct PDF download."""
        pass
    
    @abstractmethod
    async def search(
        self,
        query: str,
        max_results: int = 100,
        **kwargs,
    ) -> List[Paper]:
        """Search for papers.
        
        Args:
            query: Search query.
            max_results: Maximum number of results.
            **kwargs: Additional source-specific parameters.
            
        Returns:
            List of papers.
        """
        pass
    
    @abstractmethod
    async def get_paper_by_id(self, paper_id: str) -> Optional[Paper]:
        """Get a paper by its ID.
        
        Args:
            paper_id: Paper identifier (DOI, PMID, arXiv ID, etc.).
            
        Returns:
            Paper if found, None otherwise.
        """
        pass
    
    def search_sync(self, query: str, max_results: int = 100, **kwargs) -> List[Paper]:
        """Synchronous wrapper for search.
        
        Args:
            query: Search query.
            max_results: Maximum number of results.
            **kwargs: Additional parameters.
            
        Returns:
            List of papers.
        """
        import asyncio
        return asyncio.run(self.search(query, max_results, **kwargs))
    
    def get_paper_by_id_sync(self, paper_id: str) -> Optional[Paper]:
        """Synchronous wrapper for get_paper_by_id.
        
        Args:
            paper_id: Paper identifier.
            
        Returns:
            Paper if found, None otherwise.
        """
        import asyncio
        return asyncio.run(self.get_paper_by_id(paper_id))
    
    async def close(self) -> None:
        """Close any open connections."""
        pass