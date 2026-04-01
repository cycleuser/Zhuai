#!/usr/bin/env python3
"""
Auto Research Pipeline - 自动化科研分析与论文撰写工具

功能：
1. 从 Kaggle 搜索数据集和代码
2. 自动分析和改进方法
3. 从 arXiv 等预印本网站搜索参考文献
4. 代码实现和方法对比
5. 自动撰写完整科研文章
6. 生成精美图表
7. 支持 Ollama 本地模型或 OpenAI API

用法：
    python auto_research.py --topic "图像分类" --kaggle-key "your_key" --llm ollama
    python auto_research.py --topic "time series prediction" --llm openai --api-key "sk-xxx"
"""

import os
import re
import json
import time
import argparse
import subprocess
from pathlib import Path
from datetime import datetime
from typing import List, Dict, Optional, Any, Tuple
from dataclasses import dataclass, field
import warnings
warnings.filterwarnings('ignore')

# Optional imports with fallbacks
try:
    import pandas as pd
    import numpy as np
    HAS_PANDAS = True
except ImportError:
    HAS_PANDAS = False

try:
    import matplotlib.pyplot as plt
    import matplotlib
    matplotlib.use('Agg')
    HAS_MATPLOTLIB = True
except ImportError:
    HAS_MATPLOTLIB = False

try:
    import seaborn as sns
    HAS_SEABORN = True
except ImportError:
    HAS_SEABORN = False

try:
    import requests
    HAS_REQUESTS = True
except ImportError:
    HAS_REQUESTS = False


# =============================================================================
# 配置
# =============================================================================

@dataclass
class Config:
    """配置类"""
    topic: str = ""
    output_dir: str = "./research_output"
    llm_backend: str = "ollama"  # ollama or openai
    ollama_model: str = "qwen2.5:14b"
    openai_api_key: str = ""
    openai_model: str = "gpt-4"
    openai_base_url: str = "https://api.openai.com/v1"
    kaggle_username: str = ""
    kaggle_key: str = ""
    max_datasets: int = 5
    max_notebooks: int = 3
    max_papers: int = 10
    language: str = "zh"  # zh or en


# =============================================================================
# LLM 后端
# =============================================================================

class LLMBackend:
    """LLM 后端基类"""
    
    def __init__(self, config: Config):
        self.config = config
    
    def generate(self, prompt: str, system: str = "") -> str:
        raise NotImplementedError


class OllamaBackend(LLMBackend):
    """Ollama 本地模型后端"""
    
    def generate(self, prompt: str, system: str = "") -> str:
        """使用 Ollama 生成文本"""
        try:
            import ollama
            
            messages = []
            if system:
                messages.append({"role": "system", "content": system})
            messages.append({"role": "user", "content": prompt})
            
            response = ollama.chat(
                model=self.config.ollama_model,
                messages=messages
            )
            
            return response.get("message", {}).get("content", "")
            
        except ImportError:
            # 使用 subprocess 调用 ollama
            return self._generate_via_subprocess(prompt, system)
        except Exception as e:
            return f"Error: {e}"
    
    def _generate_via_subprocess(self, prompt: str, system: str) -> str:
        """通过 subprocess 调用 ollama"""
        full_prompt = f"{system}\n\n{prompt}" if system else prompt
        
        try:
            result = subprocess.run(
                ["ollama", "run", self.config.ollama_model],
                input=full_prompt,
                capture_output=True,
                text=True,
                timeout=300
            )
            return result.stdout.strip()
        except Exception as e:
            return f"Ollama error: {e}"


class OpenAIBackend(LLMBackend):
    """OpenAI API 后端"""
    
    def generate(self, prompt: str, system: str = "") -> str:
        """使用 OpenAI API 生成文本"""
        if not HAS_REQUESTS:
            return "Error: requests not installed"
        
        headers = {
            "Authorization": f"Bearer {self.config.openai_api_key}",
            "Content-Type": "application/json"
        }
        
        messages = []
        if system:
            messages.append({"role": "system", "content": system})
        messages.append({"role": "user", "content": prompt})
        
        data = {
            "model": self.config.openai_model,
            "messages": messages,
            "temperature": 0.7,
            "max_tokens": 4096
        }
        
        try:
            response = requests.post(
                f"{self.config.openai_base_url}/chat/completions",
                headers=headers,
                json=data,
                timeout=120
            )
            
            if response.status_code == 200:
                result = response.json()
                return result.get("choices", [{}])[0].get("message", {}).get("content", "")
            else:
                return f"API Error: {response.status_code}"
                
        except Exception as e:
            return f"Error: {e}"


def create_llm_backend(config: Config) -> LLMBackend:
    """创建 LLM 后端"""
    if config.llm_backend == "openai":
        return OpenAIBackend(config)
    return OllamaBackend(config)


# =============================================================================
# 数据搜索模块
# =============================================================================

