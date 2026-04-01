#!/usr/bin/env python3
"""
Research Agent Web Interface - 自动化科研分析 Web 系统

启动:
    python research_agent_web.py
    
访问:
    http://localhost:5000
"""

import os
import sys
import json
import threading
import queue
from pathlib import Path
from datetime import datetime
from typing import Dict, List, Optional, Any
from dataclasses import dataclass, asdict
from flask import Flask, render_template_string, request, jsonify, send_from_directory, stream_with_context, Response

# 添加父目录到路径以导入 research_agent
sys.path.insert(0, str(Path(__file__).parent))

from research_agent import (
    Config, ResearchAgent, DependencyChecker,
    Dataset, Notebook, Paper, AnalysisResult
)

# =============================================================================
# Flask 应用
# =============================================================================

app = Flask(__name__)
app.config['MAX_CONTENT_LENGTH'] = 100 * 1024 * 1024  # 100MB

# 全局状态
running_jobs: Dict[str, Dict] = {}
completed_jobs: Dict[str, Dict] = {}
job_queue = queue.Queue()

# =============================================================================
# HTML 模板
# =============================================================================

HTML_TEMPLATE = """
<!DOCTYPE html>
<html lang="zh-CN">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Research Agent - 自动化科研分析系统</title>
    <style>
        * {
            margin: 0;
            padding: 0;
            box-sizing: border-box;
        }
        
        body {
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, 'Helvetica Neue', Arial, sans-serif;
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            min-height: 100vh;
            padding: 20px;
        }
        
        .container {
            max-width: 1200px;
            margin: 0 auto;
        }
        
        .header {
            text-align: center;
            color: white;
            margin-bottom: 30px;
        }
        
        .header h1 {
            font-size: 2.5em;
            margin-bottom: 10px;
            text-shadow: 2px 2px 4px rgba(0,0,0,0.3);
        }
        
        .header p {
            font-size: 1.1em;
            opacity: 0.9;
        }
        
        .card {
            background: white;
            border-radius: 12px;
            padding: 25px;
            margin-bottom: 20px;
            box-shadow: 0 10px 40px rgba(0,0,0,0.2);
        }
        
        .card h2 {
            color: #333;
            margin-bottom: 20px;
            font-size: 1.4em;
            border-bottom: 2px solid #667eea;
            padding-bottom: 10px;
        }
        
        .form-group {
            margin-bottom: 20px;
        }
        
        .form-group label {
            display: block;
            margin-bottom: 8px;
            font-weight: 600;
            color: #555;
        }
        
        .form-group input,
        .form-group select,
        .form-group textarea {
            width: 100%;
            padding: 12px 15px;
            border: 2px solid #e0e0e0;
            border-radius: 8px;
            font-size: 14px;
            transition: border-color 0.3s;
        }
        
        .form-group input:focus,
        .form-group select:focus,
        .form-group textarea:focus {
            outline: none;
            border-color: #667eea;
        }
        
        .form-row {
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
            gap: 15px;
        }
        
        .btn {
            display: inline-block;
            padding: 14px 30px;
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            color: white;
            border: none;
            border-radius: 8px;
            font-size: 16px;
            font-weight: 600;
            cursor: pointer;
            transition: transform 0.2s, box-shadow 0.2s;
        }
        
        .btn:hover {
            transform: translateY(-2px);
            box-shadow: 0 5px 20px rgba(102, 126, 234, 0.4);
        }
        
        .btn:disabled {
            opacity: 0.6;
            cursor: not-allowed;
            transform: none;
        }
        
        .btn-secondary {
            background: #6c757d;
        }
        
        .progress-container {
            display: none;
            margin-top: 20px;
        }
        
        .progress-bar {
            height: 8px;
            background: #e0e0e0;
            border-radius: 4px;
            overflow: hidden;
            margin-bottom: 15px;
        }
        
        .progress-fill {
            height: 100%;
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            width: 0%;
            transition: width 0.3s;
        }
        
        .progress-text {
            color: #666;
            font-size: 14px;
        }
        
        .log-container {
            background: #1e1e1e;
            color: #d4d4d4;
            padding: 15px;
            border-radius: 8px;
            font-family: 'Consolas', 'Monaco', monospace;
            font-size: 13px;
            max-height: 300px;
            overflow-y: auto;
            margin-top: 15px;
        }
        
        .log-line {
            margin-bottom: 5px;
            line-height: 1.5;
        }
        
        .log-line.info { color: #6a9955; }
        .log-line.warn { color: #dcdcaa; }
        .log-line.error { color: #f44747; }
        
        .results-container {
            display: none;
        }
        
        .tabs {
            display: flex;
            border-bottom: 2px solid #e0e0e0;
            margin-bottom: 20px;
        }
        
        .tab {
            padding: 12px 25px;
            cursor: pointer;
            border-bottom: 2px solid transparent;
            margin-bottom: -2px;
            transition: all 0.3s;
        }
        
        .tab:hover {
            color: #667eea;
        }
        
        .tab.active {
            color: #667eea;
            border-bottom-color: #667eea;
        }
        
        .tab-content {
            display: none;
        }
        
        .tab-content.active {
            display: block;
        }
        
        .result-grid {
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(300px, 1fr));
            gap: 20px;
        }
        
        .result-item {
            background: #f8f9fa;
            padding: 15px;
            border-radius: 8px;
            border-left: 4px solid #667eea;
        }
        
        .result-item h4 {
            color: #333;
            margin-bottom: 8px;
        }
        
        .result-item p {
            color: #666;
            font-size: 14px;
            line-height: 1.6;
        }
        
        .figure-grid {
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(400px, 1fr));
            gap: 20px;
        }
        
        .figure-item {
            background: white;
            border: 1px solid #e0e0e0;
            border-radius: 8px;
            padding: 15px;
            text-align: center;
        }
        
        .figure-item img {
            max-width: 100%;
            height: auto;
            border-radius: 4px;
        }
        
        .figure-item p {
            margin-top: 10px;
            color: #666;
            font-weight: 500;
        }
        
        .paper-preview {
            background: #fafafa;
            border: 1px solid #e0e0e0;
            border-radius: 8px;
            padding: 25px;
            max-height: 600px;
            overflow-y: auto;
            line-height: 1.8;
        }
        
        .paper-preview h1 {
            font-size: 1.8em;
            color: #333;
            margin-bottom: 15px;
        }
        
        .paper-preview h2 {
            font-size: 1.4em;
            color: #667eea;
            margin-top: 25px;
            margin-bottom: 12px;
        }
        
        .paper-preview p {
            color: #444;
            margin-bottom: 12px;
        }
        
        .badge {
            display: inline-block;
            padding: 4px 10px;
            background: #667eea;
            color: white;
            border-radius: 20px;
            font-size: 12px;
            margin-right: 5px;
        }
        
        .stats-row {
            display: flex;
            justify-content: space-around;
            margin-bottom: 20px;
        }
        
        .stat-item {
            text-align: center;
        }
        
        .stat-value {
            font-size: 2em;
            font-weight: bold;
            color: #667eea;
        }
        
        .stat-label {
            color: #666;
            font-size: 14px;
        }
        
        .collapsible {
            cursor: pointer;
            padding: 10px;
            background: #f0f0f0;
            border-radius: 6px;
            margin-bottom: 10px;
            display: flex;
            justify-content: space-between;
            align-items: center;
        }
        
        .collapsible:hover {
            background: #e0e0e0;
        }
        
        .collapsible-content {
            display: none;
            padding: 15px;
            background: #fafafa;
            border-radius: 6px;
            margin-bottom: 10px;
        }
        
        .collapsible-content.active {
            display: block;
        }
        
        .download-btn {
            display: inline-block;
            padding: 8px 16px;
            background: #28a745;
            color: white;
            text-decoration: none;
            border-radius: 6px;
            font-size: 14px;
            margin-top: 10px;
        }
        
        .download-btn:hover {
            background: #218838;
        }
        
        @media (max-width: 768px) {
            .header h1 {
                font-size: 1.8em;
            }
            
            .form-row {
                grid-template-columns: 1fr;
            }
            
            .figure-grid {
                grid-template-columns: 1fr;
            }
        }
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <h1>🔬 Research Agent</h1>
            <p>自动化科研分析与论文撰写系统</p>
        </div>
        
        <!-- 配置表单 -->
        <div class="card" id="config-card">
            <h2>⚙️ 研究配置</h2>
            <form id="research-form">
                <div class="form-group">
                    <label for="topic">研究主题 *</label>
                    <input type="text" id="topic" name="topic" required 
                           placeholder="例如：图像分类、时间序列预测、自然语言处理...">
                </div>
                
                <div class="form-row">
                    <div class="form-group">
                        <label for="llm_backend">LLM 后端</label>
                        <select id="llm_backend" name="llm_backend">
                            <option value="ollama">Ollama (本地)</option>
                            <option value="openai">OpenAI API</option>
                        </select>
                    </div>
                    
                    <div class="form-group">
                        <label for="ollama_model">Ollama 模型</label>
                        <input type="text" id="ollama_model" name="ollama_model" 
                               value="qwen2.5:14b" placeholder="qwen2.5:14b">
                    </div>
                    
                    <div class="form-group">
                        <label for="language">论文语言</label>
                        <select id="language" name="language">
                            <option value="zh">中文</option>
                            <option value="en">English</option>
                        </select>
                    </div>
                </div>
                
                <div class="form-row">
                    <div class="form-group">
                        <label for="openai_key">OpenAI API Key</label>
                        <input type="password" id="openai_key" name="openai_key" 
                               placeholder="sk-...">
                    </div>
                    
                    <div class="form-group">
                        <label for="openai_model">OpenAI 模型</label>
                        <input type="text" id="openai_model" name="openai_model" 
                               value="gpt-4">
                    </div>
                </div>
                
                <div class="form-row">
                    <div class="form-group">
                        <label for="kaggle_username">Kaggle 用户名</label>
                        <input type="text" id="kaggle_username" name="kaggle_username" 
                               placeholder="可选，用于下载数据">
                    </div>
                    
                    <div class="form-group">
                        <label for="kaggle_key">Kaggle API Key</label>
                        <input type="password" id="kaggle_key" name="kaggle_key" 
                               placeholder="可选">
                    </div>
                </div>
                
                <div class="form-row">
                    <div class="form-group">
                        <label for="max_datasets">最大数据集数</label>
                        <input type="number" id="max_datasets" name="max_datasets" 
                               value="5" min="1" max="20">
                    </div>
                    
                    <div class="form-group">
                        <label for="max_papers">最大论文数</label>
                        <input type="number" id="max_papers" name="max_papers" 
                               value="15" min="5" max="50">
                    </div>
                    
                    <div class="form-group">
                        <label for="max_notebooks">最大 Notebook 数</label>
                        <input type="number" id="max_notebooks" name="max_notebooks" 
                               value="3" min="1" max="10">
                    </div>
                </div>
                
                <button type="submit" class="btn" id="start-btn">
                    🚀 开始研究
                </button>
            </form>
            
            <!-- 进度显示 -->
            <div class="progress-container" id="progress-container">
                <div class="progress-bar">
                    <div class="progress-fill" id="progress-fill"></div>
                </div>
                <div class="progress-text" id="progress-text">准备中...</div>
                <div class="log-container" id="log-container"></div>
            </div>
        </div>
        
        <!-- 结果展示 -->
        <div class="card results-container" id="results-card">
            <h2>📊 研究结果</h2>
            
            <div class="stats-row">
                <div class="stat-item">
                    <div class="stat-value" id="stat-datasets">0</div>
                    <div class="stat-label">数据集</div>
                </div>
                <div class="stat-item">
                    <div class="stat-value" id="stat-notebooks">0</div>
                    <div class="stat-label">Notebook</div>
                </div>
                <div class="stat-item">
                    <div class="stat-value" id="stat-papers">0</div>
                    <div class="stat-label">论文</div>
                </div>
                <div class="stat-item">
                    <div class="stat-value" id="stat-methods">0</div>
                    <div class="stat-label">分析方法</div>
                </div>
            </div>
            
            <div class="tabs">
                <div class="tab active" data-tab="datasets">📁 数据集</div>
                <div class="tab" data-tab="papers">📚 论文</div>
                <div class="tab" data-tab="results">📈 分析结果</div>
                <div class="tab" data-tab="figures">📊 图表</div>
                <div class="tab" data-tab="paper">📄 完整论文</div>
            </div>
            
            <div class="tab-content active" id="tab-datasets">
                <div class="result-grid" id="datasets-grid"></div>
            </div>
            
            <div class="tab-content" id="tab-papers">
                <div class="result-grid" id="papers-grid"></div>
            </div>
            
            <div class="tab-content" id="tab-results">
                <div class="result-grid" id="results-grid"></div>
            </div>
            
            <div class="tab-content" id="tab-figures">
                <div class="figure-grid" id="figures-grid"></div>
            </div>
            
            <div class="tab-content" id="tab-paper">
                <div class="paper-preview" id="paper-preview"></div>
                <a href="#" class="download-btn" id="download-paper" download>
                    📥 下载论文 (Markdown)
                </a>
            </div>
        </div>
        
        <!-- 历史任务 -->
        <div class="card" id="history-card" style="display:none;">
            <h2>📜 历史任务</h2>
            <div id="history-list"></div>
        </div>
    </div>
    
    <script>
        let currentJobId = null;
        
        // 表单提交
        document.getElementById('research-form').addEventListener('submit', async function(e) {
            e.preventDefault();
            
            const formData = new FormData(this);
            const data = Object.fromEntries(formData.entries());
            
            // 禁用按钮
            document.getElementById('start-btn').disabled = true;
            document.getElementById('progress-container').style.display = 'block';
            document.getElementById('results-card').style.display = 'none';
            
            try {
                const response = await fetch('/api/start', {
                    method: 'POST',
                    headers: {'Content-Type': 'application/json'},
                    body: JSON.stringify(data)
                });
                
                const result = await response.json();
                
                if (result.success) {
                    currentJobId = result.job_id;
                    pollProgress(result.job_id);
                } else {
                    alert('错误：' + result.error);
                    document.getElementById('start-btn').disabled = false;
                }
            } catch (err) {
                alert('请求失败：' + err.message);
                document.getElementById('start-btn').disabled = false;
            }
        });
        
        // 轮询进度
        async function pollProgress(jobId) {
            try {
                const response = await fetch(`/api/progress/${jobId}`);
                const data = await response.json();
                
                updateProgress(data);
                
                if (data.status === 'completed') {
                    showResults(data);
                    document.getElementById('start-btn').disabled = false;
                } else if (data.status === 'failed') {
                    addLog('错误：' + data.error, 'error');
                    document.getElementById('start-btn').disabled = false;
                } else {
                    setTimeout(() => pollProgress(jobId), 2000);
                }
            } catch (err) {
                console.error('轮询失败:', err);
                setTimeout(() => pollProgress(jobId), 2000);
            }
        }
        
        // 更新进度
        function updateProgress(data) {
            const progress = data.progress || 0;
            document.getElementById('progress-fill').style.width = progress + '%';
            document.getElementById('progress-text').textContent = data.message || '处理中...';
            
            if (data.logs) {
                data.logs.forEach(log => addLog(log.text, log.level));
            }
        }
        
        // 添加日志
        function addLog(text, level = 'info') {
            const container = document.getElementById('log-container');
            const line = document.createElement('div');
            line.className = `log-line ${level}`;
            line.textContent = `[${new Date().toLocaleTimeString()}] ${text}`;
            container.appendChild(line);
            container.scrollTop = container.scrollHeight;
        }
        
        // 显示结果
        function showResults(data) {
            document.getElementById('results-card').style.display = 'block';
            
            // 更新统计
            document.getElementById('stat-datasets').textContent = data.datasets?.length || 0;
            document.getElementById('stat-notebooks').textContent = data.notebooks?.length || 0;
            document.getElementById('stat-papers').textContent = data.papers?.length || 0;
            document.getElementById('stat-methods').textContent = data.results?.length || 0;
            
            // 数据集
            const datasetsGrid = document.getElementById('datasets-grid');
            datasetsGrid.innerHTML = (data.datasets || []).map(d => `
                <div class="result-item">
                    <h4>${escapeHtml(d.title || d.name)}</h4>
                    <p>${escapeHtml(d.description || '')}</p>
                    <div style="margin-top:10px;">
                        <span class="badge">${d.votes || 0} votes</span>
                    </div>
                    <a href="${d.url}" target="_blank" class="download-btn">查看详情</a>
                </div>
            `).join('');
            
            // 论文
            const papersGrid = document.getElementById('papers-grid');
            papersGrid.innerHTML = (data.papers || []).map(p => `
                <div class="result-item">
                    <h4>${escapeHtml(p.title)}</h4>
                    <p><strong>作者:</strong> ${(p.authors || []).slice(0,3).join(', ')}${(p.authors || []).length > 3 ? ' et al.' : ''}</p>
                    <p><strong>年份:</strong> ${p.year || 'N/A'}</p>
                    <p style="font-size:13px;color:#888;">${escapeHtml((p.abstract || '').substring(0, 200))}...</p>
                    <a href="${p.url}" target="_blank" class="download-btn">查看论文</a>
                </div>
            `).join('');
            
            // 分析结果
            const resultsGrid = document.getElementById('results-grid');
            resultsGrid.innerHTML = (data.results || []).map(r => `
                <div class="result-item">
                    <h4>${escapeHtml(r.method_name)}</h4>
                    <p><strong>准确率:</strong> ${(r.accuracy * 100).toFixed(2)}%</p>
                    <p><strong>F1 分数:</strong> ${(r.f1_score * 100).toFixed(2)}%</p>
                    <p><strong>AUC-ROC:</strong> ${(r.auc_roc * 100).toFixed(2)}%</p>
                    <p><strong>训练时间:</strong> ${r.training_time}s</p>
                </div>
            `).join('');
            
            // 图表
            const figuresGrid = document.getElementById('figures-grid');
            if (data.job_id) {
                const figures = ['method_comparison.png', 'radar_chart.png', 'heatmap.png'];
                figuresGrid.innerHTML = figures.map(f => `
                    <div class="figure-item">
                        <img src="/api/figures/${data.job_id}/${f}" alt="${f}" onerror="this.style.display='none';this.nextElementSibling.textContent='图表加载中...'">
                        <p>${f.replace('.png', '')}</p>
                    </div>
                `).join('');
            }
            
            // 论文
            if (data.paper_content) {
                document.getElementById('paper-preview').innerHTML = marked.parse(data.paper_content);
                document.getElementById('download-paper').href = `/api/paper/${data.job_id}`;
            }
            
            // 切换到结果卡片
            document.getElementById('results-card').scrollIntoView({behavior: 'smooth'});
        }
        
        // Tab 切换
        document.querySelectorAll('.tab').forEach(tab => {
            tab.addEventListener('click', function() {
                const tabId = this.dataset.tab;
                
                document.querySelectorAll('.tab').forEach(t => t.classList.remove('active'));
                document.querySelectorAll('.tab-content').forEach(c => c.classList.remove('active'));
                
                this.classList.add('active');
                document.getElementById('tab-' + tabId).classList.add('active');
            });
        });
        
        // 工具函数
        function escapeHtml(text) {
            const div = document.createElement('div');
            div.textContent = text;
            return div.innerHTML;
        }
        
        // marked.js 简单实现
        const marked = {
            parse: function(md) {
                return md
                    .replace(/^# (.*$)/gim, '<h1>$1</h1>')
                    .replace(/^## (.*$)/gim, '<h2>$1</h2>')
                    .replace(/^### (.*$)/gim, '<h3>$1</h3>')
                    .replace(/\\*\\*(.*)\\*\\*/gim, '<strong>$1</strong>')
                    .replace(/\\*(.*)\\*/gim, '<em>$1</em>')
                    .replace(/\\n/gim, '<br>');
            }
        };
    </script>
</body>
</html>
"""

