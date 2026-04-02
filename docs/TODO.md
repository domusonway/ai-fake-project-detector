# ai-fake-project-detector · 任务跟踪

---

## 当前已交付合同
V1 当前真实交付口径：
- GitHub-first
- Flask canonical surface
- explainable scoring
- rule-first peer comparison
- persisted analysis snapshots + history
- analyzed-repo ranking
- search / filter / sort
- authenticated lightweight feedback
- integrated navigation across report / detail / rankings / feedback
- stronger regression / integration coverage

严格边界：
- 排名只覆盖已分析仓库
- 反馈仅作补充，不直接主导风险分或排名
- X / Twitter、匿名投票、public API、appeals、comments、advanced fraud detection 全部延期

---

## 已完成
- [x] 同步 PRD / SOLUTION / PLAN / TODO 的 V1 合同
- [x] 明确术语从 accusatory wording 收敛到 verification / risk 语言
- [x] 明确 Flask 为 canonical V1 surface
- [x] 明确 Streamlit / simple 为 demo-only
- [x] 建立持久化分析编排：分析结果稳定写入 snapshot/history
- [x] 交付 repo detail / history 页面与 API
- [x] 交付 analyzed-repo ranking 的搜索 / 筛选 / 排序闭环
- [x] 接入 authenticated lightweight feedback，并保持 supplemental 边界
- [x] 打通分析、详情、排名、反馈之间的主导航流
- [x] 增补 ranking / history / feedback / navigation 的回归与集成测试
- [x] 将项目文档同步到 shipped V1 behavior

---

## 下一步 backlog（Post-V1）
- [ ] 评估是否将 T3 的 typing / import hygiene 清理升级为正式工程任务；当前它只是非阻塞的工程卫生备注
- [ ] 评估 embedding/hybrid peer retrieval 增强是否值得在现有 rule-first 策略之上引入
- [ ] 设计更强的反馈治理与 abuse review，但继续保持 supplemental-only 边界
- [ ] 规划 X / Twitter 信号如何以可解释、非阻塞方式接入未来版本
- [ ] 如需对外扩展，再单独规划 public API、appeals、comments 等 post-V1 能力

---

## 暂缓 / 非 V1
- [ ] X / Twitter ingestion
- [ ] anonymous voting / anonymous feedback
- [ ] public API
- [ ] appeals
- [ ] comments
- [ ] advanced fraud detection

---

## 执行要求
- 所有新增实现任务继续按 TDD 推进
- 不允许把反馈写成核心分数直接输入或排名权威
- 不允许把排名写成“全 GitHub 榜单”
- 不允许把 demo surface 误写成主产品面