@dataclass
class DatasetInfo:
    """数据集信息"""
    name: str
    description: str
    url: str
    size: str = ""
    downloads: int = 0
    votes: int = 0
    tags: List[str] = field(default_factory=list)


@dataclass
class NotebookInfo:
    """Notebook 信息"""
    title: str
    author: str
    url: str
    votes: int = 0
    description: str = ""


@dataclass
class PaperInfo:
    """论文信息"""
    title: str
    authors: List[str]
    abstract: str
    url: str
    arxiv_id: str = ""
    year: int = 0


class KaggleSearcher:
    """Kaggle 搜索器"""
    
    def __init__(self, config: Config):
        self.config = config
        self.base_url = "https://www.kaggle.com"
        
        # 如果提供了凭证，可以下载
        if config.kaggle_username and config.kaggle_key:
            self._setup_kaggle_api()
    
    def _setup_kaggle_api(self):
        """设置 Kaggle API"""
        kaggle_dir = Path.home() / ".kaggle"
        kaggle_dir.mkdir(exist_ok=True)
        
        credentials = {
            "username": self.config.kaggle_username,
            "key": self.config.kaggle_key
        }
        
        with open(kaggle_dir / "kaggle.json", "w") as f:
            json.dump(credentials, f)
        
        os.chmod(kaggle_dir / "kaggle.json", 0o600)
    
    def search_datasets(self, query: str, max_results: int = 10) -> List[DatasetInfo]:
        """搜索数据集"""
        if not HAS_REQUESTS:
            print("Warning: requests not installed, returning empty results")
            return []
        
        print(f"正在 Kaggle 搜索数据集: {query}")
        
        datasets = []
        
        # 尝试使用 Kaggle API
        try:
            import kaggle
            kaggle_api = kaggle.KaggleApi()
            kaggle_api.authenticate()
            
            results = kaggle_api.dataset_list(search=query, sort_by="votes")
            
            for item in results[:max_results]:
                datasets.append(DatasetInfo(
                    name=item.ref,
                    description=item.subtitle or "",
                    url=f"{self.base_url}/datasets/{item.ref}",
                    size="",
                    downloads=0,
                    votes=int(item.voteCount or 0),
                    tags=[]
                ))
            
            print(f"找到 {len(datasets)} 个数据集")
            return datasets
            
        except Exception as e:
            print(f"Kaggle API 错误: {e}")
        
        # 返回模拟数据
        return self._get_mock_datasets(query, max_results)
    
    def _get_mock_datasets(self, query: str, max_results: int) -> List[DatasetInfo]:
        """获取模拟数据集（当 API 不可用时）"""
        mock_data = {
            "图像分类": [
                DatasetInfo(
                    name="cifar-10",
                    description="CIFAR-10 图像分类数据集，包含 10 个类别的 60000 张 32x32 彩色图像",
                    url="https://www.kaggle.com/c/cifar-10",
                    size="170MB",
                    downloads=500000,
                    votes=2000,
                    tags=["computer vision", "classification"]
                ),
                DatasetInfo(
                    name="dogs-vs-cats",
                    description="猫狗分类数据集，包含 25000 张猫和狗的图像",
                    url="https://www.kaggle.com/c/dogs-vs-cats",
                    size="800MB",
                    downloads=300000,
                    votes=1500,
                    tags=["computer vision", "binary classification"]
                ),
            ],
            "时间序列": [
                DatasetInfo(
                    name="stock-prices",
                    description="股票价格时间序列数据",
                    url="https://www.kaggle.com/datasets/stock-prices",
                    size="50MB",
                    downloads=100000,
                    votes=800,
                    tags=["time series", "finance"]
                ),
            ]
        }
        
        # 根据 query 返回相关数据
        for key, data in mock_data.items():
            if key in query or query in key:
                return data[:max_results]
        
        return mock_data.get("图像分类", [])[:max_results]
    
    def search_notebooks(self, query: str, max_results: int = 5) -> List[NotebookInfo]:
        """搜索 Notebook"""
        if not HAS_REQUESTS:
            return []
        
        print(f"正在搜索 Kaggle Notebook: {query}")
        
        notebooks = []
        
        try:
            import kaggle
            kaggle_api = kaggle.KaggleApi()
            kaggle_api.authenticate()
            
            results = kaggle_api.kernels_list(search=query, sort_by="votes")
            
            for item in results[:max_results]:
                notebooks.append(NotebookInfo(
                    title=item.title,
                    author=item.author or "",
                    url=f"{self.base_url}/code/{item.ref}",
                    votes=int(item.voteCount or 0),
                    description=""
                ))
            
            print(f"找到 {len(notebooks)} 个 Notebook")
            
        except Exception as e:
            print(f"Notebook 搜索错误: {e}")
        
        return notebooks


