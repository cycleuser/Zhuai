"""Generate comprehensive journal database."""

import json
from pathlib import Path
from typing import List, Dict, Any

from zhuai.journals.comprehensive_data import JOURNALS_BY_DISCIPLINE, PUBLISHER_URLS


def generate_full_database() -> List[Dict[str, Any]]:
    """Generate complete journal database from discipline data."""
    journals = []
    seen_issn = set()
    idx = 1
    
    for discipline, journal_list in JOURNALS_BY_DISCIPLINE.items():
        for j in journal_list:
            issn = j.get("issn", "")
            
            if issn in seen_issn:
                continue
            
            seen_issn.add(issn)
            
            publisher = j.get("publisher", "")
            url = PUBLISHER_URLS.get(publisher, "")
            
            journal_entry = {
                "title": j.get("title", ""),
                "issn": issn,
                "publisher": publisher,
                "url": url,
                "jcr_quartile": j.get("jcr_quartile", "Q1"),
                "jcr_if": j.get("jcr_if", 0),
                "jcr_category": discipline,
                "cas_quartile": j.get("cas_quartile", "2区"),
                "cas_top": j.get("cas_top", False),
                "ei_indexed": j.get("ei_indexed", True),
                "open_access": j.get("open_access", False),
            }
            
            journals.append(journal_entry)
            idx += 1
    
    return journals


