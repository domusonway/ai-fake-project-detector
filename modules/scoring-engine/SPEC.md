# SPEC: scoring-engine

> 最后更新: 2026-04-01 | 状态: draft（契约对齐版）

***

## 模块职责

根据项目特征 + 同类基线 + 投票信号，输出可解释的 fake risk 评分报告。

***

## 依赖

- 依赖模块: structure-analyzer, peer-retrieval
- 被依赖: ranking-service

***

## 接口定义

### 函数签名

```python
def compute_fake_risk_score(
    project_features: dict,
    peer_baseline: dict | None = None,
    voting_signals: dict | None = None,
) -> dict
```

### 输入字段（最小集合）

`project_features` 至少包含：

- `code_to_doc_ratio`, `bytes_ratio`, `max_depth`
- `has_entry_point`, `has_tests`, `has_config_files`, `has_ci_cd`, `license_file_present`
- `file_type_distribution`, `language`, `stargazers_count`
- `description`, `size`

`peer_baseline`（可选）遵循 peer-retrieval 聚合契约，推荐包含：

- `sample_size`, `confidence`
- `code_to_doc_ratio_mean`, `bytes_ratio_mean`, `max_depth_mean`
- `has_entry_point_rate`, `has_tests_rate`, `has_config_files_rate`, `has_ci_cd_rate`, `license_file_present_rate`
- `stargazers_count_mean`

### 输出结构

```python
{
  "fake_risk_score": float,   # 0-100，越高越可疑（风险分）
  "risk_level": str,          # low | medium | high | extreme（兼容层）
  "risk_band": str,           # trusted | mild_suspicious | moderate_suspicious | high_suspicious | very_high_suspicious
  "dimension_scores": {
    "delivery": float,        # 0-30，风险贡献，越高越风险
    "substance": float,       # 0-20，风险贡献，越高越风险
    "evidence": float,        # 0-15，风险贡献，越高越风险
    "peer_gap": float,        # 0-15，风险贡献，越高越风险
    "community": float,       # 0-10，风险贡献，越高越风险
    "hype_gap": float,        # 0-10，风险贡献，越高越风险
  },
  "evidence_cards": list[dict],
  "guardrail_notes": list[str],
  "peer_baseline_summary": str,
}
```

> 关键语义统一：`dimension_scores` 与 `fake_risk_score` 同向，均为**风险分**（越高越风险）。

***

## 风险阈值与等级映射（对齐 PRD）

- `0-20` → `risk_band=trusted`（可信度较高）
- `21-40` → `risk_band=mild_suspicious`（轻度可疑）
- `41-60` → `risk_band=moderate_suspicious`（中度可疑）
- `61-80` → `risk_band=high_suspicious`（高度可疑）
- `81-100` → `risk_band=very_high_suspicious`（极高风险）

兼容字段 `risk_level` 建议映射：

- `trusted` → `low`
- `mild_suspicious` → `medium`
- `moderate_suspicious` → `high`
- `high_suspicious | very_high_suspicious` → `extreme`

***

## peer 基线回退策略（必须）

- 当 `peer_baseline is None` 或空：`peer_gap` 采用中性风险（不放大惩罚）
- 当 `sample_size < 3` 或 `confidence=low`：按低置信度基线处理，`peer_gap` 使用保守权重/中性偏置
- 必须在 `peer_baseline_summary` 或 `guardrail_notes` 明确披露基线置信度

***

## 历史快照 schema 约定（供 ranking/history 使用）

评分引擎输出应可被无损落盘为历史快照（由下游持久化）：

```python
{
  "snapshot_at": str,            # ISO8601
  "repo_url": str,
  "fake_risk_score": float,
  "risk_level": str,
  "risk_band": str,
  "dimension_scores": dict[str, float],
  "peer_baseline_meta": {
    "sample_size": int,
    "confidence": str,
  },
  "version": str,                # 评分规则版本
}
```

> 本模块负责语义稳定；持久化由 ranking/history 侧实现。

***

## 异常

- `ValueError`: 缺失必要字段、数值越界
- `TypeError`: 字段类型不匹配

***

## 验收标准

- [ ] `fake_risk_score` 与 `dimension_scores` 语义同向（风险分）
- [ ] 风险阈值映射与 PRD 保持一致且无自相矛盾文本
- [ ] peer 基线缺失/低置信度时存在显式保守回退
- [ ] 历史快照 schema 约定清晰可消费