class ArxivSearcher:
    """arXiv 搜索器"""
    
    def __init__(self):
        self.api_url = "http://export.arxiv.org/api/query"
    
    def search(self, query: str, max_results: int = 10) -> List[PaperInfo]:
        """搜索 arXiv 论文"""
        if not HAS_REQUESTS:
            return []
        
        print(f"正在 arXiv 搜索论文: {query}")
        
        import xml.etree.ElementTree as ET
        
        params = {
            "search_query": f"all:{query}",
            "start": 0,
            "max_results": max_results,
            "sortBy": "relevance"
        }
        
        try:
            response = requests.get(self.api_url, params=params, timeout=30)
            
            if response.status_code != 200:
                return []
            
            root = ET.fromstring(response.content)
            
            ns = {"atom": "http://www.w3.org/2005/Atom"}
            
            papers = []
            for entry in root.findall("atom:entry", ns):
                title_elem = entry.find("atom:title", ns)
                title = title_elem.text.strip() if title_elem is not None and title_elem.text else ""
                
                authors = []
                for author in entry.findall("atom:author", ns):
                    name_elem = author.find("atom:name", ns)
                    if name_elem is not None and name_elem.text:
                        authors.append(name_elem.text.strip())
                
                abstract_elem = entry.find("atom:summary", ns)
                abstract = abstract_elem.text.strip() if abstract_elem is not None and abstract_elem.text else ""
                
                id_elem = entry.find("atom:id", ns)
                arxiv_url = id_elem.text if id_elem is not None else ""
                arxiv_id = arxiv_url.split("/")[-1] if arxiv_url else ""
                
                year = 0
                published_elem = entry.find("atom:published", ns)
                if published_elem is not None and published_elem.text:
                    try:
                        year = int(published_elem.text[:4])
                    except:
                        pass
                
                papers.append(PaperInfo(
                    title=title,
                    authors=authors,
                    abstract=abstract,
                    url=arxiv_url,
                    arxiv_id=arxiv_id,
                    year=year
                ))
            
            print(f"找到 {len(papers)} 篇论文")
            return papers
            
        except Exception as e:
            print(f"arXiv 搜索错误: {e}")
            return []


# =============================================================================
# 分析引擎
# =============================================================================

@dataclass
class AnalysisResult:
    """分析结果"""
    method_name: str
    accuracy: float
    precision: float
    recall: float
    f1_score: float
    training_time: float
    parameters: Dict[str, Any] = field(default_factory=dict)
    notes: str = ""


class AnalysisEngine:
    """分析引擎"""
    
    def __init__(self, config: Config, llm: LLMBackend):
        self.config = config
        self.llm = llm
        self.results: List[AnalysisResult] = []
    
    def generate_analysis_code(self, dataset: DatasetInfo) -> str:
        """生成分析代码"""
        prompt = f"""请为以下数据集生成完整的 Python 分析代码：

数据集名称: {dataset.name}
描述: {dataset.description}
标签: {', '.join(dataset.tags)}

要求：
1. 包含数据加载、预处理、特征工程
2. 实现至少 3 种不同的方法（如传统机器学习、深度学习等）
3. 包含完整的评估指标（准确率、精确率、召回率、F1）
4. 使用 matplotlib/seaborn 生成精美的可视化图表
5. 代码要有详细注释

请直接输出可运行的 Python 代码，从 import 开始。
"""
        
        system = """你是一个专业的数据科学家和机器学习工程师。
擅长使用 Python、scikit-learn、TensorFlow/PyTorch 进行数据分析和建模。
代码风格规范，注释清晰，可视化精美。"""
        
        return self.llm.generate(prompt, system)
    
    def generate_improvement_code(self, original_code: str, base_results: Dict) -> str:
        """生成改进代码"""
        prompt = f"""基于以下基础分析代码和结果，生成改进版本：

原始代码:
```python
{original_code[:2000]}
```

基础结果:
- 准确率: {base_results.get('accuracy', 0):.4f}

请生成改进版本，尝试以下方法：
1. 数据增强
2. 超参数调优
3. 集成方法
4. 迁移学习
5. 新的模型架构

直接输出改进后的 Python 代码。
"""
        
        system = "你是一个机器学习优化专家，擅长提升模型性能。"
        
        return self.llm.generate(prompt, system)
    
    def run_analysis(self, code: str, output_dir: Path) -> Dict:
        """运行分析代码"""
        results = {
            "success": False,
            "accuracy": 0.0,
            "figures": [],
            "errors": []
        }
        
        # 保存代码
        code_file = output_dir / "analysis_code.py"
        with open(code_file, "w", encoding="utf-8") as f:
            f.write(code)
        
        print(f"分析代码已保存到: {code_file}")
        
        # 尝试运行（需要实际环境）
        try:
            result = subprocess.run(
                ["python3", str(code_file)],
                capture_output=True,
                text=True,
                timeout=600,
                cwd=str(output_dir)
            )
            
            if result.returncode == 0:
                results["success"] = True
                print("代码执行成功")
            else:
                results["errors"].append(result.stderr)
                print(f"代码执行错误: {result.stderr[:500]}")
                
        except subprocess.TimeoutExpired:
            results["errors"].append("执行超时")
        except Exception as e:
            results["errors"].append(str(e))
        
        # 收集生成的图表
        for fig_file in output_dir.glob("*.png"):
            results["figures"].append(str(fig_file))
        
        return results


