# ai-fake-project-detector

GitHub-first 的 AI 开源项目验证与风险提示 V1。当前已交付的主产品面是 Flask Web 页面 + JSON API，用于完成 **analyze -> detail/history -> rankings -> feedback** 闭环。

## 项目简介

这个项目帮助用户判断一个热门 AI GitHub 仓库是否存在“传播大于实质”的风险。V1 聚焦：

- 分析 GitHub 仓库结构与基础元数据
- 基于 **已分析仓库范围内** 的 peer baseline 做对比
- 输出可解释风险评分、证据卡片与 guardrail notes
- 保存快照历史，支持重复分析后复查变化
- 提供登录后可提交的轻量补充反馈

## 当前 V1 已交付能力

- GitHub URL analysis
- explainable fake-risk scoring
- rule-first peer retrieval / baseline
- persisted snapshots + repo history
- analyzed-repo-only rankings
- rankings search / filter / sort
- authenticated lightweight supplemental feedback
- Flask HTML 页面与 JSON API 主入口

## 目录 / 核心模块概览

- `flask_app.py`：V1 canonical surface，提供页面与 JSON API
- `app_runtime.py`：共享分析编排与持久化接入
- `modules/repo_ingestion/`：GitHub 仓库采集
- `modules/structure_analyzer/`：结构与证据特征提取
- `modules/peer_retrieval/`：rule-first 同类项目召回
- `modules/scoring_engine/`：可解释风险评分
- `services/persistence.py`：SQLite snapshots / history / rankings / feedback
- `templates/`：Flask 页面模板
- `tests/`：模块、持久化、集成回归测试
- `docs/`：PRD、方案、交付文档与 backlog

## 环境 / 依赖说明

仓库当前可明确推断的运行基础：

- Python 3
- Flask
- requests
- pytest（用于测试）
- SQLite（Python 标准库 `sqlite3`）

仓库内未提供单独锁定的依赖清单文件，因此请在你自己的 Python 环境中确保以上依赖可用。

## 如何启动

### 1) 进入项目目录

```bash
cd projects/ai-fake-project-detector
```

### 2) 准备 Python 环境

如果你还没有可用环境，可使用一个最小本地虚拟环境：

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install flask requests pytest
```

### 3) 启动 Flask

```bash
python3 flask_app.py
```

默认会以 debug 模式监听：

- `http://127.0.0.1:5000`
- `http://0.0.0.0:5000`

### 4) 可选：指定持久化数据库路径

若未指定，默认使用 `data/analysis.sqlite3`。如需改到其他位置：

```bash
export AI_FAKE_PROJECT_DB_PATH=/absolute/path/to/analysis.sqlite3
python3 flask_app.py
```

## 如何运行测试

在项目目录下执行：

```bash
pytest
```

## 关键页面 / API 路由

### 页面

- `GET /`：分析提交页
- `POST /analyze`：提交 GitHub URL 并渲染结果页
- `GET /repos/detail?repo_url=...`：仓库详情 + 历史 + 反馈摘要
- `GET /rankings`：已分析仓库排名页

### API

- `POST /api/analyze`：分析仓库并持久化 snapshot
- `POST /api/reanalyze`：重复分析同一仓库，生成新 snapshot version
- `GET /api/repos/detail?repo_url=...`：获取最新详情与历史
- `GET /api/rankings`：获取 analyzed-repo-only rankings
- `POST /api/repos/feedback`：提交登录态轻量反馈

### 轻量登录 / 反馈相关

- `POST /auth/login`：建立本地 session 身份
- `POST /auth/logout`：退出反馈身份
- `POST /repos/feedback`：页面表单反馈入口

## 当前边界与延期能力说明

以下内容 **不是 V1 已交付能力**：

- X / Twitter ingestion
- anonymous voting / anonymous feedback
- public API
- appeals
- comments
- advanced fraud detection

另外请注意：

- 排名只覆盖 **已经分析并持久化** 的仓库，不是全 GitHub 榜单
- 反馈是 **authenticated + lightweight + supplemental**，不会直接成为评分或排名权威
- `streamlit_app.py` 与 `simple_app.py` 仅保留 demo / dev companion 属性，不是主产品面

## 交付文档

- `docs/PRD.md`：产品范围与验收口径
- `docs/SOLUTION.md`：实现方案与技术边界
- `docs/PLAN.md`：当前 shipped V1 范围清单
- `docs/TODO.md`：post-V1 backlog
- `docs/DELIVERY_SUMMARY.md`：本次交付摘要
