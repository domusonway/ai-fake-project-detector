# SPEC: structure-analyzer

> 最后更新: 2026-04-01 | 状态: draft（契约对齐版）

***

## 模块职责

分析 `repo-ingestion` 输出，提取结构与可交付性相关特征，作为 `peer-retrieval` 和 `scoring-engine` 的共同输入。

***

## 依赖

- 依赖模块: repo-ingestion
- 被依赖: scoring-engine, peer-retrieval

***

## 接口定义

### 函数签名

```python
def analyze_repo_structure(repo_data: dict) -> dict
```

### 输入契约（必须来自 repo-ingestion）

- `repo_data.file_tree[*].type` 必须为 `file|dir`
- `repo_data.file_tree[*]` 至少包含 `path/type/size`

### 输出契约（供 peer + scoring 复用）

```python
{
  "file_count": int,
  "dir_count": int,
  "code_files": int,
  "doc_files": int,
  "code_to_doc_ratio": float,
  "code_bytes": int,
  "doc_bytes": int,
  "bytes_ratio": float,
  "max_depth": int,
  "avg_depth": float,
  "file_type_distribution": dict[str, int],
  "has_entry_point": bool,
  "has_tests": bool,
  "has_config_files": bool,
  "has_ci_cd": bool,
  "license_file_present": bool,
  "readme_quality_score": float,
  "structure_score": float,
}
```

> 语义约束：`structure_score` 是结构完整度（goodness，0-1，越高越好），**不可**与 `fake_risk_score` 的风险语义混用。

### 异常

- `ValueError`: 输入类型错误或 `file_tree` 条目缺失 `path/type`
- `KeyError`: 缺失必须字段（如 `file_tree`）

***

## 行为规格

### 正常路径

- 能正确统计文件/目录、深度、代码文档比例、关键结构布尔特征

### 边界/错误路径

- `file_tree` 为空时，计数归零，比例安全返回 0（不抛异常）
- `file_tree` 条目缺 `path/type` 时抛 `ValueError("Invalid file_tree item")`
- 输入不是字典或 `file_tree` 非列表时抛 `ValueError`

***

## 跨模块字段对齐

- 本模块产出的 `code_to_doc_ratio / bytes_ratio / has_tests / has_ci_cd / file_type_distribution` 为
  `peer-retrieval`、`scoring-engine` 的同名输入字段，名称不可漂移。

***

## 验收标准

- [ ] 输出字段命名与 dtype 与本 SPEC 一致
- [ ] 与 repo-ingestion 的 `file_tree` 契约兼容
- [ ] 与 peer/scoring 共享字段同名且同语义