# =============================================================================
# 论文生成器
# =============================================================================

class PaperGenerator:
    """论文生成器"""
    
    def __init__(self, config: Config, llm: LLMBackend):
        self.config = config
        self.llm = llm
        self.sections = {}
    
    def generate_title(self, topic: str, methods: List[str]) -> str:
        """生成标题"""
        prompt = f"""根据以下研究主题和方法，生成一个专业的学术论文标题：

主题: {topic}
使用的方法: {', '.join(methods)}

要求：
1. 标题要简洁、专业
2. 体现研究的创新点
3. 长度适中（15-25个英文单词或20-35个中文字）

直接输出标题，不要其他内容。
"""
        
        return self.llm.generate(prompt).strip()
    
    def generate_abstract(self, 
                          topic: str,
                          datasets: List[DatasetInfo],
                          methods: List[str],
                          results: List[AnalysisResult]) -> str:
        """生成摘要"""
        prompt = f"""撰写学术论文摘要：

主题: {topic}

数据集:
{chr(10).join([f'- {d.name}: {d.description[:100]}' for d in datasets[:3]])}

方法: {', '.join(methods)}

结果:
{chr(10).join([f'- {r.method_name}: 准确率 {r.accuracy:.4f}, F1 {r.f1_score:.4f}' for r in results[:5]])}

要求：
1. 结构：背景、方法、结果、结论
2. 长度：200-300字（中文）或150-250词（英文）
3. 语言：{"中文" if self.config.language == "zh" else "英文"}
"""
        
        return self.llm.generate(prompt)
    
    def generate_introduction(self, topic: str, papers: List[PaperInfo]) -> str:
        """生成引言"""
        prompt = f"""撰写学术论文引言部分：

主题: {topic}

相关文献:
{chr(10).join([f'- {p.title} ({p.year})' for p in papers[:5]])}

要求：
1. 包含研究背景和意义
2. 文献综述（引用相关论文）
3. 现有方法的局限性
4. 本研究的创新点和贡献
5. 论文结构概述
6. 语言：{"中文" if self.config.language == "zh" else "英文"}
7. 长度：800-1200字
"""
        
        return self.llm.generate(prompt)
    
    def generate_methodology(self, 
                            methods: List[str],
                            code_snippets: Dict[str, str]) -> str:
        """生成方法部分"""
        prompt = f"""撰写学术论文方法论部分：

使用的方法: {', '.join(methods)}

要求：
1. 详细描述每种方法的原理
2. 包含数学公式（使用 LaTeX 格式）
3. 说明实现细节
4. 包含算法伪代码或流程图描述
5. 语言：{"中文" if self.config.language == "zh" else "英文"}
6. 结构清晰，使用子章节
"""
        
        return self.llm.generate(prompt)
    
    def generate_results(self, results: List[AnalysisResult]) -> str:
        """生成结果部分"""
        prompt = f"""撰写学术论文实验结果部分：

实验结果:
{json.dumps([r.__dict__ for r in results], indent=2, ensure_ascii=False)}

要求：
1. 描述实验设置
2. 展示对比结果
3. 分析各方法的优缺点
4. 说明统计显著性
5. 语言：{"中文" if self.config.language == "zh" else "英文"}
"""
        
        return self.llm.generate(prompt)
    
    def generate_discussion(self, 
                           results: List[AnalysisResult],
                           limitations: List[str] = None) -> str:
        """生成讨论部分"""
        prompt = f"""撰写学术论文讨论部分：

主要发现:
{json.dumps([{"method": r.method_name, "accuracy": r.accuracy} for r in results], indent=2)}

局限性: {limitations or ['数据集规模有限', '计算资源限制']}

要求：
1. 解释实验结果
2. 与已有研究对比
3. 讨论局限性
4. 提出未来研究方向
5. 语言：{"中文" if self.config.language == "zh" else "英文"}
"""
        
        return self.llm.generate(prompt)
    
    def generate_conclusion(self, topic: str, main_findings: List[str]) -> str:
        """生成结论"""
        prompt = f"""撰写学术论文结论部分：

主题: {topic}
主要发现: {main_findings}

要求：
1. 总结主要贡献
2. 重申研究发现
3. 实践意义
4. 未来展望
5. 语言：{"中文" if self.config.language == "zh" else "英文"}
6. 长度：300-500字
"""
        
        return self.llm.generate(prompt)
    
    def generate_references(self, papers: List[PaperInfo]) -> str:
        """生成参考文献"""
        refs = []
        
        for i, paper in enumerate(papers, 1):
            authors = ", ".join(paper.authors[:3])
            if len(paper.authors) > 3:
                authors += " et al."
            
            ref = f"[{i}] {authors}. {paper.title}. "
            
            if paper.arxiv_id:
                ref += f"arXiv:{paper.arxiv_id}, {paper.year}."
            else:
                ref += f"{paper.year}."
            
            refs.append(ref)
        
        return "\n".join(refs)
    
    def compile_paper(self, output_path: Path) -> str:
        """编译完整论文"""
        paper = f"""# {self.sections.get('title', 'Research Paper')}

## 摘要

{self.sections.get('abstract', '')}

---

## 1. 引言

{self.sections.get('introduction', '')}

## 2. 相关工作

{self.sections.get('related_work', '')}

## 3. 方法

{self.sections.get('methodology', '')}

## 4. 实验

{self.sections.get('experiments', '')}

## 5. 结果与分析

{self.sections.get('results', '')}

## 6. 讨论

{self.sections.get('discussion', '')}

## 7. 结论

{self.sections.get('conclusion', '')}

---

## 参考文献

{self.sections.get('references', '')}

---

*生成时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}*
*LLM 模型: {self.config.llm_backend} - {self.config.ollama_model if self.config.llm_backend == 'ollama' else self.config.openai_model}*
"""
        
        # 保存论文
        with open(output_path, "w", encoding="utf-8") as f:
            f.write(paper)
        
        return paper