# =============================================================================
# Web Research Agent
# =============================================================================

class WebResearchAgent(ResearchAgent):
    """支持 Web 进度回调的研究智能体"""
    
    def __init__(self, config: Config, job_id: str, callback=None):
        super().__init__(config)
        self.job_id = job_id
        self.callback = callback
        self.logs = []
    
    def log(self, message: str, level: str = 'info'):
        """记录日志"""
        self.logs.append({
            'text': message,
            'level': level,
            'timestamp': datetime.now().isoformat()
        })
        if self.callback:
            self.callback(self.job_id, self.logs)
    
    def _print_header(self):
        """重写标题输出"""
        self.log(f"研究主题：{self.config.topic}", 'info')
        self.log(f"LLM: {self.config.llm_backend} ({self.config.ollama_model})", 'info')
    
    def _search_datasets(self):
        self.log(f"正在搜索数据集...", 'info')
        super()._search_datasets()
        self.log(f"找到 {len(self.datasets)} 个数据集", 'info')
    
    def _search_notebooks(self):
        self.log(f"正在搜索 Notebook...", 'info')
        super()._search_notebooks()
        self.log(f"找到 {len(self.notebooks)} 个 Notebook", 'info')
    
    def _search_papers(self):
        self.log(f"正在检索文献...", 'info')
        super()._search_papers()
        self.log(f"找到 {len(self.papers)} 篇论文", 'info')
    
    def _generate_analysis(self):
        self.log(f"正在生成分析代码...", 'info')
        super()._generate_analysis()
        self.log(f"分析代码已生成", 'info')
    
    def _generate_visualizations(self):
        self.log(f"正在生成可视化图表...", 'info')
        super()._generate_visualizations()
        self.log(f"图表已生成", 'info')
    
    def _write_paper(self):
        self.log(f"正在撰写论文...", 'info')
        super()._write_paper()
        self.log(f"论文已完成", 'info')
    
    def _print_summary(self):
        self.log(f"研究完成！输出目录：{self.output_dir}", 'info')


