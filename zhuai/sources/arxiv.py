"""arXiv paper source."""

import asyncio
from datetime import datetime
from typing import List, Optional
import arxiv
from zhuai.models.paper import Paper
from zhuai.sources.base import BaseSource


class ArxivSource(BaseSource):
    """arXiv paper source."""
    
    @property
    def name(self) -> str:
        """Get source name."""
        return "arXiv"
    
    @property
    def supports_pdf(self) -> bool:
        """Check if source supports PDF download."""
        return True
    
    async def search(
        self,
        query: str,
        max_results: int = 100,
        **kwargs,
    ) -> List[Paper]:
        """Search arXiv for papers.
        
        Args:
            query: Search query.
            max_results: Maximum number of results.
            **kwargs: Additional parameters.
            
        Returns:
            List of papers.
        """
        loop = asyncio.get_event_loop()
        
        def _search():
            search = arxiv.Search(
                query=query,
                max_results=max_results,
                sort_by=arxiv.SortCriterion.Relevance,
                sort_order=arxiv.SortOrder.Descending,
            )
            return list(search.results())
        
        results = await loop.run_in_executor(None, _search)
        
        papers = []
        for result in results:
            paper = Paper(
                title=result.title,
                authors=[author.name for author in result.authors],
                abstract=result.summary,
                publication_date=result.published,
                journal=result.journal_ref,
                doi=result.doi,
                arxiv_id=result.entry_id.split("/")[-1],
                pdf_url=result.pdf_url,
                source_url=result.entry_id,
                citations=0,
                keywords=result.categories if hasattr(result, "categories") else [],
                source=self.name,
                article_type="preprint",
            )
            papers.append(paper)
        
        return papers
    
    async def get_paper_by_id(self, paper_id: str) -> Optional[Paper]:
        """Get a paper by arXiv ID.
        
        Args:
            paper_id: arXiv ID.
            
        Returns:
            Paper if found, None otherwise.
        """
        loop = asyncio.get_event_loop()
        
        def _get():
            search = arxiv.Search(id_list=[paper_id])
            results = list(search.results())
            return results[0] if results else None
        
        result = await loop.run_in_executor(None, _get)
        
        if result:
            return Paper(
                title=result.title,
                authors=[author.name for author in result.authors],
                abstract=result.summary,
                publication_date=result.published,
                journal=result.journal_ref,
                doi=result.doi,
                arxiv_id=paper_id,
                pdf_url=result.pdf_url,
                source_url=result.entry_id,
                citations=0,
                keywords=result.categories if hasattr(result, "categories") else [],
                source=self.name,
                article_type="preprint",
            )
        
        return None