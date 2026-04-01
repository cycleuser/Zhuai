// Zhuai Web JavaScript

let currentPapers = [];
let selectedPapers = new Set();

// DOM Ready
document.addEventListener('DOMContentLoaded', function() {
    initEventListeners();
});

function initEventListeners() {
    // Search form
    document.getElementById('searchForm').addEventListener('submit', handleSearch);
    
    // Advanced filters toggle
    document.getElementById('toggleAdvanced').addEventListener('click', toggleAdvanced);
    
    // Results actions
    document.getElementById('selectAll').addEventListener('click', toggleSelectAll);
    document.getElementById('downloadSelected').addEventListener('click', downloadSelected);
    document.getElementById('exportCSV').addEventListener('click', () => exportResults('csv'));
    document.getElementById('exportJSON').addEventListener('click', () => exportResults('json'));
}

function toggleAdvanced() {
    const filters = document.getElementById('advancedFilters');
    const icon = this.querySelector('.fa-chevron-down');
    
    if (filters.style.display === 'none') {
        filters.style.display = 'block';
        icon.classList.replace('fa-chevron-down', 'fa-chevron-up');
    } else {
        filters.style.display = 'none';
        icon.classList.replace('fa-chevron-up', 'fa-chevron-down');
    }
}

async function handleSearch(e) {
    e.preventDefault();
    
    const query = document.getElementById('query').value.trim();
    if (!query) {
        alert('请输入搜索关键词');
        return;
    }
    
    // Get form data
    const formData = new FormData(e.target);
    const data = {
        query: query,
        sources: formData.getAll('sources'),
        max_results: parseInt(formData.get('max_results') || '50'),
        author: formData.get('author'),
        title: formData.get('title'),
        journal: formData.get('journal'),
        year_from: formData.get('year_from'),
        year_to: formData.get('year_to'),
        quartile: formData.get('quartile'),
        min_citations: formData.get('min_citations'),
        has_pdf: formData.has('has_pdf')
    };
    
    // Show loading
    showLoading(true);
    
    try {
        const response = await fetch('/api/search', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify(data)
        });
        
        const result = await response.json();
        
        if (result.error) {
            alert('搜索失败: ' + result.error);
            return;
        }
        
        currentPapers = result.papers;
        selectedPapers.clear();
        displayResults(result.papers);
        
    } catch (error) {
        alert('搜索出错: ' + error.message);
    } finally {
        showLoading(false);
    }
}

function displayResults(papers) {
    const section = document.getElementById('resultsSection');
    const list = document.getElementById('resultsList');
    const countEl = document.getElementById('resultCount');
    
    countEl.textContent = `(${papers.length} 条结果)`;
    
    if (papers.length === 0) {
        list.innerHTML = '<div class="paper-card"><p>未找到相关论文</p></div>';
        section.style.display = 'block';
        return;
    }
    
    let html = '';
    papers.forEach((paper, index) => {
        const authors = paper.authors.slice(0, 3).join(', ');
        const authorsMore = paper.authors.length > 3 ? ' et al.' : '';
        const year = paper.year || 'N/A';
        const journal = paper.journal || '';
        const citations = paper.citations || 0;
        
        const pdfBadge = paper.can_download 
            ? '<span class="pdf-badge"><i class="fas fa-file-pdf"></i> PDF</span>'
            : '<span class="pdf-badge unavailable"><i class="fas fa-file"></i> 无 PDF</span>';
        
        html += `
            <div class="paper-card" data-index="${index}">
                <div class="paper-header">
                    <input type="checkbox" class="paper-select" data-index="${index}" 
                           onchange="togglePaperSelection(${index})">
                    <div class="paper-info">
                        <div class="paper-title" onclick="togglePaperDetail(${index})">
                            ${index + 1}. ${escapeHtml(paper.title)} ${pdfBadge}
                        </div>
                        <div class="paper-meta">
                            <span class="paper-authors">${escapeHtml(authors)}${authorsMore}</span>
                            ${year ? ` | <span>${year}</span>` : ''}
                            ${journal ? ` | <span class="paper-journal">${escapeHtml(journal)}</span>` : ''}
                            ${citations ? ` | <span class="paper-citations"><i class="fas fa-quote-right"></i> ${citations}</span>` : ''}
                            ${paper.source ? ` | <span class="paper-source">${paper.source}</span>` : ''}
                        </div>
                        <div class="paper-detail" id="detail-${index}" style="display: none;">
                            ${paper.abstract ? `<div class="paper-abstract">${escapeHtml(paper.abstract)}</div>` : ''}
                            <div class="paper-actions">
                                ${paper.can_download ? `<button class="btn btn-sm btn-primary" onclick="downloadPaper(${index})"><i class="fas fa-download"></i> 下载 PDF</button>` : ''}
                                ${paper.source_url ? `<a href="${paper.source_url}" target="_blank" class="btn btn-sm"><i class="fas fa-external-link-alt"></i> 查看原文</a>` : ''}
                                ${paper.doi ? `<a href="https://doi.org/${paper.doi}" target="_blank" class="btn btn-sm"><i class="fas fa-link"></i> DOI</a>` : ''}
                                <button class="btn btn-sm" onclick="showCitation(${index})"><i class="fas fa-quote-left"></i> 引用</button>
                            </div>
                        </div>
                    </div>
                </div>
            </div>
        `;
    });
    
    list.innerHTML = html;
    section.style.display = 'block';
    section.scrollIntoView({ behavior: 'smooth' });
}