# =============================================================================
# API 路由
# =============================================================================

def progress_callback(job_id: str, logs: List[Dict]):
    """进度回调"""
    if job_id in running_jobs:
        running_jobs[job_id]['logs'] = logs[-50:]  # 保留最近 50 条日志

@app.route('/')
def index():
    """主页"""
    return render_template_string(HTML_TEMPLATE)

@app.route('/api/start', methods=['POST'])
def start_research():
    """开始研究任务"""
    data = request.json
    
    job_id = datetime.now().strftime('%Y%m%d_%H%M%S')
    
    # 创建配置
    config = Config(
        topic=data.get('topic', ''),
        output_dir=f"./web_outputs/{job_id}",
        llm_backend=data.get('llm_backend', 'ollama'),
        ollama_model=data.get('ollama_model', 'qwen2.5:14b'),
        openai_api_key=data.get('openai_key', ''),
        openai_model=data.get('openai_model', 'gpt-4'),
        kaggle_username=data.get('kaggle_username', ''),
        kaggle_key=data.get('kaggle_key', ''),
        max_datasets=int(data.get('max_datasets', 5)),
        max_notebooks=int(data.get('max_notebooks', 3)),
        max_papers=int(data.get('max_papers', 15)),
        language=data.get('language', 'zh')
    )
    
    # 创建任务
    running_jobs[job_id] = {
        'status': 'running',
        'progress': 0,
        'message': '启动中...',
        'logs': [],
        'config': asdict(config),
        'start_time': datetime.now().isoformat()
    }
    
    # 在后台线程中运行
    def run_job():
        try:
            agent = WebResearchAgent(config, job_id, progress_callback)
            agent.run()
            
            # 读取结果
            datasets_path = agent.output_dir / 'datasets.json'
            papers_path = agent.output_dir / 'papers.json'
            results_path = agent.output_dir / 'results.json'
            paper_path = agent.output_dir / 'paper.md'
            
            running_jobs[job_id]['results'] = {
                'datasets': json.loads(datasets_path.read_text()) if datasets_path.exists() else [],
                'papers': json.loads(papers_path.read_text()) if papers_path.exists() else [],
                'results': json.loads(results_path.read_text()) if results_path.exists() else [],
                'paper_content': paper_path.read_text() if paper_path.exists() else ''
            }
            
            running_jobs[job_id]['status'] = 'completed'
            running_jobs[job_id]['progress'] = 100
            running_jobs[job_id]['message'] = '研究完成！'
            
            # 移动到已完成
            completed_jobs[job_id] = running_jobs.pop(job_id)
            
        except Exception as e:
            running_jobs[job_id]['status'] = 'failed'
            running_jobs[job_id]['error'] = str(e)
            running_jobs[job_id]['logs'].append({
                'text': f'错误：{e}',
                'level': 'error',
                'timestamp': datetime.now().isoformat()
            })
    
    thread = threading.Thread(target=run_job)
    thread.daemon = True
    thread.start()
    
    return jsonify({
        'success': True,
        'job_id': job_id
    })

