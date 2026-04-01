"""Command-line interface for Zhuai."""

import click
from typing import Optional, List
from zhuai import PaperSearcher, CitationFormatter
from zhuai.sources.browser_base import BrowserSource
from zhuai.core.query_parser import create_filter_from_options


@click.group()
@click.version_option(version="2.0.0")
def main() -> None:
    """Zhuai (拽) - Academic paper search and download tool."""
    pass


@main.command()
@click.argument("query")
@click.option("--max-results", "-n", default=50, help="Maximum number of results")
@click.option("--output", "-o", default="results.csv", help="Output CSV file")
@click.option("--download", "-d", is_flag=True, help="Download papers")
@click.option("--download-format", type=click.Choice(["pdf", "html", "markdown", "all"]), default="pdf", help="Download format (pdf/html/markdown/all)")
@click.option("--download-dir", default="./downloads", help="Download directory")
@click.option("--sources", "-s", multiple=True, help="Sources to search (default: all)")
@click.option("--citation-style", "-c", default="apa", help="Citation style for unavailable papers")
@click.option("--unavailable-output", "-u", default="unavailable.txt", help="Output file for unavailable papers")
@click.option("--cookies-path", help="Path to cookies JSON file for login-required sources")
@click.option("--import-browser", type=click.Choice(["chrome", "edge", "firefox"]), help="Import cookies from browser")
@click.option("--import-profile", help="Browser profile name to import (default: Default)")
@click.option("--user-data-dir", help="Custom browser user data directory")
@click.option("--headless/--no-headless", default=True, help="Run browser in headless mode")
@click.option("--author", "-a", help="Filter by author name(s), semicolon-separated")
@click.option("--title", "-t", help="Filter by title keyword")
@click.option("--journal", "-j", help="Filter by journal name")
@click.option("--year", help="Filter by year or year range (e.g., 2020 or 2020-2024)")
@click.option("--year-from", type=int, help="Minimum publication year")
@click.option("--year-to", type=int, help="Maximum publication year")
@click.option("--quartile", "-q", help="Filter by JCR quartile (Q1/Q2/Q3/Q4)")
@click.option("--cas-quartile", help="Filter by CAS quartile (1区/2区/3区/4区)")
@click.option("--min-citations", type=int, help="Minimum citations")
@click.option("--subject", help="Filter by subject category")
@click.option("--has-pdf", is_flag=True, help="Only show papers with PDF available")
@click.option("--has-html", is_flag=True, help="Only show papers with HTML version available")
@click.option("--language", help="Filter by language (e.g., en, zh)")
@click.option("--format", "-f", type=click.Choice(["csv", "json", "html", "all"]), default="csv", help="Output format")
def search(
    query: str,
    max_results: int,
    output: str,
    download: bool,
    download_format: str,
    download_dir: str,
    sources: tuple,
    citation_style: str,
    unavailable_output: str,
    cookies_path: Optional[str],
    import_browser: Optional[str],
    import_profile: Optional[str],
    user_data_dir: Optional[str],
    headless: bool,
    author: Optional[str],
    title: Optional[str],
    journal: Optional[str],
    year: Optional[str],
    year_from: Optional[int],
    year_to: Optional[int],
    quartile: Optional[str],
    cas_quartile: Optional[str],
    min_citations: Optional[int],
    subject: Optional[str],
    has_pdf: bool,
    has_html: bool,
    language: Optional[str],
    format: str,
) -> None:
    """Search for academic papers with advanced filtering.
    
    QUERY: Search query (supports Chinese and English)
    
    Advanced query syntax:
      - Field search: title:deep learning, author:Smith, journal:Nature
      - Year range: year:2020-2024
      - Boolean: AND, OR, NOT (e.g., deep learning NOT review)
    
    Examples:
      zhuai search "deep learning" -s arxiv -s pubmed --year 2020-2024
      zhuai search "machine learning" --author "Hinton; LeCun" --quartile Q1
      zhuai search "transformer" -s arxiv --download --download-format markdown
      zhuai search "title:neural" -s arxiv --download --download-format all
    """
    source_list = list(sources) if sources else None
    
    search_filter = create_filter_from_options(
        author=author,
        title=title,
        journal=journal,
        year=year,
        year_from=year_from,
        year_to=year_to,
        jcr_quartile=quartile,
        cas_quartile=cas_quartile,
        min_citations=min_citations,
        subject=subject,
        has_pdf=has_pdf if has_pdf else None,
        language=language,
    )
    
    has_filters = any([
        search_filter.authors, search_filter.journal, 
        search_filter.year_from, search_filter.year_to,
        search_filter.jcr_quartile, search_filter.cas_quartile,
        search_filter.min_citations, search_filter.has_pdf,
    ])
    
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
    if has_filters:
        click.echo("Filters applied:")
        if search_filter.authors:
            click.echo(f"  - Authors: {', '.join(search_filter.authors)}")
        if search_filter.journal:
            click.echo(f"  - Journal: {search_filter.journal}")
        if search_filter.year_from or search_filter.year_to:
            y_from = search_filter.year_from or "any"
            y_to = search_filter.year_to or "any"
            click.echo(f"  - Year: {y_from} - {y_to}")
        if search_filter.jcr_quartile:
            click.echo(f"  - JCR Quartile: {search_filter.jcr_quartile}")
        if search_filter.cas_quartile:
            click.echo(f"  - CAS Quartile: {search_filter.cas_quartile}")
        if search_filter.min_citations:
            click.echo(f"  - Min citations: {search_filter.min_citations}")
        if search_filter.has_pdf:
            click.echo(f"  - Has PDF: Yes")
    
    if has_filters:
        papers = searcher.search_advanced_sync(
            query=query,
            search_filter=search_filter,
            max_results=max_results,
        )
    else:
        papers = searcher.search_sync(query, max_results=max_results)
    
    if not papers:
        click.echo("No papers found.")
        return
    
    click.echo(f"\nFound {len(papers)} papers")
    
    stats = searcher.get_statistics(papers)
    click.echo(f"  - With PDF: {stats['papers_with_pdf']}")
    click.echo(f"  - Without PDF: {stats['papers_without_pdf']}")
    
    # Count papers with HTML version (for arXiv)
    html_count = sum(1 for p in papers if p.has_html or p.html_url)
    if html_count > 0:
        click.echo(f"  - With HTML version: {html_count}")
    
    if format in ["csv", "all"]:
        searcher.export_to_csv(papers, output)
        click.echo(f"\nResults saved to: {output}")
    
    if format in ["json", "all"]:
        import json
        json_output = output.replace(".csv", ".json")
        with open(json_output, "w", encoding="utf-8") as f:
            json.dump([p.to_dict() for p in papers], f, indent=2, ensure_ascii=False)
        click.echo(f"JSON saved to: {json_output}")
    
    if stats['papers_without_pdf'] > 0:
        searcher.export_unavailable_citations(papers, unavailable_output, citation_style)
        click.echo(f"Unavailable paper citations saved to: {unavailable_output}")
    
    if download:
        if download_format == "pdf" and stats['papers_with_pdf'] > 0:
            click.echo(f"\nDownloading PDFs to: {download_dir}")
            results = searcher.download_papers_sync(papers, format="pdf")
            successful = sum(1 for r in results.values() if r[0])
            click.echo(f"Successfully downloaded: {successful}/{stats['papers_with_pdf']}")
        
        elif download_format == "html" and html_count > 0:
            click.echo(f"\nDownloading HTML versions to: {download_dir}")
            results = searcher.download_papers_sync(papers, format="html")
            successful = sum(1 for r in results.values() if r[0])
            click.echo(f"Successfully downloaded: {successful}/{html_count}")
        
        elif download_format == "markdown" and html_count > 0:
            click.echo(f"\nDownloading and converting to Markdown: {download_dir}")
            results = searcher.download_papers_sync(papers, format="markdown")
            successful = sum(1 for r in results.values() if r[0])
            click.echo(f"Successfully downloaded: {successful}/{html_count}")
        
        elif download_format == "all":
            click.echo(f"\nDownloading all formats to: {download_dir}")
            results = searcher.download_papers_sync(papers, format="all")
            successful = sum(1 for r in results.values() if r[0])
            click.echo(f"Successfully downloaded: {successful}/{len(papers)}")


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


