"""Journal information module for Zhuai.

This module provides comprehensive journal information including:
- SCI/JCR partitions and impact factors
- CAS (Chinese Academy of Sciences) partitions
- EI (Engineering Index) indexing status
- Official journal websites
- Publisher information

Usage:
    from zhuai.journals import JournalManager, JournalDatabase
    
    # Create manager
    manager = JournalManager()
    
    # Load sample data
    from zhuai.journals.manager import create_sample_database
    db = create_sample_database()
    
    # Search journals
    results = db.find_by_title("nature")
    
    # Filter by quartile
    q1_journals = db.filter_by_quartile("Q1")
    
    # Get statistics
    stats = db.statistics()
"""

from zhuai.journals.models import JournalInfo, JournalDatabase
from zhuai.journals.manager import JournalManager, create_sample_database
from zhuai.journals.sources import (
    JournalSource,
    LetPubSource,
    CASPartitionSource,
    JCRSource,
    EISource,
    DOAJSource,
    CrossrefJournalSource,
)

__all__ = [
    "JournalInfo",
    "JournalDatabase",
    "JournalManager",
    "JournalSource",
    "LetPubSource",
    "CASPartitionSource",
    "JCRSource",
    "EISource",
    "DOAJSource",
    "CrossrefJournalSource",
    "create_sample_database",
]