function togglePaperDetail(index) {
    const detail = document.getElementById(`detail-${index}`);
    if (detail) {
        detail.style.display = detail.style.display === 'none' ? 'block' : 'none';
    }
}

function togglePaperSelection(index) {
    if (selectedPapers.has(index)) {
        selectedPapers.delete(index);
    } else {
        selectedPapers.add(index);
    }
    updateSelectionUI();
}

function toggleSelectAll() {
    const checkboxes = document.querySelectorAll('.paper-select');
    const allSelected = selectedPapers.size === currentPapers.length;
    
    if (allSelected) {
        selectedPapers.clear();
        checkboxes.forEach(cb => cb.checked = false);
    } else {
        currentPapers.forEach((_, index) => selectedPapers.add(index));
        checkboxes.forEach(cb => cb.checked = true);
    }
    updateSelectionUI();
}

function updateSelectionUI() {
    const btn = document.getElementById('downloadSelected');
    btn.disabled = selectedPapers.size === 0;
    btn.innerHTML = selectedPapers.size > 0 
        ? `<i class="fas fa-download"></i> 下载选中 (${selectedPapers.size})`
        : '<i class="fas fa-download"></i> 下载选中';
}

async function downloadPaper(index) {
    const paper = currentPapers[index];
    if (!paper.pdf_url) {
        alert('该论文没有可用的 PDF');
        return;
    }
    
    try {
        const response = await fetch('/api/download', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ papers: [paper] })
        });
        
        const result = await response.json();
        
        if (result.success) {
            alert(`下载成功: ${result.downloaded} 个文件`);
        } else {
            alert('下载失败: ' + result.error);
        }
    } catch (error) {
        alert('下载出错: ' + error.message);
    }
}

async function downloadSelected() {
    if (selectedPapers.size === 0) return;
    
    const papersToDownload = Array.from(selectedPapers).map(index => currentPapers[index]);
    
    try {
        const response = await fetch('/api/download', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ papers: papersToDownload })
        });
        
        const result = await response.json();
        
        if (result.success) {
            alert(`下载完成: ${result.downloaded} 个成功, ${result.failed} 个失败`);
        } else {
            alert('下载失败: ' + result.error);
        }
    } catch (error) {
        alert('下载出错: ' + error.message);
    }
}

async function exportResults(format) {
    if (currentPapers.length === 0) {
        alert('没有可导出的结果');
        return;
    }
    
    try {
        const response = await fetch('/api/export', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ papers: currentPapers, format: format })
        });
        
        const blob = await response.blob();
        const url = window.URL.createObjectURL(blob);
        const a = document.createElement('a');
        a.href = url;
        a.download = `papers.${format}`;
        a.click();
        window.URL.revokeObjectURL(url);
    } catch (error) {
        alert('导出出错: ' + error.message);
    }
}

// Citation Modal
let currentCitationPaper = null;

async function showCitation(index) {
    currentCitationPaper = currentPapers[index];
    
    const modal = document.getElementById('citationModal');
    modal.style.display = 'flex';
    
    // Get initial citation
    await fetchCitation('apa');
    
    // Style buttons
    document.querySelectorAll('.style-btn').forEach(btn => {
        btn.addEventListener('click', async () => {
            document.querySelectorAll('.style-btn').forEach(b => b.classList.remove('active'));
            btn.classList.add('active');
            await fetchCitation(btn.dataset.style);
        });
    });
}

async function fetchCitation(style) {
    if (!currentCitationPaper) return;
    
    try {
        const response = await fetch('/api/citation', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ paper: currentCitationPaper, style: style })
        });
        
        const result = await response.json();
        
        if (result.success) {
            document.getElementById('citationText').textContent = result.citation;
        }
    } catch (error) {
        document.getElementById('citationText').textContent = '生成引用失败';
    }
}

function closeCitationModal() {
    document.getElementById('citationModal').style.display = 'none';
}

function copyCitation() {
    const text = document.getElementById('citationText').textContent;
    navigator.clipboard.writeText(text).then(() => {
        alert('已复制到剪贴板');
    });
}

// Utilities
function showLoading(show) {
    document.getElementById('loadingOverlay').style.display = show ? 'flex' : 'none';
}

function escapeHtml(text) {
    if (!text) return '';
    const div = document.createElement('div');
    div.textContent = text;
    return div.innerHTML;
}

// Close modal on outside click
window.onclick = function(e) {
    const modal = document.getElementById('citationModal');
    if (e.target === modal) {
        closeCitationModal();
    }
}