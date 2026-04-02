from __future__ import annotations

import json
import sqlite3
import uuid
from dataclasses import dataclass
from datetime import UTC, datetime, timedelta
from pathlib import Path
from typing import Any


ALLOWED_RANK_SORT_FIELDS = {
    "latest_fake_risk_score": "latest_fake_risk_score",
    "snapshot_at": "snapshot_at",
    "stargazers_count": "stargazers_count",
}


@dataclass(frozen=True)
class RankingQuery:
    search: str | None = None
    risk_bands: tuple[str, ...] = ()
    languages: tuple[str, ...] = ()
    sort_by: str = "latest_fake_risk_score"
    descending: bool = True
    limit: int = 20
    offset: int = 0


class PersistenceStore:
    def __init__(self, db_path: str | Path) -> None:
        self.db_path = Path(db_path)
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
        self._initialize()

    def record_analysis(
        self,
        repo_identity: dict[str, Any],
        report_snapshot: dict[str, Any],
        ranking_inputs: dict[str, Any],
    ) -> dict[str, Any]:
        validated_repo = _validate_repo_identity(repo_identity)
        validated_snapshot = _validate_report_snapshot(report_snapshot)
        validated_ranking = _validate_ranking_inputs(ranking_inputs)

        with self._connect() as connection:
            repo_id = self._upsert_repository(connection, validated_repo)
            snapshot_version = self._next_snapshot_version(connection, repo_id)
            snapshot_id = str(uuid.uuid4())
            connection.execute(
                """
                INSERT INTO analysis_snapshots (
                    snapshot_id,
                    repo_id,
                    snapshot_version,
                    snapshot_at,
                    scoring_version,
                    fake_risk_score,
                    risk_level,
                    risk_band,
                    dimension_scores_json,
                    peer_baseline_meta_json,
                    report_snapshot_json,
                    ranking_inputs_json,
                    language,
                    stargazers_count,
                    summary
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    snapshot_id,
                    repo_id,
                    snapshot_version,
                    validated_snapshot["snapshot_at"],
                    validated_snapshot["version"],
                    validated_snapshot["fake_risk_score"],
                    validated_snapshot["risk_level"],
                    validated_snapshot["risk_band"],
                    json.dumps(validated_snapshot["dimension_scores"], sort_keys=True),
                    json.dumps(validated_snapshot["peer_baseline_meta"], sort_keys=True),
                    json.dumps(validated_snapshot, sort_keys=True),
                    json.dumps(validated_ranking, sort_keys=True),
                    validated_ranking["language"],
                    validated_ranking["stargazers_count"],
                    validated_ranking["summary"],
                ),
            )

        return {
            "snapshot_id": snapshot_id,
            "repo_id": repo_id,
            "snapshot_version": snapshot_version,
            "repo_url": validated_repo["repo_url"],
        }

    def get_repo_history(self, repo_url: str) -> list[dict[str, Any]]:
        normalized_repo_url = _normalize_repo_url(repo_url)
        with self._connect() as connection:
            rows = connection.execute(
                """
                SELECT s.snapshot_id, s.snapshot_version, s.snapshot_at, s.scoring_version,
                       s.fake_risk_score, s.risk_level, s.risk_band,
                       s.dimension_scores_json, s.peer_baseline_meta_json,
                       s.report_snapshot_json, s.language, s.stargazers_count, s.summary
                FROM analysis_snapshots s
                JOIN repositories r ON r.repo_id = s.repo_id
                WHERE r.normalized_repo_url = ?
                ORDER BY s.snapshot_at DESC, s.snapshot_version DESC
                """,
                (normalized_repo_url,),
            ).fetchall()
        return [self._history_row_to_dict(row) for row in rows]

    def list_peer_candidates(self, exclude_repo_url: str | None = None) -> list[dict[str, Any]]:
        excluded_repo = _normalize_repo_url(exclude_repo_url) if exclude_repo_url else None
        with self._connect() as connection:
            rows = connection.execute(
                """
                SELECT r.repo_url, s.report_snapshot_json
                FROM analysis_snapshots s
                JOIN repositories r ON r.repo_id = s.repo_id
                JOIN (
                    SELECT repo_id, MAX(snapshot_version) AS snapshot_version
                    FROM analysis_snapshots
                    GROUP BY repo_id
                ) latest ON latest.repo_id = s.repo_id
                        AND latest.snapshot_version = s.snapshot_version
                ORDER BY s.snapshot_at DESC, r.repo_url ASC
                """
            ).fetchall()

        candidates: list[dict[str, Any]] = []
        for row in rows:
            repo_url = str(row["repo_url"])
            if excluded_repo is not None and _normalize_repo_url(repo_url) == excluded_repo:
                continue
            report_snapshot = json.loads(row["report_snapshot_json"])
            project_features = report_snapshot.get("project_features")
            if not isinstance(project_features, dict):
                continue
            candidate = {"repo_url": repo_url, "cohort": "analyzed_repo", **project_features}
            candidates.append(candidate)
        return candidates

    def query_rankings(self, query: RankingQuery) -> dict[str, Any]:
        _validate_ranking_query(query)
        sort_column = ALLOWED_RANK_SORT_FIELDS[query.sort_by]
        sort_direction = "DESC" if query.descending else "ASC"

        where_clauses: list[str] = []
        parameters: list[Any] = []

        if query.search:
            where_clauses.append(
                "(repo_url LIKE ? OR owner LIKE ? OR name LIKE ? OR summary LIKE ?)"
            )
            needle = f"%{query.search.strip()}%"
            parameters.extend([needle, needle, needle, needle])

        if query.languages:
            placeholders = ", ".join("?" for _ in query.languages)
            where_clauses.append(f"language IN ({placeholders})")
            parameters.extend(query.languages)

        if query.risk_bands:
            placeholders = ", ".join("?" for _ in query.risk_bands)
            where_clauses.append(f"risk_band IN ({placeholders})")
            parameters.extend(query.risk_bands)

        where_sql = ""
        if where_clauses:
            where_sql = "WHERE " + " AND ".join(where_clauses)

        latest_cte = """
            WITH latest_snapshots AS (
                SELECT s.repo_id,
                       s.snapshot_id,
                       s.snapshot_version,
                       s.snapshot_at,
                       s.fake_risk_score AS latest_fake_risk_score,
                       s.risk_level,
                       s.risk_band,
                       s.language,
                       s.stargazers_count,
                       s.summary
                FROM analysis_snapshots s
                JOIN (
                    SELECT repo_id, MAX(snapshot_version) AS snapshot_version
                    FROM analysis_snapshots
                    GROUP BY repo_id
                ) latest ON latest.repo_id = s.repo_id
                        AND latest.snapshot_version = s.snapshot_version
            )
        """
        base_query = f"""
            {latest_cte}
            SELECT r.repo_url, r.owner, r.name,
                   ls.snapshot_id, ls.snapshot_version, ls.snapshot_at,
                   ls.latest_fake_risk_score, ls.risk_level, ls.risk_band,
                   ls.language, ls.stargazers_count, ls.summary
            FROM latest_snapshots ls
            JOIN repositories r ON r.repo_id = ls.repo_id
            {where_sql}
        """

        with self._connect() as connection:
            total = connection.execute(
                f"SELECT COUNT(*) AS count FROM ({base_query}) ranked_repos",
                parameters,
            ).fetchone()["count"]
            items = connection.execute(
                f"{base_query} ORDER BY {sort_column} {sort_direction}, repo_url ASC LIMIT ? OFFSET ?",
                [*parameters, query.limit, query.offset],
            ).fetchall()

        return {
            "total": total,
            "items": [dict(row) for row in items],
        }

    def record_feedback(
        self,
        repo_url: str,
        actor_identity: str,
        feedback_kind: str,
        payload: dict[str, Any],
        submitted_at: str,
        dedupe_window_minutes: int = 60,
    ) -> dict[str, Any]:
        if not actor_identity.strip():
            raise ValueError("actor_identity is required")
        if not feedback_kind.strip():
            raise ValueError("feedback_kind is required")
        if dedupe_window_minutes <= 0:
            raise ValueError("dedupe_window_minutes must be positive")
        if not isinstance(payload, dict):
            raise ValueError("payload must be a dictionary")

        submitted_dt = _parse_iso8601(submitted_at)
        dedupe_bucket_start = _bucket_start(submitted_dt, dedupe_window_minutes)

        with self._connect() as connection:
            repo_id = self._lookup_repo_id(connection, repo_url)
            existing = connection.execute(
                """
                SELECT feedback_id, dedupe_bucket_start
                FROM feedback_records
                WHERE repo_id = ?
                  AND actor_identity = ?
                  AND feedback_kind = ?
                  AND dedupe_bucket_start = ?
                """,
                (repo_id, actor_identity, feedback_kind, dedupe_bucket_start),
            ).fetchone()
            if existing is not None:
                return {
                    "feedback_id": existing["feedback_id"],
                    "created": False,
                    "dedupe_bucket_start": existing["dedupe_bucket_start"],
                }

            feedback_id = str(uuid.uuid4())
            connection.execute(
                """
                INSERT INTO feedback_records (
                    feedback_id,
                    repo_id,
                    actor_identity,
                    feedback_kind,
                    payload_json,
                    submitted_at,
                    dedupe_window_minutes,
                    dedupe_bucket_start
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    feedback_id,
                    repo_id,
                    actor_identity,
                    feedback_kind,
                    json.dumps(payload, sort_keys=True),
                    _to_iso8601(submitted_dt),
                    dedupe_window_minutes,
                    dedupe_bucket_start,
                ),
            )

        return {
            "feedback_id": feedback_id,
            "created": True,
            "dedupe_bucket_start": dedupe_bucket_start,
        }

    def list_feedback(self, repo_url: str) -> list[dict[str, Any]]:
        with self._connect() as connection:
            repo_id = self._lookup_repo_id(connection, repo_url)
            rows = connection.execute(
                """
                SELECT feedback_id, actor_identity, feedback_kind, payload_json,
                       submitted_at, dedupe_window_minutes, dedupe_bucket_start
                FROM feedback_records
                WHERE repo_id = ?
                ORDER BY submitted_at DESC, feedback_id DESC
                """,
                (repo_id,),
            ).fetchall()
        return [
            {
                "feedback_id": row["feedback_id"],
                "actor_identity": row["actor_identity"],
                "feedback_kind": row["feedback_kind"],
                "payload": json.loads(row["payload_json"]),
                "submitted_at": row["submitted_at"],
                "dedupe_window_minutes": row["dedupe_window_minutes"],
                "dedupe_bucket_start": row["dedupe_bucket_start"],
            }
            for row in rows
        ]

    def _connect(self) -> sqlite3.Connection:
        connection = sqlite3.connect(self.db_path)
        connection.row_factory = sqlite3.Row
        connection.execute("PRAGMA foreign_keys = ON")
        return connection

    def _initialize(self) -> None:
        with self._connect() as connection:
            connection.executescript(
                """
                CREATE TABLE IF NOT EXISTS repositories (
                    repo_id INTEGER PRIMARY KEY AUTOINCREMENT,
                    repo_url TEXT NOT NULL,
                    normalized_repo_url TEXT NOT NULL UNIQUE,
                    owner TEXT NOT NULL,
                    name TEXT NOT NULL,
                    source TEXT NOT NULL,
                    created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
                    updated_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
                );

                CREATE TABLE IF NOT EXISTS analysis_snapshots (
                    snapshot_id TEXT PRIMARY KEY,
                    repo_id INTEGER NOT NULL,
                    snapshot_version INTEGER NOT NULL,
                    snapshot_at TEXT NOT NULL,
                    scoring_version TEXT NOT NULL,
                    fake_risk_score REAL NOT NULL,
                    risk_level TEXT NOT NULL,
                    risk_band TEXT NOT NULL,
                    dimension_scores_json TEXT NOT NULL,
                    peer_baseline_meta_json TEXT NOT NULL,
                    report_snapshot_json TEXT NOT NULL,
                    ranking_inputs_json TEXT NOT NULL,
                    language TEXT NOT NULL,
                    stargazers_count INTEGER NOT NULL,
                    summary TEXT NOT NULL,
                    created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY(repo_id) REFERENCES repositories(repo_id) ON DELETE CASCADE,
                    UNIQUE(repo_id, snapshot_version)
                );

                CREATE INDEX IF NOT EXISTS idx_analysis_snapshots_repo_version
                    ON analysis_snapshots(repo_id, snapshot_version DESC);
                CREATE INDEX IF NOT EXISTS idx_analysis_snapshots_ranking
                    ON analysis_snapshots(fake_risk_score DESC, snapshot_at DESC);

                CREATE TABLE IF NOT EXISTS feedback_records (
                    feedback_id TEXT PRIMARY KEY,
                    repo_id INTEGER NOT NULL,
                    actor_identity TEXT NOT NULL,
                    feedback_kind TEXT NOT NULL,
                    payload_json TEXT NOT NULL,
                    submitted_at TEXT NOT NULL,
                    dedupe_window_minutes INTEGER NOT NULL,
                    dedupe_bucket_start TEXT NOT NULL,
                    created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY(repo_id) REFERENCES repositories(repo_id) ON DELETE CASCADE,
                    UNIQUE(repo_id, actor_identity, feedback_kind, dedupe_bucket_start)
                );

                CREATE INDEX IF NOT EXISTS idx_feedback_repo_submitted
                    ON feedback_records(repo_id, submitted_at DESC);
                """
            )

    def _upsert_repository(self, connection: sqlite3.Connection, repo_identity: dict[str, str]) -> int:
        normalized_repo_url = _normalize_repo_url(repo_identity["repo_url"])
        connection.execute(
            """
            INSERT INTO repositories (repo_url, normalized_repo_url, owner, name, source)
            VALUES (?, ?, ?, ?, ?)
            ON CONFLICT(normalized_repo_url) DO UPDATE SET
                repo_url = excluded.repo_url,
                owner = excluded.owner,
                name = excluded.name,
                source = excluded.source,
                updated_at = CURRENT_TIMESTAMP
            """,
            (
                repo_identity["repo_url"],
                normalized_repo_url,
                repo_identity["owner"],
                repo_identity["name"],
                repo_identity["source"],
            ),
        )
        row = connection.execute(
            "SELECT repo_id FROM repositories WHERE normalized_repo_url = ?",
            (normalized_repo_url,),
        ).fetchone()
        return int(row["repo_id"])

    def _lookup_repo_id(self, connection: sqlite3.Connection, repo_url: str) -> int:
        row = connection.execute(
            "SELECT repo_id FROM repositories WHERE normalized_repo_url = ?",
            (_normalize_repo_url(repo_url),),
        ).fetchone()
        if row is None:
            raise ValueError("repo_url must reference an analyzed repository")
        return int(row["repo_id"])

    def _next_snapshot_version(self, connection: sqlite3.Connection, repo_id: int) -> int:
        row = connection.execute(
            "SELECT COALESCE(MAX(snapshot_version), 0) AS current_version FROM analysis_snapshots WHERE repo_id = ?",
            (repo_id,),
        ).fetchone()
        return int(row["current_version"]) + 1

    def _history_row_to_dict(self, row: sqlite3.Row) -> dict[str, Any]:
        report_snapshot = json.loads(row["report_snapshot_json"])
        report_snapshot["snapshot_id"] = row["snapshot_id"]
        report_snapshot["snapshot_version"] = row["snapshot_version"]
        report_snapshot["language"] = row["language"]
        report_snapshot["stargazers_count"] = row["stargazers_count"]
        report_snapshot["summary"] = row["summary"]
        return report_snapshot