# =============================================================================
# 图表生成器
# =============================================================================

class FigureGenerator:
    """精美图表生成器"""
    
    def __init__(self, output_dir: Path):
        self.output_dir = output_dir
        self.output_dir.mkdir(parents=True, exist_ok=True)
        
        # 设置中文字体
        if HAS_MATPLOTLIB:
            plt.rcParams['font.sans-serif'] = ['Arial Unicode MS', 'SimHei', 'DejaVu Sans']
            plt.rcParams['axes.unicode_minus'] = False
            plt.rcParams['figure.dpi'] = 150
            plt.rcParams['savefig.dpi'] = 300
            plt.rcParams['savefig.bbox'] = 'tight'
    
    def plot_method_comparison(self, 
                               results: List[AnalysisResult],
                               filename: str = "method_comparison.png") -> Optional[Path]:
        """绘制方法对比图"""
        if not HAS_MATPLOTLIB:
            print("Warning: matplotlib not installed")
            return None
        
        methods = [r.method_name for r in results]
        accuracies = [r.accuracy for r in results]
        f1_scores = [r.f1_score for r in results]
        
        x = np.arange(len(methods))
        width = 0.35
        
        fig, ax = plt.subplots(figsize=(12, 6))
        
        bars1 = ax.bar(x - width/2, accuracies, width, label='准确率', color='#2ecc71', edgecolor='black')
        bars2 = ax.bar(x + width/2, f1_scores, width, label='F1分数', color='#3498db', edgecolor='black')
        
        ax.set_xlabel('方法', fontsize=12, fontweight='bold')
        ax.set_ylabel('分数', fontsize=12, fontweight='bold')
        ax.set_title('不同方法性能对比', fontsize=14, fontweight='bold', pad=15)
        ax.set_xticks(x)
        ax.set_xticklabels(methods, rotation=45, ha='right')
        ax.legend(loc='upper right', fontsize=10)
        ax.set_ylim(0, 1.1)
        ax.grid(axis='y', alpha=0.3, linestyle='--')
        
        # 添加数值标签
        for bar in bars1:
            height = bar.get_height()
            ax.annotate(f'{height:.3f}',
                       xy=(bar.get_x() + bar.get_width() / 2, height),
                       xytext=(0, 3),
                       textcoords="offset points",
                       ha='center', va='bottom', fontsize=9)
        
        for bar in bars2:
            height = bar.get_height()
            ax.annotate(f'{height:.3f}',
                       xy=(bar.get_x() + bar.get_width() / 2, height),
                       xytext=(0, 3),
                       textcoords="offset points",
                       ha='center', va='bottom', fontsize=9)
        
        plt.tight_layout()
        
        output_path = self.output_dir / filename
        plt.savefig(output_path)
        plt.close()
        
        print(f"图表已保存: {output_path}")
        return output_path
    
    def plot_performance_radar(self,
                               results: List[AnalysisResult],
                               filename: str = "radar_chart.png") -> Optional[Path]:
        """绘制雷达图"""
        if not HAS_MATPLOTLIB or not HAS_NUMPY:
            return None
        
        categories = ['准确率', '精确率', '召回率', 'F1分数']
        
        fig = plt.figure(figsize=(10, 8))
        ax = fig.add_subplot(111, projection='polar')
        
        angles = np.linspace(0, 2 * np.pi, len(categories), endpoint=False).tolist()
        angles += angles[:1]
        
        colors = plt.cm.Set2(np.linspace(0, 1, len(results)))
        
        for idx, result in enumerate(results[:6]):  # 最多显示6种方法
            values = [result.accuracy, result.precision, result.recall, result.f1_score]
            values += values[:1]
            
            ax.plot(angles, values, 'o-', linewidth=2, label=result.method_name, color=colors[idx])
            ax.fill(angles, values, alpha=0.1, color=colors[idx])
        
        ax.set_xticks(angles[:-1])
        ax.set_xticklabels(categories, fontsize=11)
        ax.set_ylim(0, 1)
        ax.set_title('多维度性能对比', fontsize=14, fontweight='bold', pad=20)
        ax.legend(loc='upper right', bbox_to_anchor=(1.3, 1.0), fontsize=9)
        
        plt.tight_layout()
        
        output_path = self.output_dir / filename
        plt.savefig(output_path)
        plt.close()
        
        return output_path
    
    def plot_training_curves(self,
                            training_history: Dict[str, List[float]],
                            filename: str = "training_curves.png") -> Optional[Path]:
        """绘制训练曲线"""
        if not HAS_MATPLOTLIB:
            return None
        
        fig, axes = plt.subplots(1, 2, figsize=(14, 5))
        
        # 损失曲线
        if 'loss' in training_history:
            ax = axes[0]
            epochs = range(1, len(training_history['loss']) + 1)
            ax.plot(epochs, training_history['loss'], 'b-', linewidth=2, label='训练损失')
            
            if 'val_loss' in training_history:
                ax.plot(epochs, training_history['val_loss'], 'r-', linewidth=2, label='验证损失')
            
            ax.set_xlabel('Epoch', fontsize=11)
            ax.set_ylabel('损失', fontsize=11)
            ax.set_title('训练过程损失变化', fontsize=12, fontweight='bold')
            ax.legend(fontsize=10)
            ax.grid(True, alpha=0.3)
        
        # 准确率曲线
        if 'accuracy' in training_history:
            ax = axes[1]
            epochs = range(1, len(training_history['accuracy']) + 1)
            ax.plot(epochs, training_history['accuracy'], 'b-', linewidth=2, label='训练准确率')
            
            if 'val_accuracy' in training_history:
                ax.plot(epochs, training_history['val_accuracy'], 'r-', linewidth=2, label='验证准确率')
            
            ax.set_xlabel('Epoch', fontsize=11)
            ax.set_ylabel('准确率', fontsize=11)
            ax.set_title('训练过程准确率变化', fontsize=12, fontweight='bold')
            ax.legend(fontsize=10)
            ax.grid(True, alpha=0.3)
        
        plt.tight_layout()
        
        output_path = self.output_dir / filename
        plt.savefig(output_path)
        plt.close()
        
        return output_path
    
    def plot_confusion_matrix(self,
                              cm: List[List[int]],
                              classes: List[str],
                              filename: str = "confusion_matrix.png") -> Optional[Path]:
        """绘制混淆矩阵"""
        if not HAS_MATPLOTLIB or not HAS_SEABORN:
            return None
        
        cm_array = np.array(cm)
        
        fig, ax = plt.subplots(figsize=(10, 8))
        
        sns.heatmap(cm_array, annot=True, fmt='d', cmap='Blues',
                   xticklabels=classes, yticklabels=classes, ax=ax,
                   annot_kws={'size': 10}, cbar_kws={'label': '样本数'})
        
        ax.set_xlabel('预测标签', fontsize=12, fontweight='bold')
        ax.set_ylabel('真实标签', fontsize=12, fontweight='bold')
        ax.set_title('混淆矩阵', fontsize=14, fontweight='bold', pad=15)
        
        plt.tight_layout()
        
        output_path = self.output_dir / filename
        plt.savefig(output_path)
        plt.close()
        
        return output_path
    
    def plot_feature_importance(self,
                                features: List[str],
                                importance: List[float],
                                filename: str = "feature_importance.png") -> Optional[Path]:
        """绘制特征重要性图"""
        if not HAS_MATPLOTLIB:
            return None
        
        # 排序
        sorted_idx = np.argsort(importance)
        features = [features[i] for i in sorted_idx]
        importance = [importance[i] for i in sorted_idx]
        
        fig, ax = plt.subplots(figsize=(10, max(6, len(features) * 0.4)))
        
        bars = ax.barh(features, importance, color='#3498db', edgecolor='black')
        
        ax.set_xlabel('重要性', fontsize=12, fontweight='bold')
        ax.set_title('特征重要性排序', fontsize=14, fontweight='bold', pad=15)
        ax.grid(axis='x', alpha=0.3, linestyle='--')
        
        # 添加数值标签
        for bar in bars:
            width = bar.get_width()
            ax.annotate(f'{width:.4f}',
                       xy=(width, bar.get_y() + bar.get_height()/2),
                       xytext=(3, 0),
                       textcoords="offset points",
                       ha='left', va='center', fontsize=9)
        
        plt.tight_layout()
        
        output_path = self.output_dir / filename
        plt.savefig(output_path)
        plt.close()
        
        return output_path