def add_more_journals(base_journals: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """Add additional journals to the database."""
    
    additional_journals = [
        # More CS journals
        {"title": "IEEE Internet of Computing", "issn": "1089-7801", "jcr_if": 5.1, "jcr_quartile": "Q1", "cas_quartile": "2区", "publisher": "IEEE", "jcr_category": "Computer Science"},
        {"title": "IEEE Software", "issn": "0740-7459", "jcr_if": 3.9, "jcr_quartile": "Q1", "cas_quartile": "3区", "publisher": "IEEE", "jcr_category": "Computer Science"},
        {"title": "IEEE Transactions on Mobile Computing", "issn": "1536-1233", "jcr_if": 4.5, "jcr_quartile": "Q1", "cas_quartile": "2区", "publisher": "IEEE", "jcr_category": "Computer Science"},
        {"title": "IEEE Transactions on Cloud Computing", "issn": "2168-7161", "jcr_if": 5.9, "jcr_quartile": "Q1", "cas_quartile": "2区", "publisher": "IEEE", "jcr_category": "Computer Science"},
        {"title": "IEEE Transactions on Big Data", "issn": "2332-7790", "jcr_if": 6.0, "jcr_quartile": "Q1", "cas_quartile": "2区", "publisher": "IEEE", "jcr_category": "Computer Science"},
        {"title": "IEEE Access", "issn": "2169-3536", "jcr_if": 3.9, "jcr_quartile": "Q2", "cas_quartile": "3区", "publisher": "IEEE", "jcr_category": "Computer Science"},
        {"title": "Computer Communications", "issn": "0140-3664", "jcr_if": 6.0, "jcr_quartile": "Q1", "cas_quartile": "2区", "publisher": "Elsevier", "jcr_category": "Computer Science"},
        {"title": "Future Generation Computer Systems", "issn": "0167-739X", "jcr_if": 7.5, "jcr_quartile": "Q1", "cas_quartile": "2区", "publisher": "Elsevier", "jcr_category": "Computer Science"},
        {"title": "Journal of Network and Computer Applications", "issn": "1084-8045", "jcr_if": 7.3, "jcr_quartile": "Q1", "cas_quartile": "2区", "publisher": "Elsevier", "jcr_category": "Computer Science"},
        {"title": "Information Processing & Management", "issn": "0306-4573", "jcr_if": 8.3, "jcr_quartile": "Q1", "cas_quartile": "2区", "publisher": "Elsevier", "jcr_category": "Computer Science"},
        
        # More Physics journals
        {"title": "Journal of Physics: Conference Series", "issn": "1742-6588", "jcr_if": 0.9, "jcr_quartile": "Q3", "cas_quartile": "4区", "publisher": "IOP Publishing", "jcr_category": "Physics"},
        {"title": "European Physical Journal Plus", "issn": "2190-5444", "jcr_if": 2.6, "jcr_quartile": "Q2", "cas_quartile": "3区", "publisher": "Springer Nature", "jcr_category": "Physics"},
        {"title": "Physica A", "issn": "0378-4371", "jcr_if": 3.3, "jcr_quartile": "Q1", "cas_quartile": "3区", "publisher": "Elsevier", "jcr_category": "Physics"},
        {"title": "Physica B", "issn": "0921-4526", "jcr_if": 2.1, "jcr_quartile": "Q2", "cas_quartile": "4区", "publisher": "Elsevier", "jcr_category": "Physics"},
        {"title": "Physica C", "issn": "0921-4534", "jcr_if": 1.8, "jcr_quartile": "Q2", "cas_quartile": "4区", "publisher": "Elsevier", "jcr_category": "Physics"},
        {"title": "Physica D", "issn": "0167-2789", "jcr_if": 2.5, "jcr_quartile": "Q2", "cas_quartile": "3区", "publisher": "Elsevier", "jcr_category": "Physics"},
        {"title": "Physica E", "issn": "1386-9477", "jcr_if": 3.1, "jcr_quartile": "Q1", "cas_quartile": "3区", "publisher": "Elsevier", "jcr_category": "Physics"},
        {"title": "Physics Reports", "issn": "0370-1573", "jcr_if": 25.6, "jcr_quartile": "Q1", "cas_quartile": "1区", "cas_top": True, "publisher": "Elsevier", "jcr_category": "Physics"},
        {"title": "Physics Letters A", "issn": "0375-9601", "jcr_if": 2.8, "jcr_quartile": "Q1", "cas_quartile": "3区", "publisher": "Elsevier", "jcr_category": "Physics"},
        {"title": "Nuclear Physics A", "issn": "0375-9474", "jcr_if": 2.0, "jcr_quartile": "Q2", "cas_quartile": "4区", "publisher": "Elsevier", "jcr_category": "Physics"},
        
        # More Chemistry journals
        {"title": "Journal of Colloid and Interface Science", "issn": "0021-9797", "jcr_if": 9.9, "jcr_quartile": "Q1", "cas_quartile": "1区", "publisher": "Elsevier", "jcr_category": "Chemistry"},
        {"title": "Colloids and Surfaces A", "issn": "0927-7757", "jcr_if": 5.2, "jcr_quartile": "Q1", "cas_quartile": "2区", "publisher": "Elsevier", "jcr_category": "Chemistry"},
        {"title": "Journal of Catalysis", "issn": "0021-9517", "jcr_if": 8.5, "jcr_quartile": "Q1", "cas_quartile": "2区", "publisher": "Elsevier", "jcr_category": "Chemistry"},
        {"title": "Applied Catalysis A", "issn": "0926-860X", "jcr_if": 5.7, "jcr_quartile": "Q1", "cas_quartile": "2区", "publisher": "Elsevier", "jcr_category": "Chemistry"},
        {"title": "Applied Catalysis B", "issn": "0926-3373", "jcr_if": 22.1, "jcr_quartile": "Q1", "cas_quartile": "1区", "cas_top": True, "publisher": "Elsevier", "jcr_category": "Chemistry"},
        {"title": "Chemical Engineering Science", "issn": "0009-2509", "jcr_if": 5.2, "jcr_quartile": "Q1", "cas_quartile": "2区", "publisher": "Elsevier", "jcr_category": "Chemistry"},
        {"title": "Industrial Crops and Products", "issn": "0926-6690", "jcr_if": 6.4, "jcr_quartile": "Q1", "cas_quartile": "2区", "publisher": "Elsevier", "jcr_category": "Chemistry"},
        {"title": "Food Chemistry", "issn": "0308-8146", "jcr_if": 8.8, "jcr_quartile": "Q1", "cas_quartile": "1区", "publisher": "Elsevier", "jcr_category": "Chemistry"},
        {"title": "Analytical Chemistry", "issn": "0003-2700", "jcr_if": 7.4, "jcr_quartile": "Q1", "cas_quartile": "1区", "publisher": "American Chemical Society", "jcr_category": "Chemistry"},
        {"title": "Environmental Science & Technology Letters", "issn": "2328-8930", "jcr_if": 8.9, "jcr_quartile": "Q1", "cas_quartile": "1区", "publisher": "American Chemical Society", "jcr_category": "Chemistry"},
        
        # More Materials journals
        {"title": "2D Materials", "issn": "2053-1583", "jcr_if": 7.0, "jcr_quartile": "Q1", "cas_quartile": "2区", "publisher": "IOP Publishing", "jcr_category": "Materials Science"},
        {"title": "Materials Today", "issn": "1369-7021", "jcr_if": 24.2, "jcr_quartile": "Q1", "cas_quartile": "1区", "cas_top": True, "publisher": "Elsevier", "jcr_category": "Materials Science"},
        {"title": "Materials Today Communications", "issn": "2352-4928", "jcr_if": 3.8, "jcr_quartile": "Q2", "cas_quartile": "3区", "publisher": "Elsevier", "jcr_category": "Materials Science"},
        {"title": "Materials Today Nano", "issn": "2588-8420", "jcr_if": 5.4, "jcr_quartile": "Q1", "cas_quartile": "2区", "publisher": "Elsevier", "jcr_category": "Materials Science"},
        {"title": "Advanced Energy Materials", "issn": "1614-6832", "jcr_if": 29.4, "jcr_quartile": "Q1", "cas_quartile": "1区", "cas_top": True, "publisher": "Wiley-VCH", "jcr_category": "Materials Science"},
        {"title": "Advanced Optical Materials", "issn": "2195-1071", "jcr_if": 9.9, "jcr_quartile": "Q1", "cas_quartile": "1区", "publisher": "Wiley-VCH", "jcr_category": "Materials Science"},
        {"title": "Advanced Healthcare Materials", "issn": "2192-2640", "jcr_if": 11.1, "jcr_quartile": "Q1", "cas_quartile": "1区", "publisher": "Wiley-VCH", "jcr_category": "Materials Science"},
        {"title": "Advanced Science", "issn": "2198-3844", "jcr_if": 17.5, "jcr_quartile": "Q1", "cas_quartile": "1区", "cas_top": True, "publisher": "Wiley-VCH", "jcr_category": "Materials Science"},
        {"title": "Small Methods", "issn": "2366-9608", "jcr_if": 14.2, "jcr_quartile": "Q1", "cas_quartile": "1区", "publisher": "Wiley-VCH", "jcr_category": "Materials Science"},
        {"title": "Small Structures", "issn": "2688-4062", "jcr_if": 11.8, "jcr_quartile": "Q1", "cas_quartile": "1区", "publisher": "Wiley-VCH", "jcr_category": "Materials Science"},
        
        # More Medicine journals
        {"title": "Nature Biomedical Engineering", "issn": "2157-846X", "jcr_if": 29.2, "jcr_quartile": "Q1", "cas_quartile": "1区", "cas_top": True, "publisher": "Nature Publishing Group", "jcr_category": "Medicine"},
        {"title": "Nature Cardiovascular Research", "issn": "2731-0590", "jcr_if": 13.4, "jcr_quartile": "Q1", "cas_quartile": "1区", "publisher": "Nature Publishing Group", "jcr_category": "Medicine"},
        {"title": "Nature Cancer", "issn": "2662-1347", "jcr_if": 23.5, "jcr_quartile": "Q1", "cas_quartile": "1区", "cas_top": True, "publisher": "Nature Publishing Group", "jcr_category": "Medicine"},
        {"title": "Nature Metabolism", "issn": "2522-5812", "jcr_if": 20.8, "jcr_quartile": "Q1", "cas_quartile": "1区", "cas_top": True, "publisher": "Nature Publishing Group", "jcr_category": "Medicine"},
        {"title": "Nature Aging", "issn": "2662-8091", "jcr_if": 16.6, "jcr_quartile": "Q1", "cas_quartile": "1区", "publisher": "Nature Publishing Group", "jcr_category": "Medicine"},
        {"title": "Nature Neuroscience", "issn": "1097-6256", "jcr_if": 25.0, "jcr_quartile": "Q1", "cas_quartile": "1区", "cas_top": True, "publisher": "Nature Publishing Group", "jcr_category": "Medicine"},
        {"title": "Nature Immunology", "issn": "1529-2908", "jcr_if": 30.5, "jcr_quartile": "Q1", "cas_quartile": "1区", "cas_top": True, "publisher": "Nature Publishing Group", "jcr_category": "Medicine"},
        {"title": "Nature Genetics", "issn": "1061-4036", "jcr_if": 30.8, "jcr_quartile": "Q1", "cas_quartile": "1区", "cas_top": True, "publisher": "Nature Publishing Group", "jcr_category": "Medicine"},
        {"title": "Science Immunology", "issn": "2470-9468", "jcr_if": 18.6, "jcr_quartile": "Q1", "cas_quartile": "1区", "publisher": "AAAS", "jcr_category": "Medicine"},
        {"title": "Science Translational Medicine", "issn": "1946-6234", "jcr_if": 17.9, "jcr_quartile": "Q1", "cas_quartile": "1区", "cas_top": True, "publisher": "AAAS", "jcr_category": "Medicine"},
    ]
    
    seen_issn = {j.get("issn") for j in base_journals}
    
    for j in additional_journals:
        issn = j.get("issn", "")
        if issn and issn not in seen_issn:
            publisher = j.get("publisher", "")
            journal_entry = {
                "title": j.get("title", ""),
                "issn": issn,
                "publisher": publisher,
                "url": PUBLISHER_URLS.get(publisher, ""),
                "jcr_quartile": j.get("jcr_quartile", "Q1"),
                "jcr_if": j.get("jcr_if", 0),
                "jcr_category": j.get("jcr_category", "Unknown"),
                "cas_quartile": j.get("cas_quartile", "2区"),
                "cas_top": j.get("cas_top", False),
                "ei_indexed": j.get("ei_indexed", True),
                "open_access": j.get("open_access", False),
            }
            base_journals.append(journal_entry)
            seen_issn.add(issn)
    
    return base_journals


def save_database(journals: List[Dict[str, Any]], output_path: str) -> None:
    """Save journal database to JSON file."""
    data = {
        "description": "Comprehensive SCI/EI Journal Database",
        "version": "2024.01",
        "total_journals": len(journals),
        "journals": journals,
    }
    
    Path(output_path).parent.mkdir(parents=True, exist_ok=True)
    
    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)
    
    print(f"Saved {len(journals)} journals to {output_path}")