def _validate_repo_identity(repo_identity: dict[str, Any]) -> dict[str, str]:
    required_fields = ("repo_url", "owner", "name", "source")
    if not isinstance(repo_identity, dict):
        raise ValueError("repo_identity must be a dictionary")
    validated: dict[str, str] = {}
    for field in required_fields:
        value = repo_identity.get(field)
        if not isinstance(value, str) or not value.strip():
            raise ValueError(f"repo_identity missing required field: {field}")
        validated[field] = value.strip()
    return validated


def _validate_report_snapshot(report_snapshot: dict[str, Any]) -> dict[str, Any]:
    required_fields = (
        "snapshot_at",
        "fake_risk_score",
        "risk_level",
        "risk_band",
        "dimension_scores",
        "peer_baseline_meta",
        "version",
    )
    if not isinstance(report_snapshot, dict):
        raise ValueError("report_snapshot must be a dictionary")
    for field in required_fields:
        if field not in report_snapshot:
            raise ValueError(f"report_snapshot missing required field: {field}")

    _parse_iso8601(report_snapshot["snapshot_at"])
    if not isinstance(report_snapshot["fake_risk_score"], (int, float)):
        raise ValueError("fake_risk_score must be numeric")
    if not isinstance(report_snapshot["dimension_scores"], dict):
        raise ValueError("dimension_scores must be a dictionary")
    if not isinstance(report_snapshot["peer_baseline_meta"], dict):
        raise ValueError("peer_baseline_meta must be a dictionary")

    validated = dict(report_snapshot)
    validated["fake_risk_score"] = float(report_snapshot["fake_risk_score"])
    return validated


