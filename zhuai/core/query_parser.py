"""Advanced search query parser and filter system."""

import re
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from typing import List, Optional, Dict, Any, Set
from enum import Enum


class SearchField(Enum):
    """Search field types."""
    TITLE = "title"
    AUTHOR = "author"
    ABSTRACT = "abstract"
    KEYWORD = "keyword"
    JOURNAL = "journal"
    DOI = "doi"
    ALL = "all"


class BooleanOperator(Enum):
    """Boolean operators."""
    AND = "AND"
    OR = "OR"
    NOT = "NOT"


@dataclass
class SearchFilter:
    """Filter criteria for paper search.
    
    Attributes:
        authors: Filter by author names (any match)
        title: Filter by title keywords
        journal: Filter by journal name
        year_from: Minimum publication year
        year_to: Maximum publication year
        date_from: Start date
        date_to: End date
        jcr_quartile: JCR quartile filter (Q1, Q2, Q3, Q4)
        cas_quartile: CAS quartile filter (1区, 2区, 3区, 4区)
        min_citations: Minimum citations
        min_if: Minimum impact factor
        max_if: Maximum impact factor
        subject: Subject category
        keywords: Keywords filter
        has_pdf: Only papers with PDF
        sources: Specific sources to search
        exclude_sources: Sources to exclude
        language: Paper language filter
        article_types: Article type filter
    """
    
    authors: List[str] = field(default_factory=list)
    title: Optional[str] = None
    journal: Optional[str] = None
    year_from: Optional[int] = None
    year_to: Optional[int] = None
    date_from: Optional[datetime] = None
    date_to: Optional[datetime] = None
    jcr_quartile: Optional[str] = None
    cas_quartile: Optional[str] = None
    min_citations: Optional[int] = None
    min_if: Optional[float] = None
    max_if: Optional[float] = None
    subject: Optional[str] = None
    keywords: List[str] = field(default_factory=list)
    has_pdf: Optional[bool] = None
    sources: List[str] = field(default_factory=list)
    exclude_sources: List[str] = field(default_factory=list)
    language: Optional[str] = None
    article_types: List[str] = field(default_factory=list)
    
    def matches(self, paper: "Paper") -> bool:
        """Check if a paper matches all filter criteria.
        
        Args:
            paper: Paper to check
            
        Returns:
            True if paper matches all criteria
        """
        if self.authors:
            paper_authors_lower = [a.lower() for a in paper.authors]
            if not any(a.lower() in " ".join(paper_authors_lower) for a in self.authors):
                return False
        
        if self.title:
            if self.title.lower() not in paper.title.lower():
                return False
        
        if self.journal:
            if not paper.journal or self.journal.lower() not in paper.journal.lower():
                return False
        
        if self.year_from or self.year_to:
            if not paper.year:
                return False
            if self.year_from and paper.year < self.year_from:
                return False
            if self.year_to and paper.year > self.year_to:
                return False
        
        if self.date_from or self.date_to:
            if not paper.publication_date:
                return False
            if self.date_from and paper.publication_date < self.date_from:
                return False
            if self.date_to and paper.publication_date > self.date_to:
                return False
        
        if self.min_citations is not None:
            if paper.citations < self.min_citations:
                return False
        
        if self.has_pdf is not None:
            if self.has_pdf and not paper.can_download:
                return False
        
        if self.language:
            if paper.language and paper.language.lower() != self.language.lower():
                return False
        
        if self.keywords:
            paper_keywords_lower = [k.lower() for k in paper.keywords]
            if not any(k.lower() in " ".join(paper_keywords_lower) for k in self.keywords):
                title_abstract = f"{paper.title} {paper.abstract or ''}".lower()
                if not any(k.lower() in title_abstract for k in self.keywords):
                    return False
        
        return True
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            "authors": self.authors,
            "title": self.title,
            "journal": self.journal,
            "year_from": self.year_from,
            "year_to": self.year_to,
            "jcr_quartile": self.jcr_quartile,
            "cas_quartile": self.cas_quartile,
            "min_citations": self.min_citations,
            "min_if": self.min_if,
            "max_if": self.max_if,
            "subject": self.subject,
            "keywords": self.keywords,
            "has_pdf": self.has_pdf,
            "sources": self.sources,
            "exclude_sources": self.exclude_sources,
            "language": self.language,
            "article_types": self.article_types,
        }


@dataclass
class ParsedQuery:
    """Parsed search query with field-specific terms and operators.
    
    Attributes:
        terms: List of (field, term) tuples
        operators: List of boolean operators
        raw_query: Original query string
    """
    
    terms: List[tuple] = field(default_factory=list)
    operators: List[BooleanOperator] = field(default_factory=list)
    raw_query: str = ""
    
    def get_terms_for_field(self, field: SearchField) -> List[str]:
        """Get all terms for a specific field.
        
        Args:
            field: Search field
            
        Returns:
            List of terms for that field
        """
        return [term for f, term in self.terms if f == field]
    
    def get_all_terms(self) -> List[str]:
        """Get all search terms.
        
        Returns:
            List of all terms
        """
        return [term for _, term in self.terms]
    
    def to_simple_query(self) -> str:
        """Convert to simple query string.
        
        Returns:
            Simple query string
        """
        return " ".join(self.get_all_terms())


