# SPEC: persistence

> 最后更新: 2026-04-01 | 状态: draft（Wave 1 persistence foundation）

***

## 模块职责

为已分析仓库提供持久化基础：

- 仓库身份与最新分析归档
- append-only 的报告快照历史
- 可直接供 ranking/search 查询的物化字段
- 认证反馈记录与去重窗口语义

***

## 接口定义

### 数据契约

```python
@dataclass(frozen=True)
class RankingQuery:
    search: str | None = None
    risk_bands: tuple[str, ...] = ()
    languages: tuple[str, ...] = ()
    sort_by: str = "latest_fake_risk_score"
    descending: bool = True
    limit: int = 20
    offset: int = 0
```

```python
class PersistenceStore:
    def __init__(self, db_path: str | Path) -> None: ...

    def record_analysis(
        self,
        repo_identity: dict,
        report_snapshot: dict,
        ranking_inputs: dict,
    ) -> dict: ...

    def get_repo_history(self, repo_url: str) -> list[dict]: ...

    def query_rankings(self, query: RankingQuery) -> dict: ...

    def record_feedback(
        self,
        repo_url: str,
        actor_identity: str,
        feedback_kind: str,
        payload: dict,
        submitted_at: str,
        dedupe_window_minutes: int = 60,
    ) -> dict: ...

    def list_feedback(self, repo_url: str) -> list[dict]: ...
```

### repo_identity 最小字段

- `repo_url: str`
- `owner: str`
- `name: str`
- `source: str`（V1 默认 `github`）

### report_snapshot 最小字段

- `snapshot_at: str`（ISO8601）
- `fake_risk_score: float`
- `risk_level: str`
- `risk_band: str`
- `dimension_scores: dict[str, float]`
- `peer_baseline_meta: dict`
- `version: str`

### ranking_inputs 最小字段

- `language: str`
- `stargazers_count: int`
- `summary: str`

> 查询 ranking/search 时不得为每个请求重新跑评分引擎；必须直接查询已持久化字段。

### feedback payload 约束

- `repo_url + actor_identity + feedback_kind + dedupe_window` 构成去重语义
- 反馈记录只补充可信度信号，不得覆盖核心评分事实或历史快照

***

## 行为规格

### 正常路径

- 同一 repo 多次分析时，`record_analysis` 必须生成新的快照版本，而不是覆盖旧快照
- `get_repo_history` 返回该 repo 的完整历史，按 `snapshot_at` 倒序
- `query_rankings` 仅基于每个 repo 的最新快照 + 物化 ranking 字段返回结果
- `record_feedback` 在去重窗口内对重复反馈返回同一有效记录

### 边界 / 错误路径

- 未分析过的 repo 查询历史 → 返回 `[]`
- `RankingQuery.limit <= 0` 或 `offset < 0` → `ValueError`
- 缺失最小 repo/report/ranking 字段 → `ValueError`
- `submitted_at` 非 ISO8601 或 `dedupe_window_minutes <= 0` → `ValueError`

***

## 验收标准

- [ ] 重复分析同一仓库时产生 append-only history
- [ ] ranking/search 读取已分析仓库与最新物化字段，无需重新计算
- [ ] feedback schema 含认证身份、repo 身份、时间窗去重字段
