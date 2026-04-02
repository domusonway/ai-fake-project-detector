# SPEC: peer-retrieval

> 最后更新: 2026-04-01 | 状态: draft（契约对齐版）

***

## 模块职责

基于目标项目特征召回同类项目，输出可解释的相似度结果；V1 采用**规则优先（rule-first）**检索。

***

## 依赖

- 依赖模块: structure-analyzer
- 被依赖: scoring-engine

***

## 接口定义

### 函数签名

```python
def retrieve_similar_projects(
    target_features: dict,
    candidate_projects: list[dict],
    top_k: int = 10,
    strategy: str = "rule",
) -> list[dict]
```

### 输入字段（最小集合）

`target_features` 与每个 `candidate_projects[i]` 至少包含：

- `code_to_doc_ratio: float`
- `bytes_ratio: float`
- `max_depth: int`
- `has_entry_point: bool`
- `has_tests: bool`
- `has_config_files: bool`
- `has_ci_cd: bool`
- `license_file_present: bool`
- `file_type_distribution: dict[str, int]`
- `language: str`
- `stargazers_count: int`

### 输出字段

返回按 `similarity_score` 降序排列的列表，每项包含：

- 候选项目原始特征字段
- `similarity_score: float`（0-1）
- `match_explanation: dict[str, float]`（当前采用规则策略时必须提供）

### 策略与回退（V1 强约束）

- 默认策略：`rule`
- 若请求 `embedding`/`hybrid` 但缺少稳定嵌入输入（如 `embedding_vector`），必须回退到 `rule`
- 回退后仍需输出可解释结果（`match_explanation`）
- V1 不允许 embedding-only 成为必需路径

### 异常

- `ValueError`: 输入类型错误或 strategy 非法
- `KeyError`: 缺失必要特征字段

***

## 行为规格

### 正常路径

- `rule` 下输出稳定排序与解释字段

### 边界/错误路径

- 空候选列表 → 返回 `[]`
- `top_k <= 0` → 返回 `[]`
- `top_k > len(candidate_projects)` → 返回全部候选（按相似度排序）
- `strategy` 非 `rule|embedding|hybrid` → `ValueError("Unsupported strategy")`

### 稀疏 peer / 低置信度约定

- 若可用候选数 `< 3`，视为 `sparse_peer`
- 若头部相似度不足（如 top1 < 0.35），视为 `low_confidence_peer`
- 上述情况不得中断流程，需让下游可感知并采取保守评分（见 scoring-engine）

***

## 对 scoring-engine 的基线约定

`peer-retrieval` 的结果可被下游聚合为 `peer_baseline`：

```python
{
  "sample_size": int,
  "confidence": Literal["low", "medium", "high"],
  "code_to_doc_ratio_mean": float,
  "bytes_ratio_mean": float,
  "max_depth_mean": float,
  "has_entry_point_rate": float,
  "has_tests_rate": float,
  "has_config_files_rate": float,
  "has_ci_cd_rate": float,
  "license_file_present_rate": float,
  "stargazers_count_mean": float,
}
```

> 当 `sample_size` 小或 `confidence=low`，scoring-engine 必须走保守回退（中性 peer_gap 风险，不放大惩罚）。

***

## 验收标准

- [ ] 默认策略为 rule-first 且输出可解释
- [ ] embedding/hybrid 在缺嵌入输入时可回退到 rule
- [ ] 稀疏 peer 与低置信度语义有明确下游约束