@app.route('/api/progress/<job_id>')
def get_progress(job_id: str):
    """获取进度"""
    if job_id in running_jobs:
        job = running_jobs[job_id]
        return jsonify({
            'status': job['status'],
            'progress': job['progress'],
            'message': job['message'],
            'logs': job.get('logs', [])
        })
    elif job_id in completed_jobs:
        job = completed_jobs[job_id]
        return jsonify({
            'status': 'completed',
            'progress': 100,
            'message': '研究完成！',
            'logs': job.get('logs', []),
            'datasets': job.get('results', {}).get('datasets', []),
            'papers': job.get('results', {}).get('papers', []),
            'results': job.get('results', {}).get('results', []),
            'paper_content': job.get('results', {}).get('paper_content', ''),
            'job_id': job_id
        })
    else:
        return jsonify({'status': 'not_found'}), 404

@app.route('/api/figures/<job_id>/<filename>')
def get_figure(job_id: str, filename: str):
    """获取图表"""
    figures_dir = Path(f'./web_outputs/{job_id}/figures')
    if figures_dir.exists():
        return send_from_directory(figures_dir, filename)
    return '', 404

@app.route('/api/paper/<job_id>')
def get_paper(job_id: str):
    """获取论文"""
    paper_path = Path(f'./web_outputs/{job_id}/paper.md')
    if paper_path.exists():
        return send_from_directory(paper_path.parent, paper_path.name, as_attachment=True)
    return '', 404

