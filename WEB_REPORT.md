# Zhuai Web 界面开发报告

**日期**: 2026-04-01  
**版本**: 2.1.0

---

## 新增功能

### Web 界面

提供完整的 Web UI，支持浏览器访问：

```bash
zhuai web --port 5000
```

访问 http://localhost:5000

---

## Web 功能列表

| 功能 | 说明 |
|------|------|
| 🔍 搜索 | 支持多数据源同时搜索 |
| 🎯 高级过滤 | 作者、期刊、年份、分区等 |
| 📥 批量下载 | 选择多篇论文一键下载 |
| 📝 引用生成 | APA/MLA/GB-T/BibTeX 多格式 |
| 📊 导出 | CSV/JSON 格式导出 |
| 📖 期刊查询 | 期刊信息数据库 |

---

## API 端点

| 端点 | 方法 | 说明 |
|------|------|------|
| `/` | GET | 搜索页面 |
| `/api/search` | POST | 搜索论文 |
| `/api/download` | POST | 下载论文 |
| `/api/citation` | POST | 生成引用 |
| `/api/journals/search` | GET | 搜索期刊 |
| `/api/export` | POST | 导出结果 |

---

## 文件结构

```
zhuai/web/
├── __init__.py
├── app.py                 # Flask 应用
├── templates/
│   └── index.html        # 主页面模板
└── static/
    ├── css/
    │   └── style.css     # 样式表
    └── js/
        └── main.js       # JavaScript
```

---

## 技术栈

- **Flask** - Web 框架
- **Jinja2** - 模板引擎
- **原生 JavaScript** - 前端交互
- **CSS3** - 响应式样式

---

## 使用方式

### 启动服务

```bash
# 默认端口 5000
zhuai web

# 指定端口
zhuai web --port 8080

# 指定主机和端口
zhuai web --host 127.0.0.1 --port 3000

# 调试模式
zhuai web --debug
```

### API 调用示例

```bash
# 搜索论文
curl -X POST http://localhost:5000/api/search \
  -H "Content-Type: application/json" \
  -d '{"query": "deep learning", "sources": ["arxiv", "pubmed"]}'

# 搜索期刊
curl "http://localhost:5000/api/journals/search?q=nature"

# 生成引用
curl -X POST http://localhost:5000/api/citation \
  -H "Content-Type: application/json" \
  -d '{"paper": {"title": "Test", "authors": ["Author"]}, "style": "apa"}'
```

---

## CLI 完整命令

| 命令 | 说明 |
|------|------|
| `zhuai search` | 命令行搜索 |
| `zhuai web` | 启动 Web 界面 |
| `zhuai journals` | 搜索期刊 |
| `zhuai journal-info` | 期刊详情 |
| `zhuai sources` | 列出数据源 |

---

## 下一步

1. 用户认证（可选）
2. 搜索历史记录
3. 收藏夹功能
4. Docker 部署支持

---

*报告生成时间: 2026-04-01*