@main.command()
@click.option("--host", "-h", default="0.0.0.0", help="Host to bind to")
@click.option("--port", "-p", default=5000, help="Port to listen on")
@click.option("--debug", is_flag=True, help="Enable debug mode")
def web(host: str, port: int, debug: bool) -> None:
    """Start the web interface.
    
    Start a web server for searching and downloading papers through a browser.
    
    Examples:
        zhuai web
        zhuai web --port 8080
        zhuai web --host 127.0.0.1 --port 5000 --debug
    """
    try:
        from zhuai.web.app import run_server
        run_server(host=host, port=port, debug=debug)
    except ImportError as e:
        click.echo(f"Error: Web module not available. {e}")
        click.echo("Make sure Flask is installed: pip install flask")


@main.command()
@click.argument("query")
@click.option("--platform", "-p", type=click.Choice(["github", "huggingface", "hfmirror", "kaggle", "modelscope"]), default="github", help="Platform to search")
@click.option("--type", "-t", type=click.Choice(["code", "model", "dataset", "all"]), default="all", help="Resource type")
@click.option("--language", "-l", help="Filter by programming language")
@click.option("--min-stars", type=int, help="Minimum number of stars")
@click.option("--max-results", "-n", default=30, help="Maximum number of results")
@click.option("--output", "-o", help="Output file (CSV or JSON)")
def search_platforms(
    query: str,
    platform: str,
    type: str,
    language: Optional[str],
    min_stars: Optional[int],
    max_results: int,
    output: Optional[str],
) -> None:
    """Search code repositories, models, and datasets on various platforms.
    
    Supported platforms:
    - github: Search code repositories
    - huggingface: Search models and datasets
    - hfmirror: HuggingFace mirror (faster in China)
    - kaggle: Search datasets and models
    - modelscope: Search models and datasets (Alibaba's platform)
    
    Examples:
        zhuai search-platforms "transformer" -p github -l python
        zhuai search-platforms "bert" -p huggingface -t model
        zhuai search-platforms "image classification" -p kaggle -t dataset
        zhuai search-platforms "LLM" -p modelscope
    """
    click.echo(f"Searching {platform} for: {query}")
    
    results = []
    
    try:
        if platform == "github":
            from zhuai.sources.github import GitHubSource
            source = GitHubSource()
            results = source.search(
                query=query,
                language=language,
                min_stars=min_stars,
                max_results=max_results,
            )
        
        elif platform == "huggingface":
            from zhuai.sources.huggingface import HuggingFaceSource
            source = HuggingFaceSource()
            
            if type in ["model", "all"]:
                models = source.search_models(query, max_results=max_results)
                results.extend(models)
            if type in ["dataset", "all"]:
                datasets = source.search_datasets(query, max_results=max_results)
                results.extend(datasets)
        
        elif platform == "hfmirror":
            from zhuai.sources.huggingface import HFMirrorSource
            source = HFMirrorSource()
            
            if type in ["model", "all"]:
                models = source.search_models(query, max_results=max_results)
                results.extend(models)
            if type in ["dataset", "all"]:
                datasets = source.search_datasets(query, max_results=max_results)
                results.extend(datasets)
        
        elif platform == "kaggle":
            from zhuai.sources.kaggle import KaggleSource
            source = KaggleSource()
            
            if type in ["dataset", "all"]:
                datasets = source.search_datasets(query, max_results=max_results)
                results.extend(datasets)
            if type in ["model", "all"]:
                models = source.search_models(query, max_results=max_results)
                results.extend(models)
        
        elif platform == "modelscope":
            from zhuai.sources.modelscope import ModelScopeSource
            source = ModelScopeSource()
            
            if type in ["model", "all"]:
                models = source.search_models(query, max_results=max_results)
                results.extend(models)
            if type in ["dataset", "all"]:
                datasets = source.search_datasets(query, max_results=max_results)
                results.extend(datasets)
        
        if not results:
            click.echo("No results found.")
            return
        
        click.echo(f"\nFound {len(results)} results:\n")
        click.echo("-" * 100)
        click.echo(f"{'Name':<40} {'Stars':<10} {'Downloads':<12} {'Type':<10} {'Platform':<15}")
        click.echo("-" * 100)
        
        for r in results[:max_results]:
            name = r.name[:37] + "..." if len(r.name) > 40 else r.name
            stars = f"{r.stars:,}" if r.stars else "-"
            downloads = f"{r.downloads:,}" if r.downloads else "-"
            resource_type = r.resource_type or "-"
            platform_name = r.platform or "-"
            
            click.echo(f"{name:<40} {stars:<10} {downloads:<12} {resource_type:<10} {platform_name:<15}")
            if r.description:
                desc = r.description[:90] + "..." if len(r.description) > 90 else r.description
                click.echo(f"  {desc}")
        
        click.echo("-" * 100)
        
        if output:
            import json
            if output.endswith(".json"):
                with open(output, "w", encoding="utf-8") as f:
                    json.dump([r.to_dict() for r in results], f, indent=2, ensure_ascii=False)
            else:
                import csv
                with open(output, "w", newline="", encoding="utf-8") as f:
                    writer = csv.DictWriter(f, fieldnames=["name", "full_name", "description", "stars", "downloads", "resource_type", "platform", "url"])
                    writer.writeheader()
                    for r in results:
                        writer.writerow(r.to_dict())
            click.echo(f"\nResults saved to: {output}")
    
    except Exception as e:
        click.echo(f"Error: {e}")


