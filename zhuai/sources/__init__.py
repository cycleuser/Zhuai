"""Paper data sources module."""

from zhuai.sources.base import BaseSource
from zhuai.sources.browser_base import BrowserSource
from zhuai.sources.arxiv import ArxivSource
from zhuai.sources.pubmed import PubMedSource
from zhuai.sources.crossref import CrossRefSource
from zhuai.sources.semanticscholar import SemanticScholarSource
from zhuai.sources.cnki import CNKISource
from zhuai.sources.wanfang import WanfangSource
from zhuai.sources.vip import VIPSource
from zhuai.sources.bing import BingAcademicSource
from zhuai.sources.baidu import BaiduAcademicSource

__all__ = [
    "BaseSource",
    "BrowserSource",
    "ArxivSource",
    "PubMedSource",
    "CrossRefSource",
    "SemanticScholarSource",
    "CNKISource",
    "WanfangSource",
    "VIPSource",
    "BingAcademicSource",
    "BaiduAcademicSource",
]

ALL_SOURCES = {
    "arxiv": ArxivSource,
    "pubmed": PubMedSource,
    "crossref": CrossRefSource,
    "semanticscholar": SemanticScholarSource,
    "cnki": CNKISource,
    "wanfang": WanfangSource,
    "vip": VIPSource,
    "bing": BingAcademicSource,
    "baidu": BaiduAcademicSource,
}