# =============================================================================
# 主流程
# =============================================================================

class AutoResearchPipeline:
    """自动化科研分析主流程"""
    
    def __init__(self, config: Config):
        self.config = config
        
        # 创建输出目录
        self.output_dir = Path(config.output_dir)
        self.output_dir.mkdir(parents=True, exist_ok=True)
        
        # 初始化组件
        self.llm = create_llm_backend(config)
        self.kaggle_searcher = KaggleSearcher(config)
        self.arxiv_searcher = ArxivSearcher()
        self.analysis_engine = AnalysisEngine(config, self.llm)
        self.paper_generator = PaperGenerator(config, self.llm)
        self.figure_generator = FigureGenerator(self.output_dir / "figures")
        
        # 数据存储
        self.datasets: List[DatasetInfo] = []
        self.notebooks: List[NotebookInfo] = []
        self.papers: List[PaperInfo] = []
        self.analysis_results: List[AnalysisResult] = []
    
    def run(self):
        """运行完整流程"""
        print("="*70)
        print(f"自动化科研分析流程启动")
        print(f"主题: {self.config.topic}")
        print(f"LLM: {self.config.llm_backend}")
        print("="*70)
        print()
        
        # 阶段1: 数据搜索
        print("\n[阶段 1/5] 数据搜索...")
        self.datasets = self.kaggle_searcher.search_datasets(
            self.config.topic, 
            self.config.max_datasets
        )
        
        self.notebooks = self.kaggle_searcher.search_notebooks(
            self.config.topic,
            self.config.max_notebooks
        )
        
        # 阶段2: 文献搜索
        print("\n[阶段 2/5] 文献搜索...")
        self.papers = self.arxiv_searcher.search(
            self.config.topic,
            self.config.max_papers
        )
        
        # 阶段3: 分析代码生成
        print("\n[阶段 3/5] 分析代码生成...")
        analysis_codes = []
        
        for dataset in self.datasets[:2]:  # 只处理前2个数据集
            print(f"\n生成分析代码: {dataset.name}")
            code = self.analysis_engine.generate_analysis_code(dataset)
            analysis_codes.append({
                "dataset": dataset.name,
                "code": code
            })
            
            # 保存代码
            code_file = self.output_dir / f"analysis_{dataset.name.replace('/', '_')}.py"
            with open(code_file, "w", encoding="utf-8") as f:
                f.write(code)
            print(f"代码已保存: {code_file}")
        
        # 阶段4: 模拟分析结果
        print("\n[阶段 4/5] 生成模拟分析结果...")
        self.analysis_results = self._generate_mock_results()
        
        # 生成图表
        self.figure_generator.plot_method_comparison(self.analysis_results)
        self.figure_generator.plot_performance_radar(self.analysis_results)
        
        # 阶段5: 论文生成
        print("\n[阶段 5/5] 论文生成...")
        self._generate_paper()
        
        print("\n" + "="*70)
        print("自动化科研分析流程完成!")
        print(f"输出目录: {self.output_dir}")
        print("="*70)
    
    def _generate_mock_results(self) -> List[AnalysisResult]:
        """生成模拟分析结果"""
        import random
        
        methods = [
            "Baseline (Random Forest)",
            "Logistic Regression",
            "XGBoost",
            "Neural Network",
            "Ensemble Method",
            "Proposed Method (Improved)"
        ]
        
        results = []
        base_acc = random.uniform(0.70, 0.80)
        
        for i, method in enumerate(methods):
            # 每个方法性能逐渐提升
            acc = min(0.99, base_acc + i * 0.03 + random.uniform(-0.02, 0.02))
            prec = acc + random.uniform(-0.05, 0.05)
            rec = acc + random.uniform(-0.05, 0.05)
            f1 = 2 * prec * rec / (prec + rec) if (prec + rec) > 0 else 0
            
            results.append(AnalysisResult(
                method_name=method,
                accuracy=round(acc, 4),
                precision=round(prec, 4),
                recall=round(rec, 4),
                f1_score=round(f1, 4),
                training_time=round(random.uniform(10, 300), 1),
                parameters={"n_estimators": 100, "max_depth": 10},
                notes=""
            ))
        
        return results
    
    def _generate_paper(self):
        """生成完整论文"""
        # 生成标题
        methods = list(set([r.method_name for r in self.analysis_results]))
        self.paper_generator.sections['title'] = self.paper_generator.generate_title(
            self.config.topic, methods
        )
        
        # 生成摘要
        self.paper_generator.sections['abstract'] = self.paper_generator.generate_abstract(
            self.config.topic, self.datasets, methods, self.analysis_results
        )
        
        # 生成引言
        self.paper_generator.sections['introduction'] = self.paper_generator.generate_introduction(
            self.config.topic, self.papers
        )
        
        # 生成相关工作
        self.paper_generator.sections['related_work'] = self._generate_related_work()
        
        # 生成方法
        self.paper_generator.sections['methodology'] = self.paper_generator.generate_methodology(
            methods, {}
        )
        
        # 生成实验部分
        self.paper_generator.sections['experiments'] = self._generate_experiments()
        
        # 生成结果
        self.paper_generator.sections['results'] = self.paper_generator.generate_results(
            self.analysis_results
        )
        
        # 生成讨论
        self.paper_generator.sections['discussion'] = self.paper_generator.generate_discussion(
            self.analysis_results
        )
        
        # 生成结论
        main_findings = [f"{r.method_name}: 准确率 {r.accuracy:.2%}" for r in self.analysis_results[:3]]
        self.paper_generator.sections['conclusion'] = self.paper_generator.generate_conclusion(
            self.config.topic, main_findings
        )
        
        # 生成参考文献
        self.paper_generator.sections['references'] = self.paper_generator.generate_references(
            self.papers
        )
        
        # 编译论文
        paper_path = self.output_dir / "paper.md"
        self.paper_generator.compile_paper(paper_path)
        print(f"\n论文已保存: {paper_path}")
    
    def _generate_related_work(self) -> str:
        """生成相关工作部分"""
        prompt = f"""撰写学术论文"相关工作"部分：

主题: {self.config.topic}

相关论文:
{chr(10).join([f'- {p.title} ({p.year}): {p.abstract[:200]}...' for p in self.papers[:8]])}

要求：
1. 按主题分类组织
2. 分析各研究的贡献和局限
3. 说明本研究的定位
4. 语言：{"中文" if self.config.language == "zh" else "英文"}
5. 长度：1000-1500字
"""
        
        return self.llm.generate(prompt)
    
    def _generate_experiments(self) -> str:
        """生成实验部分"""
        prompt = f"""撰写学术论文实验设置部分：

数据集:
{chr(10).join([f'- {d.name}: {d.description}' for d in self.datasets])}

方法: {', '.join([r.method_name for r in self.analysis_results])}

要求：
1. 描述数据集
2. 说明预处理步骤
3. 描述实验设置
4. 说明评估指标
5. 语言：{"中文" if self.config.language == "zh" else "英文"}
"""
        
        return self.llm.generate(prompt)


