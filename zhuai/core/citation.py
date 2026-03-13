"""Citation formatter for standard academic citations."""

from typing import List, Optional
from zhuai.models.paper import Paper


class CitationFormatter:
    """Format academic citations in standard formats."""
    
    @staticmethod
    def format_apa(paper: Paper) -> str:
        """Format citation in APA style.
        
        Args:
            paper: Paper object to format.
            
        Returns:
            APA formatted citation string.
        """
        parts = []
        
        # Authors
        if paper.authors:
            if len(paper.authors) <= 7:
                authors_str = ", ".join(paper.authors[:-1]) if len(paper.authors) > 1 else ""
                if len(paper.authors) > 1:
                    authors_str += f", & {paper.authors[-1]}"
                else:
                    authors_str = paper.authors[0]
            else:
                authors_str = ", ".join(paper.authors[:6]) + ", ... " + paper.authors[-1]
            parts.append(authors_str)
        
        # Year
        if paper.year:
            parts.append(f"({paper.year})")
        
        # Title
        parts.append(paper.title)
        
        # Journal info
        if paper.journal:
            journal_part = f"*{paper.journal}*"
            if paper.volume:
                journal_part += f", *{paper.volume}*"
                if paper.issue:
                    journal_part += f"({paper.issue})"
            if paper.pages:
                journal_part += f", {paper.pages}"
            journal_part += "."
            parts.append(journal_part)
        
        # DOI
        if paper.doi:
            parts.append(f"https://doi.org/{paper.doi}")
        
        return " ".join(parts)
    
    @staticmethod
    def format_mla(paper: Paper) -> str:
        """Format citation in MLA style.
        
        Args:
            paper: Paper object to format.
            
        Returns:
            MLA formatted citation string.
        """
        parts = []
        
        # Authors (Last, First)
        if paper.authors:
            if len(paper.authors) == 1:
                parts.append(paper.authors[0])
            else:
                parts.append(f"{paper.authors[0]}, et al")
        
        # Title
        parts.append(f'"{paper.title}."')
        
        # Journal info
        if paper.journal:
            journal_part = f"*{paper.journal}*"
            if paper.volume:
                journal_part += f", vol. {paper.volume}"
            if paper.issue:
                journal_part += f", no. {paper.issue}"
            if paper.year:
                journal_part += f", {paper.year}"
            if paper.pages:
                journal_part += f", pp. {paper.pages}"
            journal_part += "."
            parts.append(journal_part)
        
        # DOI or URL
        if paper.doi:
            parts.append(f"https://doi.org/{paper.doi}")
        elif paper.source_url:
            parts.append(paper.source_url)
        
        return " ".join(parts)
    
    @staticmethod
    def format_chicago(paper: Paper) -> str:
        """Format citation in Chicago style.
        
        Args:
            paper: Paper object to format.
            
        Returns:
            Chicago formatted citation string.
        """
        parts = []
        
        # Authors
        if paper.authors:
            if len(paper.authors) <= 3:
                authors_str = ", ".join(paper.authors)
            else:
                authors_str = f"{paper.authors[0]} et al."
            parts.append(authors_str)
        
        # Year
        if paper.year:
            parts.append(f"{paper.year}.")
        
        # Title
        parts.append(f'"{paper.title}."')
        
        # Journal info
        if paper.journal:
            journal_part = f"*{paper.journal}*"
            if paper.volume:
                journal_part += f" {paper.volume}"
            if paper.issue:
                journal_part += f", no. {paper.issue}"
            if paper.pages:
                journal_part += f": {paper.pages}"
            journal_part += "."
            parts.append(journal_part)
        
        # DOI
        if paper.doi:
            parts.append(f"https://doi.org/{paper.doi}")
        
        return " ".join(parts)
    
    @staticmethod
    def format_gb_t_7714(paper: Paper) -> str:
        """Format citation in GB/T 7714-2015 (Chinese standard).
        
        Args:
            paper: Paper object to format.
            
        Returns:
            GB/T 7714 formatted citation string.
        """
        parts = []
        
        # Authors
        if paper.authors:
            if len(paper.authors) <= 3:
                authors_str = ", ".join(paper.authors)
            else:
                authors_str = f"{paper.authors[0]}, et al"
            parts.append(authors_str)
        
        # Title
        parts.append(paper.title)
        
        # Journal info in brackets
        journal_parts = []
        if paper.journal:
            journal_parts.append(paper.journal)
        if paper.year:
            journal_parts.append(str(paper.year))
        if paper.volume:
            journal_parts.append(f"{paper.volume}")
        if paper.issue:
            journal_parts.append(f"({paper.issue})")
        if paper.pages:
            journal_parts.append(f": {paper.pages}")
        
        if journal_parts:
            parts.append(". " + ", ".join(journal_parts) + ".")
        
        # DOI
        if paper.doi:
            parts.append(f" DOI: {paper.doi}")
        
        return "".join(parts)
    
    @staticmethod
    def format_bibtex(paper: Paper) -> str:
        """Format citation in BibTeX format.
        
        Args:
            paper: Paper object to format.
            
        Returns:
            BibTeX formatted citation string.
        """
        # Generate citation key
        first_author = paper.authors[0].split()[-1] if paper.authors else "Unknown"
        year = paper.year or "n.d."
        key = f"{first_author}{year}".replace(" ", "")
        
        lines = [f"@article{{{key},"]
        
        lines.append(f"  title = {{{paper.title}}},")
        
        if paper.authors:
            authors = " and ".join(paper.authors)
            lines.append(f"  author = {{{authors}}},")
        
        if paper.journal:
            lines.append(f"  journal = {{{paper.journal}}},")
        
        if paper.year:
            lines.append(f"  year = {{{paper.year}}},")
        
        if paper.volume:
            lines.append(f"  volume = {{{paper.volume}}},")
        
        if paper.issue:
            lines.append(f"  number = {{{paper.issue}}},")
        
        if paper.pages:
            lines.append(f"  pages = {{{paper.pages}}},")
        
        if paper.doi:
            lines.append(f"  doi = {{{paper.doi}}},")
        
        lines.append("}")
        
        return "\n".join(lines)
    
    @staticmethod
    def format_simple(paper: Paper) -> str:
        """Format a simple citation.
        
        Args:
            paper: Paper object to format.
            
        Returns:
            Simple formatted citation string.
        """
        parts = []
        
        # Authors
        if paper.authors:
            authors_str = ", ".join(paper.authors[:3])
            if len(paper.authors) > 3:
                authors_str += " et al."
            parts.append(authors_str)
        
        # Year
        if paper.year:
            parts.append(f"({paper.year})")
        
        # Title
        parts.append(paper.title)
        
        # Journal
        if paper.journal:
            journal_part = paper.journal
            if paper.volume or paper.pages:
                journal_part += ","
            parts.append(journal_part)
        
        # Volume and pages
        vol_pages = []
        if paper.volume:
            vol_pages.append(f"Vol. {paper.volume}")
        if paper.issue:
            vol_pages.append(f"No. {paper.issue}")
        if paper.pages:
            vol_pages.append(f"pp. {paper.pages}")
        
        if vol_pages:
            parts.append(", ".join(vol_pages))
        
        # DOI
        if paper.doi:
            parts.append(f"DOI: {paper.doi}")
        
        return ". ".join(parts) + "."
    
    @classmethod
    def format(
        cls,
        paper: Paper,
        style: str = "apa"
    ) -> str:
        """Format a paper citation in the specified style.
        
        Args:
            paper: Paper object to format.
            style: Citation style (apa, mla, chicago, gb_t_7714, bibtex, simple).
            
        Returns:
            Formatted citation string.
        """
        formatters = {
            "apa": cls.format_apa,
            "mla": cls.format_mla,
            "chicago": cls.format_chicago,
            "gb_t_7714": cls.format_gb_t_7714,
            "bibtex": cls.format_bibtex,
            "simple": cls.format_simple,
        }
        
        formatter = formatters.get(style.lower(), cls.format_simple)
        return formatter(paper)
    
    @classmethod
    def format_papers(
        cls,
        papers: List[Paper],
        style: str = "apa"
    ) -> List[str]:
        """Format multiple papers.
        
        Args:
            papers: List of papers to format.
            style: Citation style.
            
        Returns:
            List of formatted citation strings.
        """
        return [cls.format(paper, style) for paper in papers]