@main.command()
@click.option("--platform", "-p", type=click.Choice(["github", "huggingface", "modelscope"]), default="github", help="Platform")
@click.option("--language", "-l", help="Filter by programming language")
@click.option("--since", type=click.Choice(["daily", "weekly", "monthly"]), default="daily", help="Time period")
@click.option("--max-results", "-n", default=25, help="Maximum number of results")
def trending(platform: str, language: Optional[str], since: str, max_results: int) -> None:
    """Get trending repositories/models.
    
    Examples:
        zhuai trending -p github -l python
        zhuai trending -p huggingface
        zhuai trending -p modelscope
    """
    click.echo(f"Getting trending on {platform} ({since})...")
    
    try:
        if platform == "github":
            from zhuai.sources.github import GitHubSource
            source = GitHubSource()
            items = source.get_trending(language=language, since=since, max_results=max_results)
        
        elif platform == "huggingface":
            from zhuai.sources.huggingface import HuggingFaceSource
            source = HuggingFaceSource()
            items = source.get_trending_models(max_results=max_results)
        
        elif platform == "modelscope":
            from zhuai.sources.modelscope import ModelScopeSource
            source = ModelScopeSource()
            items = source.get_trending_models(max_results=max_results)
        
        if not items:
            click.echo("No trending items found.")
            return
        
        click.echo(f"\nTop {len(items)} trending:\n")
        click.echo("-" * 100)
        
        for item in items:
            r = item.resource
            rank = f"#{item.rank}"
            stars = f"⭐ {r.stars:,}" if r.stars else ""
            name = r.full_name[:50] if len(r.full_name) > 50 else r.full_name
            
            click.echo(f"{rank:<5} {name}")
            click.echo(f"       {stars}  {r.resource_type}  {r.url}")
            if r.description:
                desc = r.description[:80] + "..." if len(r.description) > 80 else r.description
                click.echo(f"       {desc}")
            click.echo()
        
    except Exception as e:
        click.echo(f"Error: {e}")


