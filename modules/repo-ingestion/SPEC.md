# SPEC: repo-ingestion

> 最后更新: 2026-04-01 | 状态: draft（契约对齐版）

***

## 模块职责

接收 GitHub 仓库 URL，抓取仓库元数据并输出**统一字段命名**的原始仓库对象，供 `structure-analyzer`、`peer-retrieval`、`scoring-engine` 复用。

***

## 依赖

- 依赖模块: 无
- 被依赖: structure-analyzer

***

## 性能需求

- 单仓库拉取目标: 中等仓库在 5 秒内完成基础抓取（不含重试回退）

***

## 接口定义

### 函数签名

```python
def fetch_repo_basic_info(repo_url: str, timeout: int = 10) -> dict
```

### 返回结构（跨模块统一）

```python
{
  "repo_url": str,
  "owner": str,
  "name": str,
  "readme_content": str,
  "file_tree": list[dict],
  "default_branch": str,
  "is_fork": bool,
  "created_at": str,
  "updated_at": str,
  "size": int,
  "language": str,
  "languages": dict[str, int],
  "stargazers_count": int,
  "forks_count": int,
  "open_issues_count": int,
  "topics": list[str],
  "license": dict | None,
  "description": str,
  "homepage": str | None,
}
```

### `file_tree` 子项契约（强制规范化）

每个条目至少包含：

```python
{
  "path": str,
  "type": Literal["file", "dir"],
  "size": int,
}
```

> 说明：若上游来源是 GitHub API 的 `blob/tree`，必须在本模块内归一化为 `file/dir` 再输出。

### 异常

- `ValueError`: `repo_url` 非法
- `ConnectionError`: 网络请求失败/超时
- `GitHubAPIError`: GitHub API 非 2xx（如 404/403）

***

## 行为规格

### 正常路径

- 输入有效 GitHub URL 时，输出结构满足上述字段要求
- `file_tree[*].type` 只允许 `file/dir`

### 边界/错误路径

- URL 非 GitHub 仓库格式 → `ValueError("Invalid GitHub URL")`
- 仓库不存在或无权限 → `GitHubAPIError(status_code=404|403)`
- 网络中断或超时 → `ConnectionError`

***

## 跨模块契约声明

- 本模块产出的 `file_tree` 是后续结构分析的唯一输入来源，字段不可漂移
- 任何新增字段必须向后兼容，不得改变既有字段语义

***

## 验收标准

- [ ] 输出字段命名与 dtype 与本 SPEC 一致
- [ ] `file_tree` 条目统一为 `path/type/size` 且 `type=file|dir`
- [ ] 异常类型与消息语义稳定
