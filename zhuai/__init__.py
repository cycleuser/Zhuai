"""Zhuai - A powerful academic paper search and download tool with Vision AI."""

__version__ = "2.0.0"
__author__ = "CycleUser"
__email__ = "cycleuser@users.noreply.github.com"

from zhuai.models.paper import Paper
from zhuai.core.searcher import PaperSearcher
from zhuai.core.citation import CitationFormatter
from zhuai.journals import JournalInfo, JournalDatabase, JournalManager

__all__ = [
    "Paper",
    "PaperSearcher",
    "CitationFormatter",
    "JournalInfo",
    "JournalDatabase",
    "JournalManager",
]