@main.command()
@click.argument("repo_id")
@click.option("--platform", "-p", type=click.Choice(["github", "huggingface", "kaggle", "modelscope"]), default="github", help="Platform")
def repo_info(repo_id: str, platform: str) -> None:
    """Get detailed information about a repository/model.
    
    REPO_ID: Repository/model ID (e.g., "owner/repo" for GitHub, "owner/model" for HF)
    
    Examples:
        zhuai repo-info "huggingface/transformers" -p github
        zhuai repo-info "bert-base-uncased" -p huggingface
        zhuai repo-info "Qwen/Qwen-7B-Chat" -p modelscope
    """
    click.echo(f"Fetching info for: {repo_id}")
    
    try:
        if platform == "github":
            from zhuai.sources.github import GitHubSource
            source = GitHubSource()
            
            owner, repo = repo_id.split("/") if "/" in repo_id else (repo_id, "")
            resource = source.get_repo(owner, repo)
            readme = source.get_readme(owner, repo)
            
        elif platform == "huggingface":
            from zhuai.sources.huggingface import HuggingFaceSource
            source = HuggingFaceSource()
            resource = source.get_model(repo_id)
            readme = source.get_readme(repo_id)
        
        elif platform == "kaggle":
            from zhuai.sources.kaggle import KaggleSource
            source = KaggleSource()
            
            owner, dataset = repo_id.split("/") if "/" in repo_id else (repo_id, "")
            resource = source.get_dataset(owner, dataset)
            readme = None
        
        elif platform == "modelscope":
            from zhuai.sources.modelscope import ModelScopeSource
            source = ModelScopeSource()
            resource = source.get_model(repo_id)
            readme = source.get_readme(repo_id)
        
        if not resource:
            click.echo("Not found.")
            return
        
        click.echo(f"\n{'=' * 70}")
        click.echo(f"{resource.full_name}")
        click.echo(f"{'=' * 70}")
        
        click.echo(f"\n📊 Statistics:")
        click.echo(f"  Stars: {resource.stars:,}")
        click.echo(f"  Downloads: {resource.downloads:,}")
        if resource.forks:
            click.echo(f"  Forks: {resource.forks:,}")
        if resource.likes:
            click.echo(f"  Likes: {resource.likes:,}")
        
        if resource.language:
            click.echo(f"\n💻 Language: {resource.language}")
        if resource.license:
            click.echo(f"📄 License: {resource.license}")
        
        if resource.topics:
            click.echo(f"\n🏷️  Topics: {', '.join(resource.topics[:10])}")
        
        if resource.description:
            click.echo(f"\n📝 Description:")
            click.echo(f"  {resource.description}")
        
        click.echo(f"\n🔗 URL: {resource.url}")
        
        if readme:
            click.echo(f"\n📖 README Preview (first 500 chars):")
            click.echo("-" * 70)
            preview = readme[:500] + "..." if len(readme) > 500 else readme
            click.echo(preview)
        
        click.echo(f"\n{'=' * 70}")
    
    except Exception as e:
        click.echo(f"Error: {e}")


