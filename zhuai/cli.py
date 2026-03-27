"""Command-line interface for Zhuai."""

import click
from typing import Optional, List
from zhuai import PaperSearcher, CitationFormatter
from zhuai.sources.browser_base import BrowserSource


@click.group()
@click.version_option(version="2.0.0")
def main() -> None:
    """Zhuai (拽) - Academic paper search and download tool."""
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
@click.option("--cookies-path", help="Path to cookies JSON file for login-required sources")
@click.option("--import-browser", type=click.Choice(["chrome", "edge", "firefox"]), help="Import cookies from browser")
@click.option("--import-profile", help="Browser profile name to import (default: Default)")
@click.option("--user-data-dir", help="Custom browser user data directory")
@click.option("--headless/--no-headless", default=True, help="Run browser in headless mode")
@click.option("--vision-model", default="gemma3:4b", help="Ollama vision model for CAPTCHA solving")
def search(
    query: str,
    max_results: int,
    output: str,
    download: bool,
    download_dir: str,
    sources: tuple,
    citation_style: str,
    unavailable_output: str,
    cookies_path: Optional[str],
    import_browser: Optional[str],
    import_profile: Optional[str],
    user_data_dir: Optional[str],
    headless: bool,
    vision_model: str,
) -> None:
    """Search for academic papers.
    
    QUERY: Search query (supports Chinese and English)
    """
    source_list = list(sources) if sources else None
    
    searcher = PaperSearcher(
        sources=source_list,
        download_dir=download_dir,
        cookies_path=cookies_path,
        headless=headless,
        import_browser=import_browser,
        import_profile=import_profile,
        user_data_dir=user_data_dir,
        vision_model=vision_model,
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


@main.command()
def browsers() -> None:
    """List browsers that can be imported."""
    browsers_list = BrowserSource.list_importable_browsers()
    click.echo("Browsers that can be imported:")
    for browser in browsers_list:
        click.echo(f"  - {browser['id']}: {browser['name']}")


@main.command()
def cookies_help() -> None:
    """Show instructions for exporting cookies from browser."""
    click.echo(BrowserSource.export_cookies_instructions())


@main.command()
@click.argument("keyword", required=False)
@click.option("--quartile", "-q", help="Filter by JCR quartile (Q1/Q2/Q3/Q4)")
@click.option("--cas-quartile", help="Filter by CAS quartile (1区/2区/3区/4区)")
@click.option("--sci", is_flag=True, help="Show only SCI journals")
@click.option("--ei", is_flag=True, help="Show only EI journals")
@click.option("--output", "-o", default="journals.csv", help="Output file")
@click.option("--max-results", "-n", default=20, help="Maximum results to display")
def journals(
    keyword: Optional[str],
    quartile: Optional[str],
    cas_quartile: Optional[str],
    sci: bool,
    ei: bool,
    output: str,
    max_results: int,
) -> None:
    """Search and display journal information.
    
    KEYWORD: Search keyword (optional, shows all if not provided)
    
    Examples:
        zhuai journals "nature"
        zhuai journals "computer" --quartile Q1
        zhuai journals --cas-quartile 1区 --sci
        zhuai journals "machine learning" --output ml_journals.csv
    """
    from zhuai.journals.manager import create_sample_database
    
    db = create_sample_database()
    
    if keyword:
        results = db.find_by_title(keyword)
    else:
        results = db.journals
    
    if quartile:
        results = [j for j in results if j.jcr_quartile == quartile.upper()]
    
    if cas_quartile:
        results = [j for j in results if j.cas_quartile == cas_quartile]
    
    if sci:
        results = [j for j in results if j.is_sci]
    
    if ei:
        results = [j for j in results if j.ei_indexed]
    
    results = results[:max_results]
    
    if not results:
        click.echo("No journals found.")
        return
    
    click.echo(f"\nFound {len(results)} journals:\n")
    click.echo("-" * 100)
    click.echo(f"{'Title':<50} {'ISSN':<12} {'JCR':<6} {'CAS':<6} {'EI':<4} {'IF':<8}")
    click.echo("-" * 100)
    
    for j in results:
        title = j.title[:47] + "..." if len(j.title) > 50 else j.title
        issn = j.issn or "N/A"
        jcr = j.jcr_quartile or "-"
        cas = j.cas_quartile or "-"
        ei_mark = "✓" if j.ei_indexed else "-"
        if_val = f"{j.jcr_if:.2f}" if j.jcr_if else "-"
        
        click.echo(f"{title:<50} {issn:<12} {jcr:<6} {cas:<6} {ei_mark:<4} {if_val:<8}")
        
        if j.url:
            click.echo(f"  URL: {j.url}")
    
    click.echo("-" * 100)
    
    stats = db.statistics()
    click.echo(f"\nDatabase Statistics:")
    click.echo(f"  Total journals: {stats['total']}")
    click.echo(f"  SCI journals: {stats['sci_journals']}")
    click.echo(f"  EI journals: {stats['ei_journals']}")
    click.echo(f"  SCI+EI both: {stats['sci_ei_both']}")
    click.echo(f"  CAS 1区: {stats['cas_1qu']}")
    click.echo(f"  CAS 2区: {stats['cas_2qu']}")
    
    if output:
        db.to_csv(output)
        click.echo(f"\nExported to: {output}")


@main.command()
def journal_stats() -> None:
    """Display journal database statistics."""
    from zhuai.journals.manager import create_sample_database
    
    db = create_sample_database()
    stats = db.statistics()
    
    click.echo("\n" + "=" * 60)
    click.echo("Journal Database Statistics")
    click.echo("=" * 60)
    
    click.echo(f"\nTotal Journals: {stats['total']}")
    
    click.echo(f"\nBy Database:")
    click.echo(f"  SCI (JCR indexed): {stats['sci_journals']}")
    click.echo(f"  EI indexed: {stats['ei_journals']}")
    click.echo(f"  Both SCI+EI: {stats['sci_ei_both']}")
    
    click.echo(f"\nBy CAS Partition:")
    click.echo(f"  1区 (Top): {stats['cas_1qu']}")
    click.echo(f"  2区: {stats['cas_2qu']}")
    click.echo(f"  3区: {stats['cas_3qu']}")
    click.echo(f"  4区: {stats['cas_4qu']}")
    
    click.echo(f"\nData Quality:")
    click.echo(f"  With official URL: {stats['with_url']}")
    click.echo(f"  With Impact Factor: {stats['with_if']}")
    
    click.echo("\n" + "=" * 60)


@main.command()
@click.argument("issn")
def journal_info(issn: str) -> None:
    """Get detailed information about a specific journal by ISSN.
    
    ISSN: Journal ISSN number (e.g., 0028-0836 for Nature)
    """
    from zhuai.journals.manager import create_sample_database
    
    db = create_sample_database()
    journal = db.find_by_issn(issn)
    
    if not journal:
        click.echo(f"Journal with ISSN {issn} not found.")
        return
    
    click.echo(f"\n{'=' * 60}")
    click.echo(f"Journal: {journal.title}")
    click.echo(f"{'=' * 60}")
    
    click.echo(f"\nBasic Information:")
    click.echo(f"  ISSN: {journal.issn or 'N/A'}")
    click.echo(f"  E-ISSN: {journal.eissn or 'N/A'}")
    click.echo(f"  Publisher: {journal.publisher or 'N/A'}")
    click.echo(f"  Official URL: {journal.url or 'N/A'}")
    
    click.echo(f"\nJCR/SCI Information:")
    click.echo(f"  JCR Quartile: {journal.jcr_quartile or 'N/A'}")
    click.echo(f"  Impact Factor: {journal.jcr_if or 'N/A'}")
    click.echo(f"  JCR Category: {journal.jcr_category or 'N/A'}")
    
    click.echo(f"\nCAS Partition:")
    click.echo(f"  CAS Quartile: {journal.cas_quartile or 'N/A'}")
    click.echo(f"  Top Journal: {'Yes' if journal.cas_top else 'No'}")
    
    click.echo(f"\nIndexing:")
    click.echo(f"  SCI Indexed: {'Yes' if journal.is_sci else 'No'}")
    click.echo(f"  EI Indexed: {'Yes' if journal.ei_indexed else 'No'}")
    click.echo(f"  Open Access: {'Yes' if journal.open_access else 'No'}")
    
    if journal.submission_url:
        click.echo(f"\nSubmission URL: {journal.submission_url}")
    
    click.echo(f"\n{'=' * 60}")


if __name__ == "__main__":
    main()