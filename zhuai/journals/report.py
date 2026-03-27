"""Journal data collector - fetches comprehensive journal information."""

import asyncio
import json
from datetime import datetime
from pathlib import Path
from typing import List, Optional, Dict, Any

from zhuai.journals.models import JournalInfo, JournalDatabase
from zhuai.journals.manager import JournalManager


class JournalDataCollector:
    """Collects comprehensive journal data from multiple sources."""
    
    def __init__(self, output_dir: str = "./journal_reports"):
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(parents=True, exist_ok=True)
        self.database = JournalDatabase()
    
    def load_all_data(self) -> None:
        """Load all available journal data."""
        data_dir = Path(__file__).parent / "data"
        
        json_file = data_dir / "journals.json"
        if json_file.exists():
            with open(json_file, "r", encoding="utf-8") as f:
                data = json.load(f)
            
            for item in data.get("journals", []):
                journal = JournalInfo(
                    title=item.get("title"),
                    issn=item.get("issn"),
                    eissn=item.get("eissn"),
                    publisher=item.get("publisher"),
                    url=item.get("url"),
                    jcr_quartile=item.get("jcr_quartile"),
                    jcr_if=item.get("jcr_if"),
                    jcr_category=item.get("jcr_category"),
                    jcr_rank=item.get("jcr_rank"),
                    cas_quartile=item.get("cas_quartile"),
                    cas_top=item.get("cas_top", False),
                    ei_indexed=item.get("ei_indexed", False),
                    open_access=item.get("open_access", False),
                    source="Journal Database",
                    last_updated=datetime.now(),
                )
                self.database.add(journal)
        
        print(f"Loaded {len(self.database.journals)} journals")
    
    def generate_comprehensive_report(self) -> str:
        """Generate a comprehensive journal report in Markdown format."""
        report_lines = []
        
        report_lines.append("# 学术期刊分区信息报告")
        report_lines.append("")
        report_lines.append(f"**生成时间**: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        report_lines.append(f"**期刊总数**: {len(self.database.journals)}")
        report_lines.append("")
        
        stats = self.database.statistics()
        
        report_lines.append("## 一、数据统计概览")
        report_lines.append("")
        report_lines.append("### 1.1 整体统计")
        report_lines.append("")
        report_lines.append(f"| 指标 | 数量 |")
        report_lines.append(f"|------|------|")
        report_lines.append(f"| 期刊总数 | {stats['total']} |")
        report_lines.append(f"| SCI期刊 | {stats['sci_journals']} |")
        report_lines.append(f"| EI期刊 | {stats['ei_journals']} |")
        report_lines.append(f"| SCI+EI双收录 | {stats['sci_ei_both']} |")
        report_lines.append(f"| 有官方网站 | {stats['with_url']} |")
        report_lines.append(f"| 有影响因子 | {stats['with_if']} |")
        report_lines.append("")
        
        report_lines.append("### 1.2 中科院分区分布")
        report_lines.append("")
        report_lines.append(f"| 分区 | 数量 | 占比 |")
        report_lines.append(f"|------|------|------|")
        total = max(stats['total'], 1)
        for qu, label in [("1区", "一区"), ("2区", "二区"), ("3区", "三区"), ("4区", "四区")]:
            count = stats.get(f'cas_{qu[0]}qu', 0)
            pct = count / total * 100 if total > 0 else 0
            report_lines.append(f"| {label} ({qu}) | {count} | {pct:.1f}% |")
        report_lines.append("")
        
        report_lines.append("### 1.3 JCR分区分布")
        report_lines.append("")
        report_lines.append(f"| 分区 | 数量 | 占比 |")
        report_lines.append(f"|------|------|------|")
        for q in ["Q1", "Q2", "Q3", "Q4"]:
            count = len(self.database.filter_by_quartile(q))
            pct = count / total * 100 if total > 0 else 0
            report_lines.append(f"| {q} | {count} | {pct:.1f}% |")
        report_lines.append("")
        
        report_lines.append("## 二、中科院一区期刊详细列表")
        report_lines.append("")
        
        top_journals = sorted(
            [j for j in self.database.journals if j.cas_quartile == "1区"],
            key=lambda x: x.jcr_if or 0,
            reverse=True
        )
        
        for i, j in enumerate(top_journals, 1):
            report_lines.append(f"### {i}. {j.title}")
            report_lines.append("")
            report_lines.append("| 属性 | 信息 |")
            report_lines.append("|------|------|")
            report_lines.append(f"| ISSN | {j.issn or 'N/A'} |")
            report_lines.append(f"| E-ISSN | {j.eissn or 'N/A'} |")
            report_lines.append(f"| 出版社 | {j.publisher or 'N/A'} |")
            report_lines.append(f"| 官方网站 | [{j.url}]({j.url}) |" if j.url else "| 官方网站 | N/A |")
            report_lines.append(f"| JCR分区 | {j.jcr_quartile or 'N/A'} |")
            report_lines.append(f"| 影响因子 | {j.jcr_if:.3f} |" if j.jcr_if else "| 影响因子 | N/A |")
            report_lines.append(f"| JCR类别 | {j.jcr_category or 'N/A'} |")
            report_lines.append(f"| 中科院分区 | {j.cas_quartile} {'(顶刊)' if j.cas_top else ''} |")
            report_lines.append(f"| EI收录 | {'是' if j.ei_indexed else '否'} |")
            report_lines.append(f"| 开放获取 | {'是' if j.open_access else '否'} |")
            report_lines.append("")
        
        report_lines.append("## 三、中科院二区期刊详细列表")
        report_lines.append("")
        
        second_journals = sorted(
            [j for j in self.database.journals if j.cas_quartile == "2区"],
            key=lambda x: x.jcr_if or 0,
            reverse=True
        )
        
        if second_journals:
            report_lines.append("| 序号 | 期刊名称 | ISSN | 影响因子 | JCR分区 | 出版社 | 官网 |")
            report_lines.append("|------|----------|------|----------|---------|--------|------|")
            for i, j in enumerate(second_journals, 1):
                url_link = f"[链接]({j.url})" if j.url else "N/A"
                if_val = f"{j.jcr_if:.3f}" if j.jcr_if else "N/A"
                report_lines.append(f"| {i} | {j.title} | {j.issn or 'N/A'} | {if_val} | {j.jcr_quartile or 'N/A'} | {j.publisher or 'N/A'} | {url_link} |")
        else:
            report_lines.append("暂无二区期刊数据")
        report_lines.append("")
        
        report_lines.append("## 四、学科领域分布")
        report_lines.append("")
        
        categories = {}
        for j in self.database.journals:
            cat = j.jcr_category or "未分类"
            if cat not in categories:
                categories[cat] = []
            categories[cat].append(j)
        
        report_lines.append("| 学科领域 | 期刊数量 | 代表期刊 |")
        report_lines.append("|----------|----------|----------|")
        
        for cat, journals in sorted(categories.items(), key=lambda x: len(x[1]), reverse=True):
            rep = journals[0].title if journals else "N/A"
            report_lines.append(f"| {cat} | {len(journals)} | {rep[:30]}... |")
        report_lines.append("")
        
        report_lines.append("## 五、出版商分布")
        report_lines.append("")
        
        publishers = {}
        for j in self.database.journals:
            pub = j.publisher or "未知"
            if pub not in publishers:
                publishers[pub] = []
            publishers[pub].append(j)
        
        report_lines.append("| 出版商 | 期刊数量 | 代表期刊 |")
        report_lines.append("|--------|----------|----------|")
        
        for pub, journals in sorted(publishers.items(), key=lambda x: len(x[1]), reverse=True)[:10]:
            rep = journals[0].title if journals else "N/A"
            report_lines.append(f"| {pub} | {len(journals)} | {rep[:30]}... |")
        report_lines.append("")
        
        report_lines.append("## 六、高影响因子期刊Top 20")
        report_lines.append("")
        
        all_journals_sorted = sorted(
            [j for j in self.database.journals if j.jcr_if],
            key=lambda x: x.jcr_if,
            reverse=True
        )[:20]
        
        report_lines.append("| 排名 | 期刊名称 | 影响因子 | JCR分区 | 中科院分区 |")
        report_lines.append("|------|----------|----------|---------|------------|")
        
        for i, j in enumerate(all_journals_sorted, 1):
            report_lines.append(f"| {i} | {j.title[:40]} | {j.jcr_if:.3f} | {j.jcr_quartile or 'N/A'} | {j.cas_quartile or 'N/A'} |")
        report_lines.append("")
        
        report_lines.append("## 七、数据来源说明")
        report_lines.append("")
        report_lines.append("本报告数据来源于以下渠道：")
        report_lines.append("")
        report_lines.append("1. **JCR (Journal Citation Reports)**")
        report_lines.append("   - 官方网站: https://jcr.clarivate.com/")
        report_lines.append("   - 提供数据: 影响因子、JCR分区、类别排名")
        report_lines.append("   - 更新频率: 每年6月更新")
        report_lines.append("")
        report_lines.append("2. **中科院分区表**")
        report_lines.append("   - 发布机构: 中国科学院文献情报中心")
        report_lines.append("   - 官方网站: https://www.fenqubiao.com/")
        report_lines.append("   - 提供数据: 中科院分区、顶刊标记")
        report_lines.append("   - 更新频率: 每年年底更新")
        report_lines.append("")
        report_lines.append("3. **EI Compendex**")
        report_lines.append("   - 官方网站: https://www.elsevier.com/solutions/engineering-village")
        report_lines.append("   - 提供数据: EI收录状态")
        report_lines.append("")
        report_lines.append("4. **DOAJ (Directory of Open Access Journals)**")
        report_lines.append("   - 官方网站: https://doaj.org/")
        report_lines.append("   - 提供数据: 开放获取期刊信息")
        report_lines.append("")
        report_lines.append("## 八、使用建议")
        report_lines.append("")
        report_lines.append("### 8.1 投稿建议")
        report_lines.append("")
        report_lines.append("- **顶级成果**: 优先选择中科院一区顶刊（如Nature、Science、Cell）")
        report_lines.append("- **重要成果**: 选择中科院一区非顶刊或JCR Q1期刊")
        report_lines.append("- **一般成果**: 选择中科院二区或JCR Q2期刊")
        report_lines.append("- **快速发表**: 可考虑开放获取期刊")
        report_lines.append("")
        report_lines.append("### 8.2 查询建议")
        report_lines.append("")
        report_lines.append("- **LetPub** (https://www.letpub.com.cn/): 综合查询SCI/EI信息")
        report_lines.append("- **中科院分区查询** (https://www.fenqubiao.com/): 官方分区数据")
        report_lines.append("- **JCR查询** (https://jcr.clarivate.com/): 官方影响因子")
        report_lines.append("- **EI查询** (https://www.elsevier.com/): EI收录状态")
        report_lines.append("")
        report_lines.append("---")
        report_lines.append("")
        report_lines.append(f"*报告生成时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}*")
        report_lines.append(f"*工具: Zhuai (拽) - 学术论文搜索工具*")
        
        return "\n".join(report_lines)
    
    def save_report(self, filename: str = "journal_report.md") -> Path:
        """Save report to file."""
        report = self.generate_comprehensive_report()
        filepath = self.output_dir / filename
        
        with open(filepath, "w", encoding="utf-8") as f:
            f.write(report)
        
        print(f"Report saved to: {filepath}")
        return filepath
    
    def export_full_database(self, filename: str = "full_journal_database.json") -> Path:
        """Export full database to JSON."""
        filepath = self.output_dir / filename
        self.database.to_json(str(filepath))
        return filepath


def generate_journal_report(output_dir: str = "./journal_reports") -> Path:
    """Generate comprehensive journal report."""
    collector = JournalDataCollector(output_dir)
    collector.load_all_data()
    return collector.save_report()


if __name__ == "__main__":
    generate_journal_report()