def _validate_ranking_inputs(ranking_inputs: dict[str, Any]) -> dict[str, Any]:
    required_fields = ("language", "stargazers_count", "summary")
    if not isinstance(ranking_inputs, dict):
        raise ValueError("ranking_inputs must be a dictionary")
    for field in required_fields:
        if field not in ranking_inputs:
            raise ValueError(f"ranking_inputs missing required field: {field}")
    if not isinstance(ranking_inputs["language"], str) or not ranking_inputs["language"].strip():
        raise ValueError("language must be a non-empty string")
    if not isinstance(ranking_inputs["stargazers_count"], int) or ranking_inputs["stargazers_count"] < 0:
        raise ValueError("stargazers_count must be a non-negative integer")
    if not isinstance(ranking_inputs["summary"], str):
        raise ValueError("summary must be a string")
    return {
        "language": ranking_inputs["language"].strip(),
        "stargazers_count": ranking_inputs["stargazers_count"],
        "summary": ranking_inputs["summary"].strip(),
    }


def _validate_ranking_query(query: RankingQuery) -> None:
    if query.limit <= 0:
        raise ValueError("limit must be positive")
    if query.offset < 0:
        raise ValueError("offset cannot be negative")
    if query.sort_by not in ALLOWED_RANK_SORT_FIELDS:
        raise ValueError("Unsupported sort_by field")


