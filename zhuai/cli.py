"""Command-line interface for Zhuai."""

import click
from typing import Optional, List
from zhuai import PaperSearcher, CitationFormatter


@click.group()
@click.version_option(version="2.0.0")
def main() -> None:
    """Zhuai (拽) - A powerful academic paper search and download tool."""
    pass


@main.command()
@click.argument("query")
@click.option("--max-results", "-n", default=50, help="Maximum number of results")
@click.option("--output", "-o", default="results.csv", help="Output CSV file")
@click.option("--download", "-d", is_flag=True, help="Download PDFs")
@click.option("--download-dir", default="./downloads", help="Download directory")
@click.option("--sources", "-s", multiple=True, help="Sources to search (default: all)")
@click.option("--citation-style", "-c", default="apa", help="Citation style for unavailable papers")
@click.option("--unavailable-output", "-u", default="unavailable.txt", help="Output file for unavailable papers")
def search(
    query: str,
    max_results: int,
    output: str,
    download: bool,
    download_dir: str,
    sources: tuple,
    citation_style: str,
    unavailable_output: str,
) -> None:
    """Search for academic papers.
    
    QUERY: Search query (supports Chinese and English)
    """
    source_list = list(sources) if sources else None
    
    searcher = PaperSearcher(
        sources=source_list,
        download_dir=download_dir,
    )
    
    click.echo(f"Searching for: {query}")
    papers = searcher.search_sync(query, max_results=max_results)
    
    if not papers:
        click.echo("No papers found.")
        return
    
    click.echo(f"\nFound {len(papers)} papers")
    
    stats = searcher.get_statistics(papers)
    click.echo(f"  - With PDF: {stats['papers_with_pdf']}")
    click.echo(f"  - Without PDF: {stats['papers_without_pdf']}")
    
    searcher.export_to_csv(papers, output)
    click.echo(f"\nResults saved to: {output}")
    
    if stats['papers_without_pdf'] > 0:
        searcher.export_unavailable_citations(papers, unavailable_output, citation_style)
        click.echo(f"Unavailable paper citations saved to: {unavailable_output}")
    
    if download and stats['papers_with_pdf'] > 0:
        click.echo(f"\nDownloading PDFs to: {download_dir}")
        results = searcher.download_papers_sync(papers)
        
        successful = sum(1 for r in results.values() if r[0])
        click.echo(f"Successfully downloaded: {successful}/{stats['papers_with_pdf']}")


@main.command()
@click.argument("paper_id")
@click.option("--source", "-s", help="Source to search (arxiv, pubmed, crossref, semanticscholar)")
def get(paper_id: str, source: Optional[str]) -> None:
    """Get a paper by ID (DOI, PMID, arXiv ID).
    
    PAPER_ID: Paper identifier
    """
    searcher = PaperSearcher()
    
    click.echo(f"Fetching paper: {paper_id}")
    paper = searcher.search_sync(paper_id, max_results=1)
    
    if paper:
        p = paper[0]
        click.echo(f"\nTitle: {p.title}")
        click.echo(f"Authors: {', '.join(p.authors)}")
        if p.journal:
            click.echo(f"Journal: {p.journal}")
        if p.year:
            click.echo(f"Year: {p.year}")
        if p.doi:
            click.echo(f"DOI: {p.doi}")
        if p.pdf_url:
            click.echo(f"PDF: {p.pdf_url}")
    else:
        click.echo("Paper not found.")


@main.command()
def sources() -> None:
    """List all available sources."""
    available = PaperSearcher.list_all_sources()
    click.echo("Available sources:")
    for source in available:
        click.echo(f"  - {source}")


if __name__ == "__main__":
    main()