"""HTML to Markdown converter for academic papers."""

import re
from typing import Optional, List, Tuple
from dataclasses import dataclass


@dataclass
class ConvertedContent:
    """Result of HTML to Markdown conversion."""
    
    markdown: str
    title: str
    sections: List[Tuple[str, str]]
    equations: List[str]
    figures: List[str]
    references: List[str]


class HTMLToMarkdownConverter:
    """Convert HTML content from arXiv to Markdown format.
    
    Features:
    - Preserves mathematical equations (LaTeX)
    - Converts headings properly
    - Extracts figures and tables
    - Formats references
    - Handles code blocks
    """
    
    HEADING_PATTERN = re.compile(r'<h([1-6])[^>]*>(.*?)</h\1>', re.DOTALL | re.IGNORECASE)
    PARAGRAPH_PATTERN = re.compile(r'<p[^>]*>(.*?)</p>', re.DOTALL | re.IGNORECASE)
    LINK_PATTERN = re.compile(r'<a[^>]*href=["\']([^"\']*)["\'][^>]*>(.*?)</a>', re.DOTALL | re.IGNORECASE)
    BOLD_PATTERN = re.compile(r'<(strong|b)[^>]*>(.*?)</\1>', re.DOTALL | re.IGNORECASE)
    ITALIC_PATTERN = re.compile(r'<(em|i)[^>]*>(.*?)</\1>', re.DOTALL | re.IGNORECASE)
    CODE_PATTERN = re.compile(r'<code[^>]*>(.*?)</code>', re.DOTALL | re.IGNORECASE)
    PRE_PATTERN = re.compile(r'<pre[^>]*>(.*?)</pre>', re.DOTALL | re.IGNORECASE)
    LIST_PATTERN = re.compile(r'<li[^>]*>(.*?)</li>', re.DOTALL | re.IGNORECASE)
    MATH_PATTERN = re.compile(r'<(?:math|script[^>]*type=["\']math[^"\']*["\'])[^>]*>(.*?)</(?:math|script)>', re.DOTALL | re.IGNORECASE)
    FIGURE_PATTERN = re.compile(r'<figure[^>]*>(.*?)</figure>', re.DOTALL | re.IGNORECASE)
    IMG_PATTERN = re.compile(r'<img[^>]*src=["\']([^"\']*)["\'][^>]*alt=["\']([^"\']*)["\'][^>]*/?>', re.IGNORECASE)
    TABLE_PATTERN = re.compile(r'<table[^>]*>(.*?)</table>', re.DOTALL | re.IGNORECASE)
    
    STYLE_TAGS = re.compile(r'<(style|script)[^>]*>.*?</\1>', re.DOTALL | re.IGNORECASE)
    COMMENT_PATTERN = re.compile(r'<!--.*?-->', re.DOTALL)
    WHITESPACE_PATTERN = re.compile(r'\s+')
    
    def convert(self, html: str, url: Optional[str] = None) -> ConvertedContent:
        """Convert HTML to Markdown.
        
        Args:
            html: HTML content
            url: Source URL for relative links
            
        Returns:
            ConvertedContent with markdown and metadata
        """
        title = self._extract_title(html)
        
        content = self._clean_html(html)
        
        content = self._convert_math(content)
        
        content = self._convert_headings(content)
        
        content = self._convert_formatting(content)
        
        content = self._convert_lists(content)
        
        content = self._convert_links(content, url)
        
        content = self._convert_code(content)
        
        figures = self._extract_figures(content)
        content = self._convert_figures(content)
        
        equations = self._extract_equations(content)
        
        content = self._convert_paragraphs(content)
        
        content = self._clean_whitespace(content)
        
        sections = self._extract_sections(content)
        references = self._extract_references(content)
        
        if url:
            content = f"Source: {url}\n\n---\n\n{content}"
        
        return ConvertedContent(
            markdown=content,
            title=title,
            sections=sections,
            equations=equations,
            figures=figures,
            references=references,
        )
    
    def _extract_title(self, html: str) -> str:
        """Extract title from HTML."""
        title_match = re.search(r'<title[^>]*>(.*?)</title>', html, re.DOTALL | re.IGNORECASE)
        if title_match:
            return self._clean_text(title_match.group(1))
        
        h1_match = re.search(r'<h1[^>]*>(.*?)</h1>', html, re.DOTALL | re.IGNORECASE)
        if h1_match:
            return self._clean_text(h1_match.group(1))
        
        return "Untitled"
    
    def _clean_html(self, html: str) -> str:
        """Remove style and script tags, comments."""
        content = self.STYLE_TAGS.sub('', html)
        content = self.COMMENT_PATTERN.sub('', content)
        return content
    
    def _convert_headings(self, html: str) -> str:
        """Convert HTML headings to Markdown."""
        def replace_heading(match):
            level = int(match.group(1))
            content = self._clean_text(match.group(2))
            return f"\n\n{'#' * level} {content}\n\n"
        
        return self.HEADING_PATTERN.sub(replace_heading, html)
    
    def _convert_formatting(self, html: str) -> str:
        """Convert bold and italic."""
        html = self.BOLD_PATTERN.sub(r'**\2**', html)
        html = self.ITALIC_PATTERN.sub(r'*\2*', html)
        return html
    
    def _convert_links(self, html: str, base_url: Optional[str] = None) -> str:
        """Convert HTML links to Markdown."""
        def replace_link(match):
            href = match.group(1)
            text = self._clean_text(match.group(2))
            
            if base_url and not href.startswith(('http://', 'https://', '//')):
                href = base_url.rstrip('/') + '/' + href.lstrip('/')
            
            return f'[{text}]({href})'
        
        return self.LINK_PATTERN.sub(replace_link, html)
    
    def _convert_code(self, html: str) -> str:
        """Convert code blocks."""
        def replace_pre(match):
            code = match.group(1)
            code = self.CODE_PATTERN.sub(r'\1', code)
            return f'\n\n```\n{self._clean_text(code)}\n```\n\n'
        
        html = self.PRE_PATTERN.sub(replace_pre, html)
        html = self.CODE_PATTERN.sub(r'`\1`', html)
        return html
    
    def _convert_lists(self, html: str) -> str:
        """Convert list items."""
        def replace_li(match):
            content = self._clean_text(match.group(1))
            return f'- {content}\n'
        
        return self.LIST_PATTERN.sub(replace_li, html)
    
    def _convert_math(self, html: str) -> str:
        """Convert math elements to LaTeX-style."""
        def replace_math(match):
            math_content = match.group(1)
            return f'\n$$\n{math_content}\n$$\n'
        
        return self.MATH_PATTERN.sub(replace_math, html)
    
    def _convert_figures(self, html: str) -> str:
        """Convert figure elements."""
        def replace_figure(match):
            img_match = self.IMG_PATTERN.search(match.group(1))
            if img_match:
                src = img_match.group(1)
                alt = img_match.group(2) or "Figure"
                return f'\n\n![{alt}]({src})\n\n'
            return ''
        
        return self.FIGURE_PATTERN.sub(replace_figure, html)
    
    def _extract_figures(self, html: str) -> List[str]:
        """Extract figure URLs."""
        figures = []
        for match in self.IMG_PATTERN.finditer(html):
            figures.append(match.group(1))
        return figures
    
    def _extract_equations(self, html: str) -> List[str]:
        """Extract equations from content."""
        equations = []
        for match in self.MATH_PATTERN.finditer(html):
            equations.append(match.group(1).strip())
        return equations
    
    def _convert_paragraphs(self, html: str) -> str:
        """Convert paragraph tags."""
        def replace_p(match):
            content = self._clean_text(match.group(1))
            if content:
                return f'\n\n{content}\n\n'
            return ''
        
        return self.PARAGRAPH_PATTERN.sub(replace_p, html)
    
    def _clean_text(self, text: str) -> str:
        """Clean text content."""
        text = re.sub(r'<[^>]+>', '', text)
        text = self.WHITESPACE_PATTERN.sub(' ', text)
        return text.strip()
    
    def _clean_whitespace(self, text: str) -> str:
        """Clean up excessive whitespace."""
        text = re.sub(r'\n{3,}', '\n\n', text)
        text = re.sub(r' {2,}', ' ', text)
        return text.strip()
    
    def _extract_sections(self, markdown: str) -> List[Tuple[str, str]]:
        """Extract sections based on headings."""
        sections = []
        lines = markdown.split('\n')
        current_title = "Introduction"
        current_content = []
        
        for line in lines:
            if line.startswith('#'):
                if current_content:
                    sections.append((current_title, '\n'.join(current_content).strip()))
                current_title = line.lstrip('#').strip()
                current_content = []
            else:
                current_content.append(line)
        
        if current_content:
            sections.append((current_title, '\n'.join(current_content).strip()))
        
        return sections
    
    def _extract_references(self, markdown: str) -> List[str]:
        """Extract references section."""
        refs = []
        in_refs = False
        
        for line in markdown.split('\n'):
            if re.match(r'^#\s*references', line, re.IGNORECASE):
                in_refs = True
                continue
            if in_refs:
                if line.startswith('#'):
                    break
                if line.strip():
                    refs.append(line.strip())
        
        return refs


def convert_html_to_markdown(html: str, url: Optional[str] = None) -> str:
    """Simple function to convert HTML to Markdown.
    
    Args:
        html: HTML content
        url: Source URL for relative links
        
    Returns:
        Markdown string
    """
    converter = HTMLToMarkdownConverter()
    result = converter.convert(html, url)
    return result.markdown