def _normalize_repo_url(repo_url: str) -> str:
    if not isinstance(repo_url, str) or not repo_url.strip():
        raise ValueError("repo_url is required")
    return repo_url.strip().rstrip("/").lower()


def _parse_iso8601(value: Any) -> datetime:
    if not isinstance(value, str) or not value.strip():
        raise ValueError("timestamp must be a non-empty ISO8601 string")
    try:
        parsed = datetime.fromisoformat(value.replace("Z", "+00:00"))
    except ValueError as exc:
        raise ValueError("timestamp must be a valid ISO8601 string") from exc
    if parsed.tzinfo is None:
        parsed = parsed.replace(tzinfo=UTC)
    return parsed.astimezone(UTC)


def _bucket_start(submitted_at: datetime, dedupe_window_minutes: int) -> str:
    epoch = datetime(1970, 1, 1, tzinfo=UTC)
    seconds = int((submitted_at - epoch).total_seconds())
    bucket_seconds = dedupe_window_minutes * 60
    bucket_floor = seconds - (seconds % bucket_seconds)
    bucket_dt = epoch + timedelta(seconds=bucket_floor)
    return _to_iso8601(bucket_dt)


def _to_iso8601(value: datetime) -> str:
    return value.astimezone(UTC).replace(microsecond=0).isoformat().replace("+00:00", "Z")


__all__ = ["PersistenceStore", "RankingQuery"]
