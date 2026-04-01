"""Flask web application for Zhuai."""

import os
import json
import asyncio
from datetime import datetime
from pathlib import Path
from typing import Optional, List, Dict, Any
from functools import wraps

from flask import Flask, render_template, request, jsonify, send_file, send_from_directory
from flask import session, redirect, url_for

app = Flask(__name__)
app.secret_key = os.environ.get("ZHUAI_SECRET_KEY", "zhuai-web-secret-key-change-in-production")

app.config["DOWNLOAD_DIR"] = os.path.abspath("./downloads")
app.config["MAX_RESULTS"] = 100
app.config["DEFAULT_SOURCES"] = ["arxiv", "pubmed", "crossref", "semanticscholar"]


def run_async(func):
    """Decorator to run async functions in Flask routes."""
    @wraps(func)
    def wrapper(*args, **kwargs):
        return asyncio.run(func(*args, **kwargs))
    return wrapper


def get_searcher():
    """Get or create PaperSearcher instance."""
    try:
        from zhuai import PaperSearcher
        return PaperSearcher(
            download_dir=app.config["DOWNLOAD_DIR"],
            headless=True,
        )
    except ImportError:
        return None


@app.route("/")
def index():
    """Home page with search form."""
    return render_template("index.html",
        sources={
            "arxiv": {"name": "arXiv", "type": "api", "icon": "fa-arxiv"},
            "pubmed": {"name": "PubMed", "type": "api", "icon": "fa-pubmed"},
            "crossref": {"name": "CrossRef", "type": "api", "icon": "fa-doi"},
            "semanticscholar": {"name": "Semantic Scholar", "type": "api", "icon": "fa-brain"},
            "cnki": {"name": "CNKI (知网)", "type": "browser", "icon": "fa-cnki"},
            "wanfang": {"name": "万方数据", "type": "browser", "icon": "fa-wanfang"},
            "vip": {"name": "维普", "type": "browser", "icon": "fa-vip"},
        },
        quartiles=["Q1", "Q2", "Q3", "Q4"],
        cas_quartiles=["1区", "2区", "3区", "4区"],
        years=list(range(2025, 1990, -1)),
    )