@main.command()
@click.argument("repo_id")
@click.option("--platform", "-p", type=click.Choice(["github", "huggingface", "modelscope"]), default="github", help="Platform")
@click.option("--output", "-o", help="Output file path")
def get_readme(repo_id: str, platform: str, output: Optional[str]) -> None:
    """Get README content for a repository/model.
    
    REPO_ID: Repository/model ID
    
    Examples:
        zhuai get-readme "microsoft/vscode" -p github
        zhuai get-readme "bert-base-uncased" -p huggingface -o readme.md
    """
    try:
        readme = None
        
        if platform == "github":
            from zhuai.sources.github import GitHubSource
            source = GitHubSource()
            owner, repo = repo_id.split("/") if "/" in repo_id else (repo_id, "")
            readme = source.get_readme(owner, repo)
        
        elif platform == "huggingface":
            from zhuai.sources.huggingface import HuggingFaceSource
            source = HuggingFaceSource()
            readme = source.get_readme(repo_id)
        
        elif platform == "modelscope":
            from zhuai.sources.modelscope import ModelScopeSource
            source = ModelScopeSource()
            readme = source.get_readme(repo_id)
        
        if not readme:
            click.echo("README not found.")
            return
        
        if output:
            with open(output, "w", encoding="utf-8") as f:
                f.write(readme)
            click.echo(f"README saved to: {output}")
        else:
            click.echo(readme)
    
    except Exception as e:
        click.echo(f"Error: {e}")


if __name__ == "__main__":
    main()