class QueryParser:
    """Parser for advanced search queries.
    
    Supports:
    - Field-specific search: title:deep learning, author:Smith
    - Boolean operators: AND, OR, NOT
    - Quoted phrases: "machine learning"
    - Year ranges: year:2020-2024
    - Journal filters: journal:Nature
    
    Examples:
        >>> parser = QueryParser()
        >>> query = parser.parse('title:"deep learning" author:Smith AND year:2020-2024')
        >>> query.get_terms_for_field(SearchField.TITLE)
        ['deep learning']
    """
    
    FIELD_PATTERN = re.compile(
        r'(title|author|journal|keyword|abstract|doi|year):\s*([^\s]+|"[^"]+")',
        re.IGNORECASE
    )
    
    YEAR_RANGE_PATTERN = re.compile(r'(\d{4})-(\d{4})')
    
    QUOTED_PATTERN = re.compile(r'"([^"]+)"')
    
    BOOLEAN_OPERATORS = {"AND", "OR", "NOT"}
    
    def parse(self, query: str) -> ParsedQuery:
        """Parse a search query string.
        
        Args:
            query: Query string to parse
            
        Returns:
            ParsedQuery object
        """
        parsed = ParsedQuery(raw_query=query)
        
        remaining = query
        
        field_matches = list(self.FIELD_PATTERN.finditer(query))
        
        for match in field_matches:
            field_str = match.group(1).lower()
            value = match.group(2).strip('"')
            
            field_map = {
                "title": SearchField.TITLE,
                "author": SearchField.AUTHOR,
                "journal": SearchField.JOURNAL,
                "keyword": SearchField.KEYWORD,
                "abstract": SearchField.ABSTRACT,
                "doi": SearchField.DOI,
            }
            
            field = field_map.get(field_str, SearchField.ALL)
            
            if field == SearchField.AUTHOR:
                for author in re.split(r'[;,]', value):
                    author = author.strip()
                    if author:
                        parsed.terms.append((field, author))
            elif field_str == "year":
                year_match = self.YEAR_RANGE_PATTERN.match(value)
                if year_match:
                    parsed.terms.append((SearchField.ALL, year_match.group(1)))
                    parsed.terms.append((SearchField.ALL, year_match.group(2)))
                else:
                    parsed.terms.append((SearchField.ALL, value))
            else:
                parsed.terms.append((field, value))
            
            remaining = remaining.replace(match.group(0), "", 1)
        
        tokens = remaining.split()
        
        for token in tokens:
            token_upper = token.upper()
            
            if token_upper in self.BOOLEAN_OPERATORS:
                parsed.operators.append(BooleanOperator[token_upper])
            elif token and token not in {"(", ")"}:
                parsed.terms.append((SearchField.ALL, token))
        
        return parsed
    
    def parse_to_filter(self, query: str) -> tuple:
        """Parse query to simple query string and SearchFilter.
        
        Args:
            query: Query string
            
        Returns:
            Tuple of (simple_query, SearchFilter)
        """
        parsed = self.parse(query)
        search_filter = SearchFilter()
        simple_terms = []
        
        for field, term in parsed.terms:
            if field == SearchField.AUTHOR:
                search_filter.authors.append(term)
            elif field == SearchField.JOURNAL:
                search_filter.journal = term
            elif field == SearchField.KEYWORD:
                search_filter.keywords.append(term)
            elif field == SearchField.TITLE:
                search_filter.title = term
                simple_terms.append(term)
            else:
                simple_terms.append(term)
        
        return " ".join(simple_terms), search_filter


def parse_year_range(year_str: str) -> tuple:
    """Parse year range string.
    
    Args:
        year_str: Year string (e.g., "2020", "2020-2024")
        
    Returns:
        Tuple of (year_from, year_to)
    """
    match = QueryParser.YEAR_RANGE_PATTERN.match(year_str)
    if match:
        return int(match.group(1)), int(match.group(2))
    
    try:
        year = int(year_str)
        return year, year
    except ValueError:
        return None, None


def create_filter_from_options(
    author: Optional[str] = None,
    title: Optional[str] = None,
    journal: Optional[str] = None,
    year_from: Optional[int] = None,
    year_to: Optional[int] = None,
    year: Optional[str] = None,
    jcr_quartile: Optional[str] = None,
    cas_quartile: Optional[str] = None,
    min_citations: Optional[int] = None,
    min_if: Optional[float] = None,
    max_if: Optional[float] = None,
    subject: Optional[str] = None,
    has_pdf: Optional[bool] = None,
    language: Optional[str] = None,
    **kwargs,
) -> SearchFilter:
    """Create SearchFilter from CLI options.
    
    Args:
        author: Author name(s), semicolon-separated
        title: Title keyword
        journal: Journal name
        year_from: Start year
        year_to: End year
        year: Year or year range (e.g., "2020" or "2020-2024")
        jcr_quartile: JCR quartile
        cas_quartile: CAS quartile
        min_citations: Minimum citations
        min_if: Minimum impact factor
        max_if: Maximum impact factor
        subject: Subject category
        has_pdf: Require PDF
        language: Language filter
        **kwargs: Additional options
        
    Returns:
        SearchFilter object
    """
    search_filter = SearchFilter()
    
    if author:
        search_filter.authors = [a.strip() for a in author.split(";") if a.strip()]
    
    if title:
        search_filter.title = title
    
    if journal:
        search_filter.journal = journal
    
    if year:
        y_from, y_to = parse_year_range(year)
        search_filter.year_from = y_from
        search_filter.year_to = y_to
    else:
        search_filter.year_from = year_from
        search_filter.year_to = year_to
    
    if jcr_quartile:
        search_filter.jcr_quartile = jcr_quartile.upper()
    
    if cas_quartile:
        search_filter.cas_quartile = cas_quartile
    
    search_filter.min_citations = min_citations
    search_filter.min_if = min_if
    search_filter.max_if = max_if
    search_filter.subject = subject
    search_filter.has_pdf = has_pdf
    search_filter.language = language
    
    return search_filter