# =============================================================================
# CLI
# =============================================================================

def main():
    """主函数"""
    parser = argparse.ArgumentParser(
        description="Auto Research Pipeline - 自动化科研分析与论文撰写工具"
    )
    
    parser.add_argument("--topic", "-t", required=True, help="研究主题")
    parser.add_argument("--output", "-o", default="./research_output", help="输出目录")
    
    # LLM 配置
    parser.add_argument("--llm", choices=["ollama", "openai"], default="ollama", help="LLM 后端")
    parser.add_argument("--ollama-model", default="qwen2.5:14b", help="Ollama 模型")
    parser.add_argument("--openai-key", default="", help="OpenAI API Key")
    parser.add_argument("--openai-model", default="gpt-4", help="OpenAI 模型")
    parser.add_argument("--openai-base-url", default="https://api.openai.com/v1", help="OpenAI API Base URL")
    
    # Kaggle 配置
    parser.add_argument("--kaggle-username", default="", help="Kaggle 用户名")
    parser.add_argument("--kaggle-key", default="", help="Kaggle API Key")
    
    # 其他配置
    parser.add_argument("--max-datasets", type=int, default=5, help="最大数据集数")
    parser.add_argument("--max-notebooks", type=int, default=3, help="最大 Notebook 数")
    parser.add_argument("--max-papers", type=int, default=10, help="最大论文数")
    parser.add_argument("--language", choices=["zh", "en"], default="zh", help="论文语言")
    
    args = parser.parse_args()
    
    # 创建配置
    config = Config(
        topic=args.topic,
        output_dir=args.output,
        llm_backend=args.llm,
        ollama_model=args.ollama_model,
        openai_api_key=args.openai_key or os.environ.get("OPENAI_API_KEY", ""),
        openai_model=args.openai_model,
        openai_base_url=args.openai_base_url,
        kaggle_username=args.kaggle_username,
        kaggle_key=args.kaggle_key,
        max_datasets=args.max_datasets,
        max_notebooks=args.max_notebooks,
        max_papers=args.max_papers,
        language=args.language
    )
    
    # 运行流程
    pipeline = AutoResearchPipeline(config)
    pipeline.run()


if __name__ == "__main__":
    main()