@app.route("/api/search", methods=["POST"])
@run_async
async def api_search():
    """API endpoint for searching papers."""
    data = request.get_json()
    
    query = data.get("query", "")
    if not query:
        return jsonify({"error": "Query is required"}), 400
    
    max_results = data.get("max_results", 50)
    sources = data.get("sources", app.config["DEFAULT_SOURCES"])
    
    filters = {}
    if data.get("author"):
        filters["author"] = data.get("author")
    if data.get("title"):
        filters["title"] = data.get("title")
    if data.get("journal"):
        filters["journal"] = data.get("journal")
    if data.get("year_from"):
        filters["year_from"] = int(data.get("year_from"))
    if data.get("year_to"):
        filters["year_to"] = int(data.get("year_to"))
    if data.get("quartile"):
        filters["quartile"] = data.get("quartile")
    if data.get("min_citations"):
        filters["min_citations"] = int(data.get("min_citations"))
    if data.get("has_pdf"):
        filters["has_pdf"] = True
    
    try:
        searcher = get_searcher()
        
        if filters:
            from zhuai.core.query_parser import create_filter_from_options
            search_filter = create_filter_from_options(**filters)
            papers = await searcher.search_advanced(
                query=query,
                search_filter=search_filter,
                max_results=max_results,
                sources=sources,
            )
        else:
            papers = await searcher.search(
                query=query,
                max_results=max_results,
                sources=sources,
            )
        
        results = []
        for paper in papers:
            results.append({
                "title": paper.title,
                "authors": paper.authors,
                "year": paper.year,
                "journal": paper.journal,
                "doi": paper.doi,
                "pmid": paper.pmid,
                "arxiv_id": paper.arxiv_id,
                "pdf_url": paper.pdf_url,
                "source_url": paper.source_url,
                "citations": paper.citations,
                "abstract": paper.abstract[:500] + "..." if paper.abstract and len(paper.abstract) > 500 else paper.abstract,
                "source": paper.source,
                "can_download": paper.can_download,
            })
        
        return jsonify({
            "success": True,
            "total": len(results),
            "papers": results,
            "query": query,
        })
        
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@app.route("/api/download", methods=["POST"])
@run_async
async def api_download():
    """API endpoint for downloading papers."""
    data = request.get_json()
    papers = data.get("papers", [])
    
    if not papers:
        return jsonify({"error": "No papers to download"}), 400
    
    try:
        from zhuai.models.paper import Paper
        
        paper_objects = []
        for p in papers:
            paper = Paper(
                title=p.get("title", ""),
                authors=p.get("authors", []),
                pdf_url=p.get("pdf_url"),
                doi=p.get("doi"),
            )
            paper_objects.append(paper)
        
        searcher = get_searcher()
        results = await searcher.download_papers(paper_objects)
        
        downloaded = []
        failed = []
        
        for paper, (success, filepath) in zip(papers, results.values()):
            if success:
                downloaded.append({
                    "title": paper.get("title"),
                    "filepath": filepath,
                })
            else:
                failed.append(paper.get("title"))
        
        return jsonify({
            "success": True,
            "downloaded": len(downloaded),
            "failed": len(failed),
            "results": downloaded,
        })
        
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@app.route("/api/citation", methods=["POST"])
def api_citation():
    """API endpoint for generating citations."""
    data = request.get_json()
    paper = data.get("paper", {})
    style = data.get("style", "apa")
    
    try:
        from zhuai import CitationFormatter
        from zhuai.models.paper import Paper
        
        formatter = CitationFormatter()
        
        paper_obj = Paper(
            title=paper.get("title", ""),
            authors=paper.get("authors", []),
            year=paper.get("year"),
            journal=paper.get("journal"),
            doi=paper.get("doi"),
        )
        
        citation = formatter.format(paper_obj, style)
        
        return jsonify({
            "success": True,
            "citation": citation,
            "style": style,
        })
        
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@app.route("/api/journals/search")
def api_journals_search():
    """API endpoint for searching journals."""
    keyword = request.args.get("q", "")
    quartile = request.args.get("quartile")
    limit = request.args.get("limit", 20, type=int)
    
    try:
        from zhuai.journals.manager import JournalManager
        
        manager = JournalManager()
        manager.load_from_files()
        
        if keyword:
            journals = manager.database.find_by_title(keyword)
        else:
            journals = manager.database.journals
        
        if quartile:
            journals = [j for j in journals if j.jcr_quartile == quartile.upper()]
        
        results = []
        for j in journals[:limit]:
            results.append({
                "title": j.title,
                "issn": j.issn,
                "publisher": j.publisher,
                "url": j.url,
                "jcr_quartile": j.jcr_quartile,
                "jcr_if": j.jcr_if,
                "cas_quartile": j.cas_quartile,
                "ei_indexed": j.ei_indexed,
            })
        
        return jsonify({
            "success": True,
            "total": len(results),
            "journals": results,
        })
        
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@app.route("/api/export", methods=["POST"])
def api_export():
    """API endpoint for exporting results."""
    data = request.get_json()
    papers = data.get("papers", [])
    format_type = data.get("format", "csv")
    
    try:
        from zhuai.models.paper import Paper
        import tempfile
        
        paper_objects = []
        for p in papers:
            paper = Paper(
                title=p.get("title", ""),
                authors=p.get("authors", []),
                year=p.get("year"),
                journal=p.get("journal"),
                doi=p.get("doi"),
                pdf_url=p.get("pdf_url"),
                source_url=p.get("source_url"),
                citations=p.get("citations", 0),
                abstract=p.get("abstract"),
            )
            paper_objects.append(paper)
        
        searcher = get_searcher()
        
        with tempfile.NamedTemporaryFile(mode="w", suffix=f".{format_type}", delete=False) as f:
            filepath = f.name
        
        if format_type == "csv":
            searcher.export_to_csv(paper_objects, filepath)
        elif format_type == "json":
            with open(filepath, "w", encoding="utf-8") as f:
                json.dump([p.to_dict() for p in paper_objects], f, indent=2, ensure_ascii=False)
        
        return send_file(filepath, as_attachment=True, download_name=f"papers.{format_type}")
        
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@app.route("/downloads/<path:filename>")
def download_file(filename):
    """Serve downloaded files."""
    return send_from_directory(app.config["DOWNLOAD_DIR"], filename)


@app.route("/static/<path:path>")
def serve_static(path):
    """Serve static files."""
    return send_from_directory("static", path)


def create_app(config=None):
    """Create and configure the Flask application.
    
    Args:
        config: Optional configuration dictionary
        
    Returns:
        Configured Flask app
    """
    if config:
        app.config.update(config)
    
    Path(app.config["DOWNLOAD_DIR"]).mkdir(parents=True, exist_ok=True)
    
    return app


def run_server(host="0.0.0.0", port=5000, debug=False):
    """Run the Flask development server.
    
    Args:
        host: Host to bind to
        port: Port to listen on
        debug: Enable debug mode
    """
    create_app()
    print(f"\n{'='*60}")
    print(f"  Zhuai Web Server")
    print(f"  http://{host}:{port}")
    print(f"{'='*60}\n")
    app.run(host=host, port=port, debug=debug)


if __name__ == "__main__":
    run_server(debug=True)