def generate_report(journals: List[Dict[str, Any]]) -> Dict[str, Any]:
    """Generate statistics report."""
    total = len(journals)
    
    sci_count = sum(1 for j in journals if j.get("jcr_quartile"))
    ei_count = sum(1 for j in journals if j.get("ei_indexed"))
    both_count = sum(1 for j in journals if j.get("jcr_quartile") and j.get("ei_indexed"))
    
    cas_1 = sum(1 for j in journals if j.get("cas_quartile") == "1区")
    cas_2 = sum(1 for j in journals if j.get("cas_quartile") == "2区")
    cas_3 = sum(1 for j in journals if j.get("cas_quartile") == "3区")
    cas_4 = sum(1 for j in journals if j.get("cas_quartile") == "4区")
    cas_top = sum(1 for j in journals if j.get("cas_top"))
    
    q1 = sum(1 for j in journals if j.get("jcr_quartile") == "Q1")
    q2 = sum(1 for j in journals if j.get("jcr_quartile") == "Q2")
    q3 = sum(1 for j in journals if j.get("jcr_quartile") == "Q3")
    q4 = sum(1 for j in journals if j.get("jcr_quartile") == "Q4")
    
    categories = {}
    for j in journals:
        cat = j.get("jcr_category", "Unknown")
        categories[cat] = categories.get(cat, 0) + 1
    
    return {
        "total": total,
        "sci_count": sci_count,
        "ei_count": ei_count,
        "both_count": both_count,
        "cas_partition": {"1区": cas_1, "2区": cas_2, "3区": cas_3, "4区": cas_4, "top": cas_top},
        "jcr_partition": {"Q1": q1, "Q2": q2, "Q3": q3, "Q4": q4},
        "categories": categories,
    }


if __name__ == "__main__":
    journals = generate_full_database()
    journals = add_more_journals(journals)
    
    output_path = Path(__file__).parent / "data" / "journals.json"
    save_database(journals, str(output_path))
    
    report = generate_report(journals)
    print(f"\nDatabase Statistics:")
    print(f"  Total: {report['total']}")
    print(f"  SCI: {report['sci_count']}, EI: {report['ei_count']}, Both: {report['both_count']}")
    print(f"  CAS 1区: {report['cas_partition']['1区']} (Top: {report['cas_partition']['top']})")
    print(f"  CAS 2区: {report['cas_partition']['2区']}")
    print(f"  JCR Q1: {report['jcr_partition']['Q1']}, Q2: {report['jcr_partition']['Q2']}")