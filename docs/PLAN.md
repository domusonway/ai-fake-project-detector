# ai-fake-project-detector · 开发计划

---

## V1 交付结果
当前项目已交付一个以 **GitHub 仓库验证与风险提示** 为核心的 V1，形成如下闭环：
- explainable scoring
- peer comparison
- persisted analysis orchestration
- repo detail + score history
- analyzed-repo ranking
- search / filter / sort
- authenticated lightweight feedback
- integrated navigation across main surfaces
- regression / integration coverage for shipped flows

同时保持以下 guardrails：
- GitHub 是唯一 V1 数据源
- X / Twitter 明确延期
- 排名只覆盖已分析仓库
- 反馈补充展示，不直接成为评分或排名权威
- 实现过程遵循 TDD

---

## V1 范围清单

### In scope（已交付）
1. GitHub URL analysis
2. 结构化特征提取
3. 同类项目对比与 baseline
4. 可解释风险评分
5. 分析快照持久化与历史查询
6. 已分析仓库排名
7. 搜索 / 筛选 / 排序
8. 仓库详情页与详情 API
9. 登录态轻量反馈
10. 分析、详情、排名、反馈之间的集成导航
11. 回归 / 集成测试覆盖

### Out of scope / Deferred
1. X / Twitter ingestion
2. anonymous voting / anonymous feedback
3. public API
4. appeals
5. comments
6. advanced fraud detection

---

## 已确认实施前提
- Flask 是 V1 的 canonical surface
- Streamlit / simple 仅 demo-only
- persistence foundation 已承接 snapshot / history / ranking / feedback dedupe
- 评分语义统一为 risk-oriented
- peer retrieval 在 V1 采用 rule-first 策略，并保留 sparse/low-confidence disclosure

---

## 模块与职责

| 模块 | 职责 | 依赖 | 当前状态 |
|------|------|------|----------|
| repo-ingestion | GitHub 仓库接入 | GitHub 数据 | ✅ 已接入主流程 |
| structure-analyzer | 结构与证据特征提取 | repo-ingestion | ✅ 已接入主流程 |
| peer-retrieval | 同类项目召回与 baseline | structure-analyzer | ✅ 已接入主流程（rule-first） |
| scoring-engine | 可解释风险评分 | structure-analyzer, peer-retrieval | ✅ 已接入主流程 |
| persistence/query | snapshots/history/ranking/feedback dedupe | analysis outputs | ✅ 已落地 SQLite 存储与查询 |
| Flask surface | 分析、详情、排名、反馈接口/页面 | persistence + core modules | ✅ 已作为 canonical V1 surface |

---

## 执行批次状态

### 批次 1：文档与契约对齐
- [x] 同步 PRD / SOLUTION / PLAN / TODO 的 V1 合同
- [x] 明确 GitHub-first、feedback 边界、analyzed-repo ranking 边界
- [x] 明确 deferred scope 与 TDD posture

### 批次 2：核心模块契约稳定
- [x] 对齐 repo-ingestion / structure-analyzer / peer-retrieval / scoring-engine 契约
- [x] 统一 risk semantics 与 explainability 产物

### 批次 3：测试基线与数据集
- [~] labeled fixtures / peer baseline dataset 已可用于当前 pytest 覆盖
- [~] 仍存在 typing / import hygiene 工程备注，但不阻塞 V1 功能与 pytest 通过

### 批次 4：持久化与主入口收敛
- [x] 明确 Flask 为主入口
- [x] 建立 snapshots / history / ranking / feedback dedupe 持久化基础

### 批次 5：分析编排与快照链路
- [x] 落地 analysis orchestration 与 snapshot 写入闭环
- [x] `/api/analyze` 与 `/api/reanalyze` 共享持久化分析主流程

### 批次 6：详情、排名、反馈与集成验证
- [x] 交付 repo detail / history 页面与 API
- [x] 交付 analyzed-repo rankings + search/filter/sort
- [x] 交付 authenticated lightweight feedback 与基础 anti-abuse
- [x] 打通 landing / report / detail / rankings / feedback 导航
- [x] 扩充回归 / 集成测试覆盖

### 批次 7：文档回写 shipped behavior
- [x] 将项目文档回写为当前已交付 V1 行为

---

## 当前交付口径
- 报告包含总分、分维度风险、证据卡、guardrail notes、peer baseline 摘要
- 排名明确声明“仅限已分析仓库”，并支持搜索 / 筛选 / 排序
- 历史通过 append-only snapshots 暴露最新结果与时间倒序历史
- 反馈明确为“authenticated + lightweight + supplemental”，并具备 dedupe / rate limit
- 任一文档不得把 X / Twitter、匿名投票、公共 API 写成 V1 必需项

---

## 验收状态
- [x] 有效 GitHub URL 可分析并持久化为版本化报告快照
- [x] 结果页 / 详情页暴露总分、分维度、证据卡、guardrail notes、peer baseline 与历史
- [x] 排名 / 搜索 / 筛选仅覆盖已分析仓库
- [x] 登录反馈被存储、去重、限流、补充展示，且不直接改写核心评分或排名
- [x] pytest 回归 / 集成覆盖保持通过

---

## Post-V1 backlog（来自当前真实剩余项）
1. 决定是否把 T3 的 typing / import hygiene 清理提升为正式工程任务
2. 评估 embedding/hybrid peer retrieval 是否值得在 rule-first 之上作为增强能力
3. 如需扩面，再设计 X / Twitter 信号如何以非阻塞、非主判据方式接入
4. 设计更强的反馈治理与 abuse review，而不破坏 supplemental-only 边界
5. 若产品要对外开放，再单独规划 public API、appeals、comments 等 post-V1 能力

---

## 交接说明
- 本计划反映当前 shipped V1，不再作为“待实现”清单使用
- 继续迭代时，新增事项优先写入 `docs/TODO.md` 的 post-V1 backlog
- 若后续范围变化，`docs/PRD.md`、`docs/SOLUTION.md`、`docs/PLAN.md`、`docs/TODO.md` 需同步更新