@app.route('/api/jobs')
def list_jobs():
    """列出所有任务"""
    jobs = []
    for job_id, job in completed_jobs.items():
        jobs.append({
            'job_id': job_id,
            'topic': job['config'].get('topic', ''),
            'status': job['status'],
            'start_time': job.get('start_time', ''),
            'datasets': len(job.get('results', {}).get('datasets', [])),
            'papers': len(job.get('results', {}).get('papers', []))
        })
    return jsonify(jobs)

# =============================================================================
# 主函数
# =============================================================================

def main():
    """启动 Web 服务"""
    import socket
    
    # 检查依赖
    try:
        import flask
    except ImportError:
        print("错误：需要安装 Flask")
        print("运行：pip install flask")
        sys.exit(1)
    
    # 查找可用端口
    port = 5000
    while True:
        try:
            sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            sock.bind(('127.0.0.1', port))
            sock.close()
            break
        except OSError:
            port += 1
    
    print("\n" + "=" * 60)
    print("  Research Agent Web Interface")
    print("=" * 60)
    print(f"\n  🌐 访问地址：http://localhost:{port}")
    print(f"  📁 输出目录：./web_outputs/")
    print("\n  按 Ctrl+C 停止服务")
    print("=" * 60 + "\n")
    
    # 创建输出目录
    Path('./web_outputs').mkdir(exist_ok=True)
    
    # 启动服务
    app.run(host='0.0.0.0', port=port, debug=False, threaded=True)


if __name__ == '__main__':
    main()
