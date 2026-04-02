# ai-fake-project-detector · 方案设计

---

## 方案目标
交付一个 **GitHub-first、可解释、可持久化** 的 V1：
- 分析 GitHub 仓库
- 与同类项目做 peer comparison
- 输出证据驱动的风险评分
- 支持已分析仓库排名、搜索/筛选、历史追踪
- 支持登录态轻量反馈，但反馈不直接主导核心评分或排名

---

## 已落地技术决策
- **Flask 是 canonical V1 surface**：承担主 Web 页面与 JSON 接口
- `app_runtime.py` 提供共享分析编排；`streamlit_app.py` 与 `simple_app.py` 仅为 demo / dev companion
- **Persistence foundation 已落地**：本地 SQLite 持久化快照、历史、排名查询与反馈去重
- 评分保持 explainable，不能走黑盒结论路线
- GitHub 是 V1 唯一数据源；X / Twitter 延期

---

## V1 设计原则
- **Explainability first**：每个显著分数都要能追溯到证据
- **Peer-relative first**：同类项目比较是可信度核心，不是附属功能
- **Analyzed-repo scope only**：排名只基于已分析仓库
- **Feedback is supplemental**：反馈只做补充层，不做直接分数或排名权威
- **Rule-first retrieval**：V1 优先稳定规则与回退路径，再考虑 embedding/hybrid 增强
- **Append-only history**：重复分析生成新 snapshot version，历史可追溯
- **TDD execution posture**：实现阶段按 RED → GREEN → REFACTOR 推进

---

## V1 能力分层

### 1) Analysis pipeline
- `repo-ingestion`：接收 GitHub URL，拉取仓库基础信息
- `structure-analyzer`：提取结构化特征与证据素材
- `peer-retrieval`：基于规则优先的可比项目召回生成 baseline，保留置信度/稀疏性披露
- `scoring-engine`：输出风险分、风险等级、分维度风险、证据卡片、guardrail notes、peer baseline 摘要
- `app_runtime.analyze_repository(...)`：串联采集 → 分析 → peer retrieval → scoring → snapshot persistence

### 2) Persistence + query layer
- `PersistenceStore.record_analysis(...)`：写入 append-only `analysis_snapshots`
- `PersistenceStore.get_repo_history(...)`：读取同一仓库的倒序历史快照
- `PersistenceStore.query_rankings(...)`：基于每个仓库最新 snapshot 生成 analyzed-repo-only 排名结果
- `PersistenceStore.record_feedback(...)` / `list_feedback(...)`：保存轻量反馈、时间窗口去重、辅助汇总

### 3) Product surface
- Flask 页面：分析入口、结果页、详情页、排名页
- Flask JSON endpoints：分析、重复分析、详情、排名、反馈
- 登录态 session：本地轻量身份，仅用于反馈权限与显示

---

## 核心数据与输出

### 核心输出
- `fake_risk_score`：0–100，越高风险越高
- `risk_level` / `risk_band`：与分数区间一致
- `dimension_scores`：各维度风险分，语义与总分一致
- `evidence_cards`：用户可读证据
- `guardrail_notes`：保护性说明
- `peer_baseline_summary`：同类比较摘要
- `peer_baseline_meta` / `retrieval_metadata`：比较范围、样本量、置信度、披露信息
- `snapshot_id` / `snapshot_version` / `snapshot_at`：持久化历史标识

### 关键边界
- 排名基于 **latest analyzed snapshots**
- 搜索 / 筛选 / 排序作用于已分析仓库数据集
- 详情页展示最新报告与完整历史，不重算旧快照
- 反馈单独存储与展示，不直接覆盖评分结果

---

## 关键模块

| 模块 | 职责 | V1 状态 / 约束 |
|------|------|----------------|
| repo-ingestion | GitHub 仓库采集 | 已用于主流程；不接入 X / Twitter |
| structure-analyzer | 提取结构与证据特征 | 已用于主流程；只输出可解释特征 |
| peer-retrieval | 同类项目召回 | 已采用 rule-first 策略并披露稀疏/低置信度 |
| scoring-engine | 生成风险报告 | 已输出 explainable risk report，禁止黑盒总分 |
| persistence/query | snapshots/history/ranking/feedback dedupe | 已落地 SQLite 持久化与查询 |
| Flask app surface | 页面与 JSON 接口 | 已作为 V1 主入口 |
| demo surfaces | 演示与开发辅助 | 保留但非主产品面 |

---

## 运行流程
1. 用户提交 GitHub URL
2. `repo-ingestion` 获取仓库元数据与内容
3. `structure-analyzer` 产出结构化特征与证据
4. `peer-retrieval` 用规则优先策略召回可比较仓库并生成 baseline
5. `scoring-engine` 输出 explainable risk report
6. `PersistenceStore` 保存 snapshot、repo identity 与 ranking inputs
7. Flask 结果页暴露详情页 / 排名页导航
8. 详情页 / API 读取最新快照与历史，保留 peer guardrail/disclaimer
9. 排名页 / API 只基于最新持久化快照提供搜索、筛选、排序
10. 登录用户提交轻量反馈；系统做去重/限流并单独展示

---

## 排名设计
- 排名数据源：每个仓库的最新持久化 snapshot
- 支持过滤：`search`、`language`、`risk_band`
- 支持排序：`latest_fake_risk_score`、`snapshot_at`、`stargazers_count`
- 支持方向与分页：`direction`、`limit`、`offset`
- 排名披露固定说明：仅覆盖已分析仓库，反馈只做补充展示，不参与权威排序

---

## 历史设计
- 同仓库每次分析都会生成新版本 snapshot
- 详情页默认展示最新快照，并附带按时间倒序的历史列表
- 历史记录保留当时的评分输出、peer 元数据、证据与说明
- 重复分析通过 `/api/reanalyze` 复用相同主流程，而不是旁路逻辑

---

## 反馈设计
- 仅登录用户可提交
- 反馈形态保持 lightweight：`support` / `disagree` / `needs_review`
- 展示为“Supplemental Feedback”摘要与近期活动
- 通过 session identity、60 分钟 dedupe window、每仓库冷却时间实现基础 anti-abuse
- 反馈不直接参与核心风险分计算，也不改写排名顺序

---

## 回归与集成覆盖
- 模块测试覆盖采集、结构分析、peer retrieval、评分与持久化契约
- 集成测试覆盖 `/api/analyze`、`/api/reanalyze`、详情页/API、排名页/API、反馈提交
- 主导航流覆盖 landing → analyze → detail/history → rankings → feedback
- 回归测试明确锁定 GitHub-only、analyzed-repo-only、supplemental-only 三类边界

---

## Deferred scope
- X / Twitter ingestion
- anonymous voting / anonymous feedback
- public API
- appeals / 作者申诉
- comments / 评论区
- advanced fraud detection / 复杂反作弊

---

## 主要风险与控制
- **术语风险**：统一使用验证 / 风险 / 可信度语言
- **比较失真风险**：peer retrieval 保持规则优先，并显式披露 sparse / low-confidence baseline
- **误伤风险**：评分 guardrails 要保护 early-but-real 与证据充分的研究型仓库
- **反馈越权风险**：反馈明确为 supplemental，不可直接改写分数或排序
- **范围蔓延风险**：X / Twitter 与公开 API 继续延期
- **多入口混乱风险**：Flask 保持主入口，其他应用只保留 demo 属性
